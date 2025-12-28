# Epic Technical Specification: Entity Reprocessing

**Epic ID:** P13-3
**Phase:** 13 - Platform Maturity & External Integration
**Priority:** P3
**Generated:** 2025-12-28
**PRD Reference:** docs/PRD-phase13.md
**Epic Reference:** docs/epics-phase13.md

---

## Executive Summary

This epic implements bulk entity reprocessing functionality to improve historical data quality by retroactively matching events to recognized entities. As entity recognition has evolved through Phase 4-11, many historical events lack entity matches. This feature allows administrators to reprocess events to apply current entity matching algorithms.

**Functional Requirements Coverage:** FR19-FR26 (8 requirements)
**Backlog Reference:** FF-034

---

## Architecture Overview

### High-Level Design

```
                    Frontend                                Backend
                       │                                      │
           ┌───────────▼───────────┐                         │
           │   Reprocessing UI      │                         │
           │  - Filter controls     │                         │
           │  - Start button        │                         │
           │  - Progress display    │                         │
           │  - Cancel button       │                         │
           └───────────┬───────────┘                         │
                       │ POST /api/v1/events/reprocess-entities
                       │─────────────────────────────────────►│
                       │                          ┌───────────▼───────────┐
                       │                          │ ReprocessingService    │
                       │                          │ - Background task      │
                       │                          │ - Batch processing     │
                       │                          │ - Progress tracking    │
                       │                          └───────────┬───────────┘
                       │                                      │
                       │ WS: reprocessing_progress            │
                       │◄─────────────────────────────────────│
                       │ {processed: 150, matched: 45, ...}   │
                       │                                      │
                       │ WS: reprocessing_complete            │
                       │◄─────────────────────────────────────│
```

### Component Architecture

```
backend/app/
├── services/
│   └── reprocessing_service.py    # NEW: Core reprocessing logic
├── api/v1/
│   └── events.py                  # MODIFY: Add reprocess endpoints
├── schemas/
│   └── reprocessing.py            # NEW: Request/Response schemas
└── tasks/
    └── reprocessing_task.py       # NEW: Background task runner

frontend/
├── components/settings/
│   └── ReprocessingSection.tsx    # NEW: Reprocessing UI
└── hooks/
    └── useReprocessing.ts         # NEW: Reprocessing state/WebSocket
```

---

## Story Specifications

### Story P13-3.1: Create Reprocessing Background Task

**Acceptance Criteria:**
- AC-3.1.1: Given a reprocessing request, when the task starts, then events are processed in batches of 100
- AC-3.1.2: Given an event is processed, when entity matching runs, then embedding is generated if missing and entity matching is attempted
- AC-3.1.3: Given the task is running, when progress updates occur, then state is persisted to database for resume capability

**Technical Specification:**

```python
# backend/app/services/reprocessing_service.py
import asyncio
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session

from app.services.entity_service import get_entity_service, EntityService
from app.services.embedding_service import get_embedding_service
from app.services.websocket_manager import broadcast_message

logger = logging.getLogger(__name__)


@dataclass
class ReprocessingProgress:
    """Current state of reprocessing task."""
    task_id: str
    status: str  # pending, running, completed, cancelled, error
    total_events: int
    processed: int
    entities_matched: int
    embeddings_generated: int
    errors: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    last_event_id: Optional[str] = None  # For resume capability


class ReprocessingService:
    """
    Service for bulk entity reprocessing of historical events.

    Processes events in batches, generates missing embeddings,
    and matches entities using the current recognition algorithms.
    """

    BATCH_SIZE = 100
    PROGRESS_BROADCAST_INTERVAL = 1  # seconds
    PROGRESS_BROADCAST_BATCH = 100  # events

    def __init__(self):
        self._current_task: Optional[ReprocessingProgress] = None
        self._cancel_requested = False
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        """Check if reprocessing is currently running."""
        return self._current_task is not None and self._current_task.status == "running"

    def get_status(self) -> Optional[ReprocessingProgress]:
        """Get current reprocessing status."""
        return self._current_task

    async def start_reprocessing(
        self,
        db: Session,
        filters: "ReprocessingFilters",
    ) -> ReprocessingProgress:
        """
        Start a new reprocessing task.

        Args:
            db: Database session
            filters: Filtering options for which events to process

        Returns:
            ReprocessingProgress with initial state

        Raises:
            ValueError: If reprocessing is already running
        """
        async with self._lock:
            if self.is_running:
                raise ValueError("Reprocessing already in progress")

            # Count matching events
            total = await self._count_events(db, filters)

            task_id = str(uuid.uuid4())
            self._current_task = ReprocessingProgress(
                task_id=task_id,
                status="pending",
                total_events=total,
                processed=0,
                entities_matched=0,
                embeddings_generated=0,
                errors=0,
            )
            self._cancel_requested = False

            # Persist initial state
            await self._save_progress(db)

            # Start background task
            asyncio.create_task(self._run_reprocessing(db, filters))

            return self._current_task

    async def cancel_reprocessing(self) -> bool:
        """Request cancellation of running task."""
        if not self.is_running:
            return False

        self._cancel_requested = True
        return True

    async def _run_reprocessing(
        self,
        db: Session,
        filters: "ReprocessingFilters",
    ):
        """
        Main reprocessing loop.

        Processes events in batches, updating progress after each batch.
        """
        from app.models.event import Event
        from app.models.event_embedding import EventEmbedding

        self._current_task.status = "running"
        self._current_task.started_at = datetime.now(timezone.utc)

        entity_service = get_entity_service()
        embedding_service = get_embedding_service()

        last_broadcast = datetime.now(timezone.utc)

        try:
            # Build query based on filters
            query = self._build_event_query(db, filters)

            # Process in batches
            offset = 0
            while True:
                if self._cancel_requested:
                    self._current_task.status = "cancelled"
                    break

                events = query.offset(offset).limit(self.BATCH_SIZE).all()
                if not events:
                    self._current_task.status = "completed"
                    break

                for event in events:
                    if self._cancel_requested:
                        break

                    try:
                        await self._process_event(
                            db, event, entity_service, embedding_service
                        )
                        self._current_task.processed += 1
                        self._current_task.last_event_id = event.id
                    except Exception as e:
                        logger.error(f"Error processing event {event.id}: {e}")
                        self._current_task.errors += 1

                    # Broadcast progress periodically
                    now = datetime.now(timezone.utc)
                    if (now - last_broadcast).total_seconds() >= self.PROGRESS_BROADCAST_INTERVAL:
                        await self._broadcast_progress()
                        last_broadcast = now

                offset += self.BATCH_SIZE
                await self._save_progress(db)

        except Exception as e:
            logger.error(f"Reprocessing task failed: {e}")
            self._current_task.status = "error"
            self._current_task.error_message = str(e)

        finally:
            self._current_task.completed_at = datetime.now(timezone.utc)
            await self._save_progress(db)
            await self._broadcast_progress(final=True)

    async def _process_event(
        self,
        db: Session,
        event: "Event",
        entity_service: EntityService,
        embedding_service,
    ):
        """
        Process a single event for entity matching.

        1. Check if event has embedding
        2. Generate embedding if missing
        3. Run entity matching
        4. Update event with matched entity IDs
        """
        from app.models.event_embedding import EventEmbedding
        from app.models.event import Event

        # Check for existing embedding
        embedding = db.query(EventEmbedding).filter(
            EventEmbedding.event_id == event.id
        ).first()

        # Generate embedding if missing
        if not embedding and event.thumbnail_path:
            try:
                embedding_vector = await embedding_service.generate_embedding(
                    event.thumbnail_path
                )
                if embedding_vector:
                    embedding = EventEmbedding(
                        event_id=event.id,
                        embedding=embedding_vector,
                    )
                    db.add(embedding)
                    db.commit()
                    self._current_task.embeddings_generated += 1
            except Exception as e:
                logger.warning(f"Failed to generate embedding for event {event.id}: {e}")
                return

        # Skip if still no embedding
        if not embedding:
            return

        # Run entity matching
        try:
            result = await entity_service.match_or_create_entity(
                db=db,
                event_id=event.id,
                embedding=embedding.embedding,
                entity_type=self._infer_entity_type(event),
            )

            if not result.is_new:
                self._current_task.entities_matched += 1

                # Update event with matched entity ID
                matched_ids = event.matched_entity_ids or []
                if result.entity_id not in matched_ids:
                    matched_ids.append(result.entity_id)
                    event.matched_entity_ids = matched_ids
                    db.commit()

        except Exception as e:
            logger.warning(f"Entity matching failed for event {event.id}: {e}")

    def _infer_entity_type(self, event: "Event") -> str:
        """Infer entity type from event description."""
        if not event.description:
            return "unknown"

        desc_lower = event.description.lower()
        if any(word in desc_lower for word in ["person", "man", "woman", "child", "someone"]):
            return "person"
        if any(word in desc_lower for word in ["car", "truck", "vehicle", "suv", "van"]):
            return "vehicle"
        return "unknown"

    async def _count_events(self, db: Session, filters: "ReprocessingFilters") -> int:
        """Count events matching filters."""
        return self._build_event_query(db, filters).count()

    def _build_event_query(self, db: Session, filters: "ReprocessingFilters"):
        """Build SQLAlchemy query based on filters."""
        from app.models.event import Event

        query = db.query(Event)

        if filters.start_date:
            query = query.filter(Event.timestamp >= filters.start_date)
        if filters.end_date:
            query = query.filter(Event.timestamp <= filters.end_date)
        if filters.camera_id:
            query = query.filter(Event.camera_id == filters.camera_id)
        if filters.unmatched_only:
            query = query.filter(
                (Event.matched_entity_ids == None) |
                (Event.matched_entity_ids == [])
            )

        return query.order_by(Event.timestamp.asc())

    async def _save_progress(self, db: Session):
        """Persist progress to database for resume capability."""
        from app.models.system_setting import SystemSetting
        import json

        setting = db.query(SystemSetting).filter(
            SystemSetting.key == "reprocessing_progress"
        ).first()

        progress_data = {
            "task_id": self._current_task.task_id,
            "status": self._current_task.status,
            "total_events": self._current_task.total_events,
            "processed": self._current_task.processed,
            "entities_matched": self._current_task.entities_matched,
            "embeddings_generated": self._current_task.embeddings_generated,
            "errors": self._current_task.errors,
            "last_event_id": self._current_task.last_event_id,
            "started_at": self._current_task.started_at.isoformat() if self._current_task.started_at else None,
        }

        if setting:
            setting.value = json.dumps(progress_data)
        else:
            setting = SystemSetting(
                key="reprocessing_progress",
                value=json.dumps(progress_data),
            )
            db.add(setting)

        db.commit()

    async def _broadcast_progress(self, final: bool = False):
        """Broadcast progress update via WebSocket."""
        message_type = "reprocessing_complete" if final else "reprocessing_progress"

        await broadcast_message({
            "type": message_type,
            "data": {
                "task_id": self._current_task.task_id,
                "status": self._current_task.status,
                "total": self._current_task.total_events,
                "processed": self._current_task.processed,
                "entities_matched": self._current_task.entities_matched,
                "embeddings_generated": self._current_task.embeddings_generated,
                "errors": self._current_task.errors,
                "progress_percent": round(
                    self._current_task.processed / self._current_task.total_events * 100, 1
                ) if self._current_task.total_events > 0 else 0,
            }
        })


# Singleton
_reprocessing_service: Optional[ReprocessingService] = None

def get_reprocessing_service() -> ReprocessingService:
    global _reprocessing_service
    if _reprocessing_service is None:
        _reprocessing_service = ReprocessingService()
    return _reprocessing_service
```

**Files to Create:**
- `backend/app/services/reprocessing_service.py` (NEW)

---

### Story P13-3.2: Implement Reprocessing API Endpoints

**Acceptance Criteria:**
- AC-3.2.1: Given valid filters, when POST to reprocess endpoint, then task starts and returns estimated count
- AC-3.2.2: Given a running task, when GET status is called, then current progress is returned
- AC-3.2.3: Given a running task, when DELETE is called, then task cancellation is requested

**Technical Specification:**

```python
# backend/app/api/v1/events.py - Add to existing file

@router.post("/reprocess-entities", response_model=ReprocessingStartResponse)
async def start_entity_reprocessing(
    request: ReprocessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start bulk entity reprocessing.

    Processes events in background, matching entities and generating
    missing embeddings. Progress is broadcast via WebSocket.
    """
    service = get_reprocessing_service()

    filters = ReprocessingFilters(
        start_date=request.start_date,
        end_date=request.end_date,
        camera_id=request.camera_id,
        unmatched_only=request.unmatched_only,
    )

    try:
        progress = await service.start_reprocessing(db, filters)
        return ReprocessingStartResponse(
            task_id=progress.task_id,
            status=progress.status,
            total_events=progress.total_events,
            message=f"Started reprocessing {progress.total_events} events",
        )
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.get("/reprocess-entities", response_model=ReprocessingStatusResponse)
async def get_reprocessing_status():
    """Get current reprocessing task status."""
    service = get_reprocessing_service()
    progress = service.get_status()

    if not progress:
        return ReprocessingStatusResponse(
            status="idle",
            total_events=0,
            processed=0,
            entities_matched=0,
            embeddings_generated=0,
            errors=0,
        )

    return ReprocessingStatusResponse(
        task_id=progress.task_id,
        status=progress.status,
        total_events=progress.total_events,
        processed=progress.processed,
        entities_matched=progress.entities_matched,
        embeddings_generated=progress.embeddings_generated,
        errors=progress.errors,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        error_message=progress.error_message,
    )


@router.delete("/reprocess-entities", response_model=MessageResponse)
async def cancel_reprocessing():
    """Cancel running reprocessing task."""
    service = get_reprocessing_service()

    if await service.cancel_reprocessing():
        return MessageResponse(message="Cancellation requested")
    else:
        raise HTTPException(404, "No reprocessing task running")
```

**Schemas:**
```python
# backend/app/schemas/reprocessing.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReprocessingRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    camera_id: Optional[str] = None
    unmatched_only: bool = True


class ReprocessingFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    camera_id: Optional[str] = None
    unmatched_only: bool = True


class ReprocessingStartResponse(BaseModel):
    task_id: str
    status: str
    total_events: int
    message: str


class ReprocessingStatusResponse(BaseModel):
    task_id: Optional[str] = None
    status: str
    total_events: int
    processed: int
    entities_matched: int
    embeddings_generated: int
    errors: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
```

**Files to Create/Modify:**
- `backend/app/api/v1/events.py` (MODIFY)
- `backend/app/schemas/reprocessing.py` (NEW)

---

### Story P13-3.3: Add WebSocket Progress Updates

**Acceptance Criteria:**
- AC-3.3.1: Given reprocessing is running, when progress updates, then WebSocket broadcasts `reprocessing_progress` message
- AC-3.3.2: Given reprocessing completes, when task finishes, then WebSocket broadcasts `reprocessing_complete` message
- AC-3.3.3: Given frontend is subscribed, when messages arrive, then progress bar updates in real-time

**Technical Specification:**

WebSocket broadcasts are already implemented in `_broadcast_progress()` method above. The frontend needs to subscribe and handle these messages.

```typescript
// frontend/hooks/useReprocessing.ts
import { useEffect, useState, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';

interface ReprocessingProgress {
  task_id: string;
  status: 'idle' | 'pending' | 'running' | 'completed' | 'cancelled' | 'error';
  total: number;
  processed: number;
  entities_matched: number;
  embeddings_generated: number;
  errors: number;
  progress_percent: number;
}

export function useReprocessing() {
  const [progress, setProgress] = useState<ReprocessingProgress | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    // Handle progress updates
    const handleProgress = (data: ReprocessingProgress) => {
      setProgress(data);
    };

    subscribe('reprocessing_progress', handleProgress);
    subscribe('reprocessing_complete', handleProgress);

    // Fetch initial status
    fetchStatus();

    return () => {
      unsubscribe('reprocessing_progress', handleProgress);
      unsubscribe('reprocessing_complete', handleProgress);
    };
  }, []);

  const fetchStatus = async () => {
    const res = await fetch('/api/v1/events/reprocess-entities');
    const data = await res.json();
    if (data.status !== 'idle') {
      setProgress({
        task_id: data.task_id,
        status: data.status,
        total: data.total_events,
        processed: data.processed,
        entities_matched: data.entities_matched,
        embeddings_generated: data.embeddings_generated,
        errors: data.errors,
        progress_percent: data.total_events > 0
          ? (data.processed / data.total_events) * 100
          : 0,
      });
    }
  };

  const startReprocessing = async (options: {
    startDate?: string;
    endDate?: string;
    cameraId?: string;
    unmatchedOnly?: boolean;
  }) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/events/reprocess-entities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: options.startDate,
          end_date: options.endDate,
          camera_id: options.cameraId,
          unmatched_only: options.unmatchedOnly ?? true,
        }),
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const data = await res.json();
      setProgress({
        task_id: data.task_id,
        status: data.status,
        total: data.total_events,
        processed: 0,
        entities_matched: 0,
        embeddings_generated: 0,
        errors: 0,
        progress_percent: 0,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const cancelReprocessing = async () => {
    await fetch('/api/v1/events/reprocess-entities', { method: 'DELETE' });
  };

  return {
    progress,
    isLoading,
    isRunning: progress?.status === 'running',
    startReprocessing,
    cancelReprocessing,
  };
}
```

**Files to Create:**
- `frontend/hooks/useReprocessing.ts` (NEW)

---

### Story P13-3.4: Create Reprocessing UI

**Acceptance Criteria:**
- AC-3.4.1: Given the Settings page, when viewing Reprocessing section, then filter controls and start button are displayed
- AC-3.4.2: Given reprocessing is running, when viewing the UI, then progress bar with stats is shown
- AC-3.4.3: Given reprocessing is running, when clicking cancel, then confirmation appears and task stops

**Technical Specification:**

```typescript
// frontend/components/settings/ReprocessingSection.tsx
import { useState } from 'react';
import { useReprocessing } from '@/hooks/useReprocessing';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Calendar } from '@/components/ui/calendar';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { useCameras } from '@/hooks/useCameras';

export function ReprocessingSection() {
  const { progress, isLoading, isRunning, startReprocessing, cancelReprocessing } = useReprocessing();
  const { cameras } = useCameras();

  const [startDate, setStartDate] = useState<Date | undefined>();
  const [endDate, setEndDate] = useState<Date | undefined>();
  const [cameraId, setCameraId] = useState<string>('');
  const [unmatchedOnly, setUnmatchedOnly] = useState(true);

  const handleStart = async () => {
    await startReprocessing({
      startDate: startDate?.toISOString(),
      endDate: endDate?.toISOString(),
      cameraId: cameraId || undefined,
      unmatchedOnly,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Entity Reprocessing</CardTitle>
        <CardDescription>
          Retroactively match entities to historical events
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress display when running */}
        {progress && progress.status !== 'idle' && (
          <div className="space-y-4 p-4 bg-muted rounded-lg">
            <div className="flex justify-between items-center">
              <span className="font-medium">
                {progress.status === 'running' ? 'Processing...' :
                 progress.status === 'completed' ? 'Completed' :
                 progress.status === 'cancelled' ? 'Cancelled' : 'Error'}
              </span>
              <span className="text-sm text-muted-foreground">
                {progress.processed} / {progress.total} events
              </span>
            </div>

            <Progress value={progress.progress_percent} />

            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Entities Matched</span>
                <p className="font-medium">{progress.entities_matched}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Embeddings Generated</span>
                <p className="font-medium">{progress.embeddings_generated}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Errors</span>
                <p className="font-medium">{progress.errors}</p>
              </div>
            </div>

            {isRunning && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm">Cancel</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Cancel Reprocessing?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Progress will be lost. You can start a new reprocessing task later.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Continue Processing</AlertDialogCancel>
                    <AlertDialogAction onClick={cancelReprocessing}>
                      Cancel Task
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        )}

        {/* Filters - only show when not running */}
        {(!progress || progress.status === 'idle' || progress.status === 'completed') && (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Start Date (Optional)</Label>
                <Calendar
                  mode="single"
                  selected={startDate}
                  onSelect={setStartDate}
                  className="rounded-md border"
                />
              </div>
              <div>
                <Label>End Date (Optional)</Label>
                <Calendar
                  mode="single"
                  selected={endDate}
                  onSelect={setEndDate}
                  className="rounded-md border"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Camera (Optional)</Label>
                <Select value={cameraId} onValueChange={setCameraId}>
                  <SelectTrigger>
                    <SelectValue placeholder="All cameras" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All cameras</SelectItem>
                    {cameras.map((camera) => (
                      <SelectItem key={camera.id} value={camera.id}>
                        {camera.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  checked={unmatchedOnly}
                  onCheckedChange={setUnmatchedOnly}
                />
                <Label>Only events without entities</Label>
              </div>
            </div>

            <Button
              onClick={handleStart}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? 'Starting...' : 'Start Reprocessing'}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
```

**Files to Create:**
- `frontend/components/settings/ReprocessingSection.tsx` (NEW)
- `frontend/app/settings/reprocessing/page.tsx` (NEW - optional route)

---

## API Contracts

### Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/events/reprocess-entities` | Start reprocessing | Admin JWT |
| GET | `/api/v1/events/reprocess-entities` | Get status | Admin JWT |
| DELETE | `/api/v1/events/reprocess-entities` | Cancel task | Admin JWT |

### WebSocket Messages

**reprocessing_progress:**
```json
{
  "type": "reprocessing_progress",
  "data": {
    "task_id": "uuid",
    "status": "running",
    "total": 5000,
    "processed": 1500,
    "entities_matched": 342,
    "embeddings_generated": 156,
    "errors": 3,
    "progress_percent": 30.0
  }
}
```

**reprocessing_complete:**
```json
{
  "type": "reprocessing_complete",
  "data": {
    "task_id": "uuid",
    "status": "completed",
    "total": 5000,
    "processed": 5000,
    "entities_matched": 1124,
    "embeddings_generated": 523,
    "errors": 12,
    "progress_percent": 100.0
  }
}
```

---

## NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR10 | 100 events/second | Batch processing with async |
| NFR11 | Progress updates every 1s/100 events | Configurable in service |
| NFR14 | Resumable after restart | Progress saved to DB |

---

## Testing Strategy

### Unit Tests
- Filter query building
- Progress calculation
- Cancellation handling

### Integration Tests
- Full reprocessing cycle with test events
- WebSocket message delivery
- Resume after simulated crash

### Performance Tests
- Process 10,000+ events without timeout
- Memory usage under load
