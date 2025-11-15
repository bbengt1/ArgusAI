# Implementation Patterns

[← Back to Architecture Index](./README.md) | [← Previous: API Contracts](./07-api-contracts.md) | [Next: Security Architecture →](./09-security-architecture.md)

---

## Implementation Patterns

### Naming Conventions

**Backend (Python):**
- **Files:** `snake_case.py` (e.g., `camera_service.py`, `event_processor.py`)
- **Classes:** `PascalCase` (e.g., `CameraService`, `EventProcessor`, `AlertRule`)
- **Functions/Methods:** `snake_case` (e.g., `process_event`, `get_camera_by_id`, `evaluate_rule`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`, `AI_MODEL_PRIMARY`)
- **Private methods:** `_leading_underscore` (e.g., `_capture_frame`, `_encrypt_api_key`)
- **Database tables:** `snake_case` plural (e.g., `cameras`, `events`, `alert_rules`, `system_settings`)
- **Database columns:** `snake_case` (e.g., `camera_id`, `created_at`, `is_enabled`, `rtsp_url`)
- **Foreign keys:** `{table_singular}_id` (e.g., `camera_id`, `user_id`, `alert_rule_id`)
- **API endpoints:** `kebab-case` (e.g., `/api/v1/alert-rules`, `/api/v1/event-stats`)

**Frontend (TypeScript/React):**
- **Component files:** `PascalCase.tsx` (e.g., `EventCard.tsx`, `CameraPreview.tsx`, `AlertRuleForm.tsx`)
- **Utility files:** `kebab-case.ts` (e.g., `api-client.ts`, `websocket.ts`, `utils.ts`)
- **Components:** `PascalCase` (e.g., `EventCard`, `CameraPreview`, `Header`)
- **Functions:** `camelCase` (e.g., `fetchEvents`, `handleSubmit`, `formatDate`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `API_BASE_URL`, `WS_RECONNECT_DELAY`)
- **Types/Interfaces:** `PascalCase`, interfaces prefixed with `I` (e.g., `IEvent`, `ICameraConfig`, `IAlertRule`)
- **Hooks:** `use` prefix (e.g., `useEvents`, `useCameras`, `useWebSocket`)
- **Context:** `PascalCase` with `Context` suffix (e.g., `AuthContext`, `WebSocketContext`)
- **CSS classes:** Tailwind utilities (avoid custom classes unless necessary)

### Code Organization

**Backend Service Pattern:**
```python
# app/services/camera_service.py
from typing import Optional, List
import cv2
import threading
from app.models.camera import Camera
from app.core.logging import logger

class CameraService:
    """Handles camera capture and RTSP connection management."""
    
    def __init__(self):
        self._capture_threads: dict[str, threading.Thread] = {}
        self._active_captures: dict[str, cv2.VideoCapture] = {}
    
    async def start_camera(self, camera: Camera) -> bool:
        """Start capturing from camera in background thread."""
        try:
            # Implementation...
            logger.info(f"Started camera {camera.id}", extra={"camera_id": camera.id})
            return True
        except Exception as e:
            logger.error(f"Failed to start camera {camera.id}: {e}", exc_info=True)
            return False
    
    async def stop_camera(self, camera_id: str) -> None:
        """Stop camera capture thread."""
        # Implementation...
    
    def _capture_loop(self, camera: Camera) -> None:
        """Private method: continuous frame capture loop."""
        # Implementation...
```

**Frontend Hook Pattern:**
```typescript
// hooks/useEvents.ts
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import type { IEvent, EventFilters } from '@/types/event';

export function useEvents(filters?: EventFilters) {
  const [events, setEvents] = useState<IEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const data = await apiClient.get('/events', { params: filters });
        setEvents(data.data);
      } catch (err) {
        setError(err.message || 'Failed to fetch events');
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [filters]);

  return { events, loading, error };
}
```

### Error Handling

**Backend Error Pattern:**
```python
from fastapi import HTTPException, status
from app.core.logging import logger

async def process_event(event_id: str) -> Event:
    try:
        event = await event_service.process(event_id)
        return event
    except EventNotFoundError as e:
        logger.warning(f"Event not found: {event_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )
    except AIServiceError as e:
        logger.error(f"AI service failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

**Frontend Error Pattern:**
```typescript
try {
  const camera = await apiClient.post('/cameras', cameraData);
  toast.success('Camera added successfully');
  router.push('/cameras');
} catch (error) {
  console.error('Failed to add camera:', error);
  
  if (error.status === 400) {
    toast.error(error.message || 'Invalid camera configuration');
  } else if (error.status === 409) {
    toast.error('Camera with this name already exists');
  } else {
    toast.error('Failed to add camera. Please try again.');
  }
}
```

### Logging Standards

**Log Levels:**
- `DEBUG`: Detailed diagnostic info (frame capture details, motion detection metrics)
- `INFO`: General informational messages (event processed, alert triggered, camera started)
- `WARNING`: Something unexpected but not breaking (AI API slow, camera lagging, high queue)
- `ERROR`: Error occurred but handled (AI API failed with fallback, camera disconnected)
- `CRITICAL`: System cannot continue (database connection lost, all AI providers down)

**Structured Logging:**
```python
logger.info(
    f"Event {event_id} processed successfully",
    extra={
        "event_id": event_id,
        "camera_id": camera_id,
        "processing_time_ms": duration_ms,
        "confidence": confidence,
        "objects_detected": objects,
        "ai_provider": "openai"
    }
)
```

**What NOT to log:**
- Passwords or API keys (use `[REDACTED]` placeholder)
- Full RTSP URLs with credentials
- User personal data beyond IDs
- Full stack traces in production (sanitize)

### Date/Time Handling

**Backend:**
- Store all timestamps in UTC (no timezone)
- Use `datetime.datetime.utcnow()` for current time
- SQLAlchemy: `DateTime(timezone=False)` (SQLite doesn't support timezones)
- API responses: ISO 8601 format (`2025-11-15T10:30:00Z`)

```python
from datetime import datetime

# Create timestamp
timestamp = datetime.utcnow()

# Store in database
event.timestamp = timestamp

# Return in API response
return {
    "timestamp": timestamp.isoformat() + "Z"  # Add 'Z' for UTC indicator
}
```

**Frontend:**
- Display times in user's local timezone
- Use `date-fns` for all date formatting
- Recent events: relative time ("5 minutes ago", "2 hours ago")
- Older events: absolute time ("Nov 15, 10:30 AM")

```typescript
import { formatDistanceToNow, format } from 'date-fns';

// Display logic
const displayTime = (timestamp: string) => {
  const date = new Date(timestamp);
  const hoursAgo = (Date.now() - date.getTime()) / (1000 * 60 * 60);
  
  if (hoursAgo < 24) {
    return formatDistanceToNow(date, { addSuffix: true }); // "5 minutes ago"
  } else {
    return format(date, 'MMM d, h:mm a'); // "Nov 15, 10:30 AM"
  }
};
```

### Testing Patterns

**Backend Unit Test:**
```python
# tests/test_services/test_motion_detection.py
import pytest
from app.services.motion_detection import MotionDetectionService

@pytest.fixture
def motion_service():
    return MotionDetectionService(sensitivity='medium')

def test_detect_motion_with_significant_change(motion_service):
    # Arrange
    frame1 = load_test_image('empty_room.jpg')
    frame2 = load_test_image('person_enters.jpg')
    
    # Act
    motion_detected = motion_service.detect_motion(frame1, frame2)
    
    # Assert
    assert motion_detected is True

def test_detect_motion_no_change(motion_service):
    frame = load_test_image('empty_room.jpg')
    motion_detected = motion_service.detect_motion(frame, frame)
    assert motion_detected is False
```

**Frontend Component Test:**
```typescript
// components/events/EventCard.test.tsx
import { render, screen } from '@testing-library/react';
import { EventCard } from './EventCard';

const mockEvent = {
  id: 'event-123',
  timestamp: '2025-11-15T10:30:00Z',
  description: 'Person wearing blue jacket approaching front door',
  confidence: 85,
  objects_detected: ['person'],
  camera_id: 'camera-1'
};

test('renders event card with description', () => {
  render(<EventCard event={mockEvent} />);
  expect(screen.getByText(/Person wearing blue jacket/i)).toBeInTheDocument();
});

test('displays confidence score', () => {
  render(<EventCard event={mockEvent} />);
  expect(screen.getByText('85%')).toBeInTheDocument();
});
```

---

---

[← Previous: API Contracts](./07-api-contracts.md) | [Next: Security Architecture →](./09-security-architecture.md) | [Back to Index](./README.md)
