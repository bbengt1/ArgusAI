# MCP Server Research for ArgusAI

**Author:** Claude Opus 4.5
**Date:** 2025-12-25
**Story:** P10-6.1 - Research Local MCP Server
**Status:** Complete

---

## Executive Summary

This document presents research on implementing a local Model Context Protocol (MCP) server for ArgusAI to enhance AI event descriptions with rich local context. MCP is an open standard introduced by Anthropic in November 2024 that has since been adopted by OpenAI, Google DeepMind, and others.

**Key Recommendation:** Implement an **embedded MCP server** within the FastAPI backend using the official Python SDK (`mcp` package). This approach provides the lowest latency (<50ms overhead), minimal deployment complexity, and natural integration with existing async services.

---

## 1. Model Context Protocol Overview

### 1.1 What is MCP?

The Model Context Protocol (MCP) is an open standard for connecting AI systems to external data sources and tools. It provides a standardized way for LLM applications to:

- **Access contextual data** through Resources (read-only data similar to GET endpoints)
- **Execute actions** through Tools (functions with side effects, similar to POST endpoints)
- **Use templates** through Prompts (reusable interaction patterns)

### 1.2 Protocol Architecture

```
┌──────────────────┐         ┌──────────────────┐
│   AI Provider    │◄───────►│    MCP Client    │
│ (Claude, GPT-4)  │         │                  │
└──────────────────┘         └────────┬─────────┘
                                      │
                              MCP Protocol
                              (JSON-RPC 2.0)
                                      │
                             ┌────────▼─────────┐
                             │   MCP Server     │
                             │  (ArgusAI)       │
                             └────────┬─────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
    ┌───────▼───────┐         ┌───────▼───────┐         ┌───────▼───────┐
    │   Resources   │         │     Tools     │         │    Prompts    │
    │ (Read Context)│         │(Execute Code) │         │  (Templates)  │
    └───────────────┘         └───────────────┘         └───────────────┘
```

### 1.3 Core Primitives

| Primitive | Purpose | ArgusAI Use Case |
|-----------|---------|------------------|
| **Resources** | Expose read-only data to LLMs | Entity database, feedback history, camera context |
| **Tools** | Allow LLMs to call functions | Look up similar events, get entity details |
| **Prompts** | Reusable templates | Context-enhanced description prompts |

### 1.4 Transport Options

| Transport | Description | Use Case |
|-----------|-------------|----------|
| **STDIO** | Standard input/output | CLI tools, subprocess communication |
| **SSE** | Server-Sent Events | Web browser clients |
| **HTTP Streamable** | Full-duplex HTTP | Web services with CORS |
| **Custom ASGI** | Mount to existing frameworks | FastAPI integration |

---

## 2. Hosting Options Evaluation

### 2.1 Option A: Sidecar Process

```
┌──────────────────────────────────────────────────────┐
│                   ArgusAI Host                       │
│  ┌─────────────────┐    IPC     ┌─────────────────┐  │
│  │  FastAPI Backend│◄──────────►│   MCP Server    │  │
│  │   (Port 8000)   │ (STDIO/    │   (Separate     │  │
│  │                 │   Unix)    │    Process)     │  │
│  └─────────────────┘            └─────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Pros:**
- Process isolation (crash doesn't affect main backend)
- Independent scaling
- Clear separation of concerns

**Cons:**
- IPC overhead adds latency (5-20ms per call)
- Additional process management complexity
- Separate deployment/monitoring
- Database connection pooling complications

**Estimated Latency:** 50-100ms per context lookup

### 2.2 Option B: Embedded Server (Recommended)

```
┌──────────────────────────────────────────────────────┐
│                FastAPI Backend (Port 8000)           │
│  ┌────────────────────────────────────────────────┐  │
│  │             Application Context                │  │
│  │  ┌─────────────┐  ┌──────────────────────────┐│  │
│  │  │ Event       │  │     MCP Server Module    ││  │
│  │  │ Processor   │─►│  ┌──────────────────┐    ││  │
│  │  └─────────────┘  │  │ ArgusContext     │    ││  │
│  │                   │  │ Provider         │    ││  │
│  │  ┌─────────────┐  │  └──────────────────┘    ││  │
│  │  │ Context     │◄─┤                          ││  │
│  │  │ Prompt Svc  │  │  Resources:              ││  │
│  │  └─────────────┘  │  - entities://            ││  │
│  │                   │  - feedback://            ││  │
│  │                   │  - patterns://            ││  │
│  │                   └──────────────────────────┘│  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Pros:**
- Minimal latency (direct function calls, 5-20ms)
- Shared database sessions (no connection overhead)
- Single deployment unit
- Unified logging and monitoring
- Natural async integration with existing services

**Cons:**
- Larger process footprint
- MCP server failure could affect main backend (mitigated with error handling)

**Estimated Latency:** 20-50ms per context lookup

### 2.3 Option C: Standalone Service

```
┌─────────────────┐       HTTP        ┌─────────────────┐
│  FastAPI Backend│◄─────────────────►│   MCP Server    │
│   (Port 8000)   │    (Port 8001)    │  (Standalone)   │
└─────────────────┘                   └─────────────────┘
         │                                     │
         └──────────────┬──────────────────────┘
                        │
                 ┌──────▼──────┐
                 │   Database  │
                 │   (Shared)  │
                 └─────────────┘
```

**Pros:**
- Complete isolation
- Independent scaling (horizontal)
- Can be deployed on separate hardware

**Cons:**
- Network latency (10-50ms per call)
- Separate deployment and infrastructure
- Database connection management complexity
- CORS and authentication overhead

**Estimated Latency:** 80-150ms per context lookup

### 2.4 Recommendation Summary

| Criteria | Sidecar | Embedded | Standalone |
|----------|---------|----------|------------|
| **Latency** | 50-100ms | **20-50ms** | 80-150ms |
| **Deployment** | Medium | **Simple** | Complex |
| **Resource Usage** | Medium | **Low** | High |
| **Failure Isolation** | **Good** | Fair | **Good** |
| **Scalability** | Medium | Low | **High** |
| **Development Effort** | Medium | **Low** | High |

**Recommendation:** **Embedded Server** for ArgusAI

Rationale:
1. Event processing has <5s SLA with <100ms context overhead target
2. ArgusAI is a single-instance home deployment (no horizontal scaling needed)
3. Existing services already use async patterns compatible with embedded MCP
4. Single deployment unit simplifies Docker/K8s configuration

---

## 3. Context Data Schema

### 3.1 Complete Context Schema

```json
{
  "context_type": "argusai_event_context",
  "version": "1.0",
  "event_id": "evt-abc123",
  "generated_at": "2025-12-25T14:30:00Z",
  "data": {
    "feedback_history": {
      "recent_feedback": [
        {
          "event_id": "evt-xyz789",
          "rating": "not_helpful",
          "correction": "This was actually a neighbor, not a delivery person",
          "correction_type": null,
          "camera_id": "cam-123",
          "timestamp": "2025-12-24T10:15:00Z"
        }
      ],
      "camera_accuracy": {
        "camera_id": "cam-123",
        "total_feedback": 45,
        "helpful_count": 38,
        "accuracy_rate": 0.844
      },
      "common_corrections": [
        {"pattern": "delivery person", "actual": "neighbor", "count": 5},
        {"pattern": "package", "actual": "newspaper", "count": 3}
      ]
    },
    "known_entities": {
      "matched_entity": {
        "id": "ent-456",
        "type": "person",
        "name": "John (Neighbor)",
        "occurrence_count": 23,
        "first_seen": "2025-06-15T08:30:00Z",
        "last_seen": "2025-12-24T18:45:00Z",
        "is_vip": false,
        "is_blocked": false
      },
      "similar_entities": [
        {
          "id": "ent-789",
          "type": "person",
          "name": "Mail Carrier",
          "similarity_score": 0.72
        }
      ],
      "vehicle_entities": [
        {
          "id": "ent-veh-001",
          "type": "vehicle",
          "name": null,
          "vehicle_signature": "white-toyota-camry",
          "color": "white",
          "make": "toyota",
          "model": "camry"
        }
      ]
    },
    "entity_corrections": [
      {
        "original_entity_id": "ent-456",
        "corrected_entity_id": "ent-789",
        "correction_type": "manual_reassignment",
        "reason": "User identified as different person",
        "timestamp": "2025-12-20T14:00:00Z"
      }
    ],
    "camera_context": {
      "camera_id": "cam-123",
      "name": "Front Door",
      "location_hint": "Covers front porch and driveway entrance",
      "typical_activity": ["deliveries", "visitors", "pedestrians"],
      "detection_types_enabled": ["person", "vehicle", "package"],
      "false_positive_patterns": [
        {"trigger": "tree shadow", "frequency": "daily at 3pm"},
        {"trigger": "passing cars", "frequency": "occasional"}
      ]
    },
    "time_patterns": {
      "current_time": {
        "hour": 14,
        "day_of_week": "Wednesday",
        "is_weekend": false
      },
      "activity_level": {
        "expected": "medium",
        "confidence": 0.85,
        "basis": "30 days of history"
      },
      "typical_events_at_time": [
        {"type": "delivery", "probability": 0.35},
        {"type": "pedestrian", "probability": 0.45}
      ],
      "is_unusual_timing": false,
      "timing_note": "Activity is typical for this time of day"
    }
  }
}
```

### 3.2 Schema Component Details

#### 3.2.1 Feedback History Schema

```python
@dataclass
class FeedbackHistoryContext:
    """Recent feedback and accuracy metrics for AI prompt context."""

    # Recent feedback entries (last 10-20)
    recent_feedback: list[FeedbackEntry]

    # Per-camera accuracy statistics
    camera_accuracy: CameraAccuracyStats

    # Patterns of common corrections
    common_corrections: list[CorrectionPattern]

@dataclass
class FeedbackEntry:
    event_id: str
    rating: Literal["helpful", "not_helpful"]
    correction: Optional[str]
    correction_type: Optional[str]  # e.g., "not_package"
    camera_id: str
    timestamp: datetime

@dataclass
class CorrectionPattern:
    pattern: str      # What AI said
    actual: str       # What user corrected to
    count: int        # How many times this correction occurred
```

#### 3.2.2 Known Entities Schema

```python
@dataclass
class KnownEntitiesContext:
    """Entity information for recognition context."""

    # Entity matched to current event (if any)
    matched_entity: Optional[EntityInfo]

    # Similar entities that might be confused
    similar_entities: list[SimilarEntityInfo]

    # Vehicle entities relevant to this camera
    vehicle_entities: list[VehicleEntityInfo]

@dataclass
class EntityInfo:
    id: str
    type: Literal["person", "vehicle", "unknown"]
    name: Optional[str]
    occurrence_count: int
    first_seen: datetime
    last_seen: datetime
    is_vip: bool
    is_blocked: bool

@dataclass
class VehicleEntityInfo:
    id: str
    name: Optional[str]
    vehicle_signature: str  # e.g., "white-toyota-camry"
    color: str
    make: str
    model: str
```

#### 3.2.3 Camera Context Schema

```python
@dataclass
class CameraContextInfo:
    """Camera-specific context for better descriptions."""

    camera_id: str
    name: str
    location_hint: str

    # What types of activity typically occur here
    typical_activity: list[str]

    # Enabled detection types
    detection_types_enabled: list[str]

    # Known false positive triggers
    false_positive_patterns: list[FalsePositivePattern]

@dataclass
class FalsePositivePattern:
    trigger: str      # What causes false positives
    frequency: str    # How often (e.g., "daily at 3pm")
```

#### 3.2.4 Time Patterns Schema

```python
@dataclass
class TimePatternContext:
    """Time-of-day pattern information."""

    current_time: TimeInfo
    activity_level: ActivityLevelInfo
    typical_events_at_time: list[EventProbability]
    is_unusual_timing: bool
    timing_note: str

@dataclass
class ActivityLevelInfo:
    expected: Literal["low", "medium", "high"]
    confidence: float  # 0.0-1.0
    basis: str        # e.g., "30 days of history"

@dataclass
class EventProbability:
    type: str         # e.g., "delivery", "pedestrian"
    probability: float
```

---

## 4. MCP Server Implementation Design

### 4.1 Server Structure

```python
"""
ArgusAI MCP Server - Embedded in FastAPI Backend

Location: backend/app/services/mcp_server.py
"""
from mcp.server.fastmcp import FastMCP
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from app.services.entity_service import get_entity_service
from app.services.similarity_service import get_similarity_service
from app.services.pattern_service import get_pattern_service
from app.core.database import get_db

# Initialize MCP server
mcp = FastMCP("argusai-context")


@mcp.resource("argusai://entities/{entity_id}")
async def get_entity_resource(entity_id: str) -> dict:
    """
    Get detailed information about a known entity.

    Args:
        entity_id: UUID of the recognized entity

    Returns:
        Entity details including name, type, occurrence count,
        and recent sightings.
    """
    entity_service = get_entity_service()
    async with get_db() as db:
        entity = await entity_service.get_entity(db, entity_id)
        return entity.to_context_dict() if entity else {}


@mcp.resource("argusai://feedback/camera/{camera_id}")
async def get_camera_feedback(camera_id: str) -> dict:
    """
    Get feedback history and accuracy stats for a camera.

    Args:
        camera_id: UUID of the camera

    Returns:
        Recent feedback, accuracy rate, and common corrections.
    """
    async with get_db() as db:
        # Query recent feedback for this camera
        feedback_entries = await get_recent_feedback(db, camera_id, limit=20)
        accuracy_stats = await get_accuracy_stats(db, camera_id)
        corrections = await get_common_corrections(db, camera_id)

        return {
            "recent_feedback": [f.to_dict() for f in feedback_entries],
            "accuracy": accuracy_stats,
            "common_corrections": corrections
        }


@mcp.tool()
async def find_similar_events(
    event_id: str,
    limit: int = 5,
    min_similarity: float = 0.7
) -> list[dict]:
    """
    Find events visually similar to the given event.

    Use this to identify recurring patterns or visitors.

    Args:
        event_id: UUID of the reference event
        limit: Maximum number of similar events to return
        min_similarity: Minimum cosine similarity threshold (0.0-1.0)

    Returns:
        List of similar events with similarity scores and descriptions.
    """
    similarity_service = get_similarity_service()
    async with get_db() as db:
        similar = await similarity_service.find_similar_events(
            db=db,
            event_id=event_id,
            limit=limit,
            min_similarity=min_similarity
        )
        return [s.to_dict() for s in similar]


@mcp.tool()
async def get_event_context(
    event_id: str,
    camera_id: str,
    event_time: str  # ISO 8601 format
) -> dict:
    """
    Get comprehensive context for describing an event.

    Aggregates entity matches, feedback history, camera context,
    and time patterns into a single context object.

    Args:
        event_id: UUID of the event being described
        camera_id: UUID of the camera that captured the event
        event_time: When the event occurred (ISO 8601)

    Returns:
        Complete context object with all relevant information.
    """
    event_dt = datetime.fromisoformat(event_time)

    async with get_db() as db:
        context = await build_full_context(
            db=db,
            event_id=event_id,
            camera_id=camera_id,
            event_time=event_dt
        )
        return context


@mcp.prompt()
def description_with_context() -> str:
    """
    Prompt template for context-enhanced event descriptions.

    Returns:
        System prompt that incorporates available context.
    """
    return """
You are describing a security camera event with additional context.

{context_section}

When generating your description:
1. If a known entity is identified, use their name
2. If this appears to be a recurring event, mention the pattern
3. If timing is unusual, note this observation
4. Incorporate feedback corrections to avoid past mistakes
5. Be specific about actions observed (arrived, departed, delivered, etc.)

Generate a clear, natural description of what occurred.
"""
```

### 4.2 Integration with Event Processor

```python
"""
Modified Event Processor with MCP Integration

Location: backend/app/services/event_processor.py (modifications)
"""
from app.services.mcp_context import MCPContextProvider

class EventProcessor:
    def __init__(self):
        # ... existing initialization ...
        self._mcp_provider = MCPContextProvider()

    async def _generate_description(
        self,
        db: Session,
        event_id: str,
        camera_id: str,
        event_time: datetime,
        frames: list[bytes]
    ) -> str:
        """Generate AI description with MCP context."""

        # Step 1: Get MCP context (target: <50ms)
        start_time = time.time()

        try:
            mcp_context = await self._mcp_provider.get_context(
                db=db,
                event_id=event_id,
                camera_id=camera_id,
                event_time=event_time
            )
            context_time_ms = (time.time() - start_time) * 1000

            logger.info(
                "MCP context retrieved",
                extra={
                    "event_id": event_id,
                    "context_time_ms": round(context_time_ms, 2),
                    "has_entity": mcp_context.has_entity_match,
                    "has_feedback": len(mcp_context.feedback_history) > 0
                }
            )
        except Exception as e:
            # Fail open - continue without MCP context
            logger.warning(
                f"MCP context retrieval failed: {e}",
                extra={"event_id": event_id}
            )
            mcp_context = None

        # Step 2: Build prompt with or without context
        base_prompt = self._build_base_prompt(frames)

        if mcp_context:
            prompt = self._enhance_prompt_with_context(base_prompt, mcp_context)
        else:
            prompt = base_prompt

        # Step 3: Call AI provider
        return await self._ai_service.describe(prompt, frames)
```

### 4.3 Context Provider Implementation

```python
"""
MCP Context Provider - Orchestrates context gathering

Location: backend/app/services/mcp_context.py
"""
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.services.entity_service import get_entity_service, EntityMatchResult
from app.services.similarity_service import get_similarity_service
from app.services.pattern_service import get_pattern_service


@dataclass
class MCPEventContext:
    """Complete context for an event."""

    event_id: str
    camera_id: str
    event_time: datetime
    generated_at: datetime = field(default_factory=datetime.utcnow)

    # Entity context
    matched_entity: Optional[EntityMatchResult] = None
    similar_entities: list = field(default_factory=list)

    # Feedback context
    feedback_history: list = field(default_factory=list)
    camera_accuracy: Optional[dict] = None
    common_corrections: list = field(default_factory=list)

    # Camera context
    camera_name: str = ""
    location_hint: str = ""
    typical_activity: list = field(default_factory=list)
    false_positive_patterns: list = field(default_factory=list)

    # Time patterns
    activity_level: str = "medium"
    is_unusual_timing: bool = False
    timing_note: str = ""

    # Metadata
    context_time_ms: float = 0.0

    @property
    def has_entity_match(self) -> bool:
        return self.matched_entity is not None


class MCPContextProvider:
    """
    Provides MCP context for event description.

    Implements fail-open pattern - if any component fails,
    continues with available context.

    Target latency: <50ms total context gathering
    """

    TIMEOUT_MS = 80  # Slightly above target to allow for variance

    def __init__(self):
        self._entity_service = get_entity_service()
        self._similarity_service = get_similarity_service()
        self._pattern_service = get_pattern_service()

    async def get_context(
        self,
        db: Session,
        event_id: str,
        camera_id: str,
        event_time: datetime,
        embedding: Optional[list[float]] = None
    ) -> MCPEventContext:
        """
        Gather all context for an event.

        Runs context queries in parallel for minimum latency.
        Individual failures don't block other context sources.

        Args:
            db: Database session
            event_id: Event being described
            camera_id: Camera that captured the event
            event_time: When the event occurred
            embedding: Optional pre-computed event embedding

        Returns:
            MCPEventContext with all available context
        """
        start_time = time.time()
        context = MCPEventContext(
            event_id=event_id,
            camera_id=camera_id,
            event_time=event_time
        )

        # Run context queries in parallel
        tasks = [
            self._get_entity_context(db, embedding, context),
            self._get_feedback_context(db, camera_id, context),
            self._get_camera_context(db, camera_id, context),
            self._get_time_context(db, camera_id, event_time, context),
        ]

        # Wait with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.TIMEOUT_MS / 1000
            )
        except asyncio.TimeoutError:
            logger.warning(
                "MCP context gathering timed out",
                extra={"event_id": event_id, "timeout_ms": self.TIMEOUT_MS}
            )

        context.context_time_ms = (time.time() - start_time) * 1000
        return context

    async def _get_entity_context(
        self,
        db: Session,
        embedding: Optional[list[float]],
        context: MCPEventContext
    ) -> None:
        """Get entity match and similar entities."""
        if not embedding:
            return

        try:
            match = await self._entity_service.match_entity(
                db=db,
                embedding=embedding,
                entity_type="person"
            )
            if match:
                context.matched_entity = match
        except Exception as e:
            logger.warning(f"Entity context failed: {e}")

    async def _get_feedback_context(
        self,
        db: Session,
        camera_id: str,
        context: MCPEventContext
    ) -> None:
        """Get feedback history and accuracy stats."""
        try:
            # Get recent feedback for this camera
            from app.models.event_feedback import EventFeedback
            from app.models.event import Event

            recent = (
                db.query(EventFeedback)
                .join(Event)
                .filter(Event.camera_id == camera_id)
                .order_by(EventFeedback.created_at.desc())
                .limit(20)
                .all()
            )
            context.feedback_history = [
                {
                    "rating": f.rating,
                    "correction": f.correction,
                    "correction_type": f.correction_type
                }
                for f in recent
            ]

            # Calculate accuracy
            total = len(recent)
            helpful = sum(1 for f in recent if f.rating == "helpful")
            if total > 0:
                context.camera_accuracy = {
                    "total": total,
                    "helpful": helpful,
                    "rate": helpful / total
                }
        except Exception as e:
            logger.warning(f"Feedback context failed: {e}")

    async def _get_camera_context(
        self,
        db: Session,
        camera_id: str,
        context: MCPEventContext
    ) -> None:
        """Get camera-specific context."""
        try:
            from app.models.camera import Camera

            camera = db.query(Camera).filter(Camera.id == camera_id).first()
            if camera:
                context.camera_name = camera.name
                context.location_hint = camera.location or ""
        except Exception as e:
            logger.warning(f"Camera context failed: {e}")

    async def _get_time_context(
        self,
        db: Session,
        camera_id: str,
        event_time: datetime,
        context: MCPEventContext
    ) -> None:
        """Get time-of-day pattern context."""
        try:
            result = await self._pattern_service.is_typical_timing(
                db=db,
                camera_id=camera_id,
                timestamp=event_time
            )

            if result.is_typical is not None:
                context.is_unusual_timing = not result.is_typical
                context.timing_note = result.reason
                context.activity_level = (
                    "high" if result.confidence > 0.8
                    else "medium" if result.confidence > 0.5
                    else "low"
                )
        except Exception as e:
            logger.warning(f"Time context failed: {e}")
```

---

## 5. Performance Analysis

### 5.1 Latency Budget

| Component | Target | Expected | Notes |
|-----------|--------|----------|-------|
| Entity lookup | 10ms | 5-15ms | Cached embedding comparison |
| Feedback query | 15ms | 10-20ms | Indexed camera_id query |
| Camera query | 5ms | 3-8ms | Primary key lookup |
| Time patterns | 10ms | 5-15ms | Pre-calculated patterns |
| **Total context** | **<50ms** | **25-60ms** | Parallel execution |
| Prompt construction | 5ms | 2-5ms | String formatting |
| **Total MCP overhead** | **<100ms** | **30-70ms** | Within SLA |

### 5.2 Memory Footprint

| Component | Memory | Notes |
|-----------|--------|-------|
| MCP server module | ~5MB | Python module + SDK |
| Context cache (optional) | 10-50MB | If caching recent contexts |
| Embedding comparisons | ~2MB per 1000 entities | 512-dim float32 vectors |

### 5.3 Optimization Strategies

1. **Parallel Queries**: Execute entity, feedback, camera, and time queries concurrently
2. **Fail Open**: Any component failure doesn't block others
3. **Timeout Enforcement**: Hard 80ms timeout on context gathering
4. **Query Optimization**: Index camera_id and created_at in feedback table
5. **Lazy Loading**: Only load MCP module when first context is requested

---

## 6. Implementation Roadmap

### 6.1 Phase 1: Foundation (MVP)

**Effort:** 1-2 days
**Scope:**
- Create `backend/app/services/mcp_context.py` with MCPContextProvider
- Implement feedback history context (highest impact)
- Add basic entity match context
- Integrate with `context_prompt_service.py`

**Deliverables:**
- Feedback context in AI prompts
- Entity recognition context

### 6.2 Phase 2: Full Context

**Effort:** 1-2 days
**Scope:**
- Add camera context (location hints, typical activity)
- Add time pattern context
- Implement context caching (optional)

**Deliverables:**
- Complete context schema implementation
- All context sources integrated

### 6.3 Phase 3: MCP Protocol

**Effort:** 2-3 days
**Scope:**
- Install `mcp` package
- Implement MCP resources and tools
- Enable external MCP client connections (optional)

**Deliverables:**
- Full MCP protocol compliance
- External tool compatibility

### 6.4 Dependencies

| Dependency | Required | Purpose |
|------------|----------|---------|
| `mcp[cli]` | Phase 3 | MCP SDK with CLI tools |
| Existing `sentence-transformers` | Phase 1 | Already installed for embeddings |
| Existing `fastapi` | Phase 1 | Already installed |
| Existing `sqlalchemy` | Phase 1 | Already installed |

---

## 7. Open Questions and Future Considerations

### 7.1 Resolved Questions

| Question | Resolution |
|----------|------------|
| Sidecar vs embedded? | **Embedded** - lowest latency, simplest deployment |
| Context schema format? | **Dataclasses** with JSON serialization |
| Failure handling? | **Fail open** - continue without context if errors |

### 7.2 Open Questions for Future Resolution

| Question | Considerations |
|----------|---------------|
| Q1: Should context be cached? | Pro: Faster repeat lookups. Con: Stale data. Recommend: Short TTL (60s) if implementing. |
| Q2: How to handle conflicting corrections? | If user says "delivery" but later "neighbor", which takes precedence? Recommend: Most recent wins. |
| Q3: Optimal embedding dimension? | Current: 512 (CLIP ViT-B/32). SigLIP uses 768. Recommend: Stay with 512 for now, evaluate if accuracy issues. |
| Q4: Should MCP expose to external clients? | Phase 3 consideration. Enables Claude Desktop integration but adds security surface. |

### 7.3 Future Enhancements

1. **Query-Adaptive Context**: Select context based on re-analysis query (Story P10-6.2)
2. **Context A/B Testing**: Compare description quality with/without context
3. **Context Metrics Dashboard**: Track context usage and impact
4. **External MCP Clients**: Allow Claude Desktop to query ArgusAI context

---

## 8. Conclusion

Implementing a local MCP server for ArgusAI is feasible and beneficial. The **embedded approach** is recommended due to its low latency (<50ms), simple deployment, and natural integration with existing async services.

The proposed context schema covers all key data sources:
- Feedback history for learning from corrections
- Known entities for recognition
- Camera context for location awareness
- Time patterns for typical activity

With parallel query execution and fail-open error handling, the MCP context can be gathered within the 100ms overhead budget while maintaining the <5s event processing SLA.

**Next Step:** Begin Phase 1 implementation by creating the `MCPContextProvider` class and integrating with the existing `ContextEnhancedPromptService`.

---

## References

- [Anthropic Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Python Package on PyPI](https://pypi.org/project/mcp/)
- [Anthropic MCP Introduction Blog](https://www.anthropic.com/news/model-context-protocol)
- [Source: docs/sprint-artifacts/tech-spec-epic-P10-6.md]
- [Source: backend/app/services/context_prompt_service.py]
- [Source: backend/app/services/embedding_service.py]
- [Source: backend/app/models/event_feedback.py]
- [Source: backend/app/models/recognized_entity.py]
