# Phase 15 Additions

**Date:** 2025-12-30
**Author:** Architecture Workflow
**Version:** 1.0

---

## Phase 15 Executive Summary

Phase 15 transforms ArgusAI from a single-user system to a **multi-user platform** with proper authentication, session management, and role-based access control. It also addresses UX friction points in entity modals and settings pages, adds multi-entity event support, and introduces AI visual annotations.

**Key Architectural Changes:**
- New User and Session models with JWT-based authentication
- Role-Based Access Control (RBAC) with three permission levels
- Virtual scrolling for entity event lists
- Standardized settings form state management
- Multi-entity event relationships (many-to-many)
- AI bounding box annotations on frames

---

## Phase 15 Technology Stack Additions

| Technology | Version | Purpose |
|------------|---------|---------|
| passlib | 1.7.4 | Password hashing with bcrypt backend |
| python-jose | 3.3.0 | JWT token generation and validation |
| @tanstack/react-virtual | 3.x | Virtual scrolling for large lists |
| Pillow | 10.x | Drawing bounding boxes on frames |

**Note:** Most Phase 15 functionality builds on existing dependencies. The above are additions or new use cases.

---

## Phase 15 Project Structure Additions

```
backend/app/
├── models/
│   ├── user.py              # NEW: User model with roles
│   └── session.py           # NEW: Session tracking model
├── schemas/
│   ├── user.py              # NEW: User request/response schemas
│   └── session.py           # NEW: Session schemas
├── api/v1/
│   ├── users.py             # NEW: User management endpoints
│   └── auth.py              # EXTENDED: Session management endpoints
├── services/
│   ├── password_service.py          # NEW: Password hashing/validation
│   ├── session_service.py           # NEW: Session management
│   └── frame_annotation_service.py  # NEW: Bounding box drawing
└── core/
    └── permissions.py       # NEW: RBAC dependency decorators

frontend/
├── app/
│   └── change-password/
│       └── page.tsx         # NEW: Force password change page
├── components/
│   ├── settings/
│   │   ├── UserManagement.tsx       # NEW: User admin UI
│   │   ├── SessionList.tsx          # NEW: Active sessions UI
│   │   └── UnsavedIndicator.tsx     # NEW: Dirty form indicator
│   ├── entities/
│   │   └── EntityDetailModal.tsx    # MODIFIED: Virtual scroll, event click
│   └── events/
│       ├── EventCard.tsx            # MODIFIED: Multi-entity badges
│       └── AnnotationLegend.tsx     # NEW: Bounding box color legend
├── hooks/
│   ├── useSettingsForm.ts           # NEW: Form state management hook
│   └── useUnsavedChangesWarning.ts  # NEW: Navigation warning hook
└── lib/
    └── api-client.ts        # EXTENDED: User/session endpoints
```

---

## Phase 15 Database Schema Additions

### User Model (P15-2.1)

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,                    -- UUID
    email TEXT UNIQUE NOT NULL,             -- Login email (unique)
    password_hash TEXT NOT NULL,            -- bcrypt hash (cost factor 12)
    role TEXT NOT NULL DEFAULT 'viewer',    -- 'admin', 'operator', 'viewer'
    is_active BOOLEAN DEFAULT TRUE,         -- Account enabled/disabled
    must_change_password BOOLEAN DEFAULT FALSE, -- Force password change flag
    password_expires_at TIMESTAMP,          -- For temporary passwords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP                 -- Last successful login
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

**Role Enum Values:**
- `admin` - Full system access including user management
- `operator` - Manage events, entities, cameras (no user management)
- `viewer` - Read-only access to dashboard and events

### Session Model (P15-2.2)

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                    -- UUID
    user_id TEXT NOT NULL,                  -- FK to users.id
    token_hash TEXT NOT NULL,               -- SHA-256 hash of JWT for validation
    device_info TEXT,                       -- Parsed from User-Agent (e.g., "Chrome on Windows")
    ip_address TEXT,                        -- Client IP
    user_agent TEXT,                        -- Full User-Agent string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,          -- Session expiration
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

### Event Model Extensions (P15-5.3)

```sql
-- Add to existing events table
ALTER TABLE events ADD COLUMN has_annotations BOOLEAN DEFAULT FALSE;
ALTER TABLE events ADD COLUMN bounding_boxes TEXT;  -- JSON array of bounding box data
```

**Bounding Boxes JSON Structure:**
```json
[
  {
    "x": 0.25,           // Normalized 0-1 (left edge)
    "y": 0.30,           // Normalized 0-1 (top edge)
    "width": 0.15,       // Normalized 0-1
    "height": 0.40,      // Normalized 0-1
    "entity_type": "person",
    "confidence": 0.92,
    "label": "Person walking toward door"
  }
]
```

---

## Phase 15 Service Architecture

### Authentication & Session Flow (P15-2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Authentication Flow                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────┐    POST /login     ┌─────────────┐    Validate     ┌─────┐ │
│  │ Browser │ ─────────────────► │  AuthRouter │ ──────────────► │ DB  │ │
│  │         │                    │             │                 │     │ │
│  │         │ ◄───────────────── │             │ ◄────────────── │     │ │
│  └─────────┘   Set-Cookie JWT   └─────────────┘    User + Hash  └─────┘ │
│       │                              │                                   │
│       │ must_change_password?        │ Create Session                   │
│       │        ┌─────────────────────┘                                   │
│       ▼        ▼                                                         │
│  ┌─────────────────────┐    ┌─────────────────────┐                     │
│  │ /change-password    │    │  SessionService     │                     │
│  │ (Force change UI)   │    │  - Track device/IP  │                     │
│  └─────────────────────┘    │  - Update last_active│                    │
│                             │  - Enforce limits   │                     │
│                             └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### PasswordService (P15-2.4)

```python
# backend/app/services/password_service.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

class PasswordService:
    COMPLEXITY_RULES = {
        "min_length": 8,
        "require_upper": True,
        "require_lower": True,
        "require_digit": True,
        "require_special": True,
        "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?"
    }

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt cost factor 12."""
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain, hashed)

    def validate_complexity(self, password: str) -> list[str]:
        """Return list of failed rules (empty if valid)."""
        errors = []
        if len(password) < 8:
            errors.append("Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            errors.append("Password must contain an uppercase letter")
        if not any(c.islower() for c in password):
            errors.append("Password must contain a lowercase letter")
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain a number")
        if not any(c in self.COMPLEXITY_RULES["special_chars"] for c in password):
            errors.append("Password must contain a special character")
        return errors
```

### SessionService (P15-2.7, P15-2.8)

```python
# backend/app/services/session_service.py
class SessionService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.max_sessions = settings.MAX_SESSIONS_PER_USER  # Default: 5
        self.expiry_hours = settings.SESSION_EXPIRY_HOURS   # Default: 24

    def create_session(self, user_id: str, token: str, request: Request) -> Session:
        """Create new session, enforcing max concurrent limit."""
        # Enforce max sessions - remove oldest if at limit
        user_sessions = self.db.query(Session).filter(
            Session.user_id == user_id,
            Session.expires_at > datetime.utcnow()
        ).order_by(Session.created_at.asc()).all()

        if len(user_sessions) >= self.max_sessions:
            self.db.delete(user_sessions[0])  # Remove oldest

        # Create new session
        session = Session(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            device_info=self._parse_user_agent(request.headers.get("user-agent")),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            expires_at=datetime.utcnow() + timedelta(hours=self.expiry_hours)
        )
        self.db.add(session)
        self.db.commit()
        return session

    def update_activity(self, token_hash: str):
        """Update last_active_at on each authenticated request."""
        self.db.query(Session).filter(Session.token_hash == token_hash).update(
            {"last_active_at": datetime.utcnow()}
        )
        self.db.commit()

    def revoke_session(self, session_id: str, user_id: str):
        """Revoke specific session."""
        self.db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user_id
        ).delete()
        self.db.commit()

    def revoke_all_except_current(self, user_id: str, current_token_hash: str):
        """Revoke all sessions except the current one."""
        self.db.query(Session).filter(
            Session.user_id == user_id,
            Session.token_hash != current_token_hash
        ).delete()
        self.db.commit()
```

### RBAC Permissions (P15-2.9)

```python
# backend/app/core/permissions.py
from fastapi import Depends, HTTPException, status
from app.models.user import User, Role

def require_role(*allowed_roles: Role):
    """FastAPI dependency to require specific roles."""
    async def check_role(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized for this action"
            )
        return current_user
    return check_role

# Usage in routers:
@router.get("/users")
async def list_users(user: User = Depends(require_role(Role.ADMIN))):
    ...

@router.post("/events/{id}/entity")
async def assign_entity(user: User = Depends(require_role(Role.ADMIN, Role.OPERATOR))):
    ...
```

**Permission Matrix:**

| Endpoint Pattern | Admin | Operator | Viewer |
|-----------------|-------|----------|--------|
| `GET /events/*` | ✓ | ✓ | ✓ |
| `POST/PUT/DELETE /events/*` | ✓ | ✓ | ✗ |
| `GET /cameras/*` | ✓ | ✓ | ✓ |
| `POST/PUT/DELETE /cameras/*` | ✓ | ✓ | ✗ |
| `GET /entities/*` | ✓ | ✓ | ✓ |
| `POST/PUT/DELETE /entities/*` | ✓ | ✓ | ✗ |
| `*/users/*` | ✓ | ✗ | ✗ |
| `*/settings/*` | ✓ | ✓ | ✗ |
| `GET /system/*` | ✓ | ✓ | ✓ |
| `PUT /system/*` | ✓ | ✗ | ✗ |

### FrameAnnotationService (P15-5.2)

```python
# backend/app/services/frame_annotation_service.py
from PIL import Image, ImageDraw, ImageFont

class FrameAnnotationService:
    # Color palette by entity type (RGB)
    COLORS = {
        "person": (59, 130, 246),    # Blue
        "vehicle": (34, 197, 94),    # Green
        "package": (249, 115, 22),   # Orange
        "animal": (168, 85, 247),    # Purple
        "other": (156, 163, 175),    # Gray
    }

    def annotate_frame(
        self,
        frame_path: str,
        bounding_boxes: list[dict]
    ) -> str:
        """Draw bounding boxes on frame and return annotated path."""
        img = Image.open(frame_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size

        for box in bounding_boxes:
            # Convert normalized coordinates to pixels
            x1 = int(box["x"] * width)
            y1 = int(box["y"] * height)
            x2 = int((box["x"] + box["width"]) * width)
            y2 = int((box["y"] + box["height"]) * height)

            color = self.COLORS.get(box["entity_type"], self.COLORS["other"])

            # Draw rectangle (2px stroke)
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

            # Draw label with confidence
            label = f"{box['entity_type']} {int(box['confidence'] * 100)}%"
            self._draw_label(draw, label, x1, y1 - 20, color)

        # Save annotated version
        annotated_path = frame_path.replace(".jpg", "_annotated.jpg")
        img.save(annotated_path, quality=90)
        return annotated_path

    def _draw_label(self, draw, text, x, y, color):
        """Draw label with background for readability."""
        # White background for text
        bbox = draw.textbbox((x, y), text)
        draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], fill=(255, 255, 255))
        draw.text((x, y), text, fill=color)
```

---

## Phase 15 API Contracts

### User Management API (P15-2.3)

```yaml
# POST /api/v1/users - Create user (Admin only)
Request:
  email: string (required)
  role: "admin" | "operator" | "viewer" (required)
  send_email: boolean (optional, default false)

Response:
  id: string
  email: string
  role: string
  is_active: boolean
  must_change_password: boolean
  temporary_password: string | null  # Only shown if send_email=false
  created_at: string (ISO 8601)

# GET /api/v1/users - List all users (Admin only)
Response:
  - id: string
    email: string
    role: string
    is_active: boolean
    last_login_at: string | null
    created_at: string

# PUT /api/v1/users/{id} - Update user (Admin only)
Request:
  email: string (optional)
  role: string (optional)
  is_active: boolean (optional)

Response:
  id: string
  email: string
  role: string
  is_active: boolean
  updated_at: string

# DELETE /api/v1/users/{id} - Delete user (Admin only)
Response: 204 No Content

# POST /api/v1/users/{id}/reset - Reset password (Admin only)
Response:
  temporary_password: string
  expires_at: string (72 hours from now)
```

### Session Management API (P15-2.7)

```yaml
# GET /api/v1/auth/sessions - List active sessions
Response:
  - id: string
    device_info: string
    ip_address: string
    created_at: string
    last_active_at: string
    is_current: boolean  # True if this is the requesting session

# DELETE /api/v1/auth/sessions/{id} - Revoke specific session
Response: 204 No Content

# DELETE /api/v1/auth/sessions - Revoke all except current
Response:
  revoked_count: number

# POST /api/v1/auth/change-password
Request:
  current_password: string (required unless must_change_password=true)
  new_password: string (required)

Response:
  success: boolean
  message: string
```

### Multi-Entity Events API (P15-4.1)

```yaml
# GET /api/v1/events/{id}
Response:
  id: string
  # ... existing fields ...
  matched_entity_ids: string[]  # Array instead of single ID
  matched_entities:             # Populated entity objects
    - id: string
      name: string
      type: string
      avatar_url: string | null

# PUT /api/v1/events/{id}/entities - Assign multiple entities
Request:
  entity_ids: string[]  # Array of entity IDs

Response:
  id: string
  matched_entity_ids: string[]
  matched_entities: Entity[]
```

### AI Bounding Boxes API (P15-5.1)

```yaml
# GET /api/v1/events/{id}
Response:
  # ... existing fields ...
  has_annotations: boolean
  bounding_boxes:
    - x: number (0-1)
      y: number (0-1)
      width: number (0-1)
      height: number (0-1)
      entity_type: "person" | "vehicle" | "package" | "animal" | "other"
      confidence: number (0-1)
      label: string
  thumbnail_path: string           # Original frame
  annotated_thumbnail_path: string | null  # Annotated frame (if has_annotations)
```

---

## Phase 15 Frontend Architecture

### Entity Modal Virtual Scrolling (P15-1.2)

```tsx
// frontend/components/entities/EntityDetailModal.tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function EntityEventList({ events }: { events: Event[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: events.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,  // Estimated row height
    overscan: 5,             // Render 5 extra items outside viewport
  });

  return (
    <div ref={parentRef} className="max-h-[60vh] overflow-y-auto">
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: 'absolute',
              top: 0,
              transform: `translateY(${virtualRow.start}px)`,
              width: '100%',
            }}
          >
            <EventListItem
              event={events[virtualRow.index]}
              onClick={() => setSelectedEvent(events[virtualRow.index])}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Settings Form Hook (P15-3.2)

```tsx
// frontend/hooks/useSettingsForm.ts
import { useState, useCallback, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useSettingsForm<T extends object>(
  initialData: T,
  saveFn: (data: T) => Promise<void>,
  queryKey: string[]
) {
  const [formData, setFormData] = useState<T>(initialData);
  const queryClient = useQueryClient();

  const isDirty = useMemo(() => {
    return JSON.stringify(formData) !== JSON.stringify(initialData);
  }, [formData, initialData]);

  const mutation = useMutation({
    mutationFn: saveFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });

  const save = useCallback(async () => {
    await mutation.mutateAsync(formData);
  }, [formData, mutation]);

  const reset = useCallback(() => {
    setFormData(initialData);
  }, [initialData]);

  const updateField = useCallback(<K extends keyof T>(field: K, value: T[K]) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  return {
    formData,
    setFormData,
    updateField,
    isDirty,
    save,
    reset,
    isLoading: mutation.isPending,
    error: mutation.error,
  };
}
```

### Unsaved Changes Warning (P15-3.4)

```tsx
// frontend/hooks/useUnsavedChangesWarning.ts
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export function useUnsavedChangesWarning(isDirty: boolean) {
  const router = useRouter();

  // Browser close/refresh warning
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = '';  // Required for Chrome
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isDirty]);

  // SPA navigation warning (handled via confirmation dialog)
  const confirmNavigation = useCallback(() => {
    if (!isDirty) return true;
    return window.confirm('You have unsaved changes. Discard changes?');
  }, [isDirty]);

  return { confirmNavigation };
}
```

---

## Phase 15 Architecture Decision Records

### ADR-P15-001: Session-Based Authentication with JWT

**Status:** Accepted

**Context:**
ArgusAI Phase 1.5 implemented stub authentication. Phase 15 requires production-ready multi-user authentication with session tracking.

**Decision:**
Use JWT tokens stored in HTTP-only cookies with server-side session tracking in the database.

**Rationale:**
- HTTP-only cookies prevent XSS token theft
- Server-side session tracking enables:
  - Viewing active sessions
  - Remote session revocation
  - Concurrent session limits
  - Last activity tracking
- JWT provides stateless validation for most requests
- Token hash stored in DB allows invalidation without blacklists

**Consequences:**
- Every authenticated request updates `last_active_at` (acceptable overhead)
- Session cleanup requires background task (already have APScheduler)

### ADR-P15-002: bcrypt with Cost Factor 12

**Status:** Accepted

**Context:**
Password hashing algorithm and cost factor selection.

**Decision:**
Use bcrypt via passlib with cost factor 12.

**Rationale:**
- bcrypt is industry standard for password hashing
- Cost factor 12 provides ~250ms hash time (good balance of security vs UX)
- passlib provides upgrade path if bcrypt is deprecated
- Aligns with OWASP recommendations

**Consequences:**
- Login takes ~250ms for password verification
- Password changes require same overhead

### ADR-P15-003: Three-Role RBAC (Admin/Operator/Viewer)

**Status:** Accepted

**Context:**
Role-based access control granularity for multi-user support.

**Decision:**
Implement three fixed roles: Admin, Operator, Viewer.

**Rationale:**
- Simple model covers 95% of use cases
- Admin: Full access (system owner/family admin)
- Operator: Can manage security data but not users (family members)
- Viewer: Read-only (guests, monitoring-only accounts)
- Avoids complexity of custom permissions
- Matches PRD requirements (FR17-FR22)

**Consequences:**
- Cannot create custom permission combinations
- Future: Could add `permissions` JSON field for fine-grained control

### ADR-P15-004: Virtual Scrolling for Entity Events

**Status:** Accepted

**Context:**
Entity detail modals can show 1000+ events, causing performance issues.

**Decision:**
Use @tanstack/react-virtual for virtualized event lists.

**Rationale:**
- Only renders visible rows (~10-15 at a time)
- Maintains smooth 60fps scrolling
- Library already used elsewhere in React ecosystem
- Meets NFR7: 500ms load time with 1000+ events
- Threshold: Enable virtualization when event count > 50

**Consequences:**
- Slightly more complex component code
- Must maintain consistent row heights for scroll accuracy

### ADR-P15-005: Explicit Save Pattern for Settings

**Status:** Accepted

**Context:**
Settings pages use inconsistent save patterns (some auto-save, some require button).

**Decision:**
Standardize on explicit Save button pattern for all settings.

**Rationale:**
- Predictable user experience
- Prevents accidental changes
- Clear indication of what will be changed
- Allows batch changes before commit
- Enables cancel/reset functionality

**Consequences:**
- Users must click Save (extra step)
- Must implement unsaved changes detection and warnings
- More consistent than auto-save for sensitive settings

### ADR-P15-006: Multi-Entity via EntityEvent Junction Table

**Status:** Accepted

**Context:**
Events currently support single entity. Need to support multiple entities per event.

**Decision:**
Use existing EntityEvent junction table for many-to-many relationship. Keep `matched_entity_ids` JSON field for denormalized quick access.

**Rationale:**
- Junction table already exists from Phase 9
- Supports efficient queries in both directions (events by entity, entities by event)
- JSON field provides fast read access without joins
- Backward compatible with single-entity events

**Consequences:**
- Must keep JSON field in sync with junction table
- Entity assignment updates both

### ADR-P15-007: Provider-Specific Bounding Box Support

**Status:** Accepted

**Context:**
AI visual annotations require bounding box coordinates from AI providers.

**Decision:**
Request bounding boxes from providers that support them natively (GPT-4o, Gemini). Others return null.

**Rationale:**
- GPT-4o and Gemini have native object detection with bounding boxes
- Claude requires complex prompt engineering for coordinates (unreliable)
- xAI Grok doesn't support bounding boxes
- Graceful degradation: events without boxes still have descriptions

**Consequences:**
- Annotations only available for subset of providers
- Frontend must handle has_annotations=false gracefully
- Consider: Could use separate object detection model in future

---

## Phase 15 Epic to Architecture Mapping

| Epic | Primary Architecture Components |
|------|--------------------------------|
| P15-1: Entity UX | `EntityDetailModal.tsx` (virtual scroll), `@tanstack/react-virtual` |
| P15-2: Auth & Users | `User` model, `Session` model, `PasswordService`, `SessionService`, `permissions.py`, RBAC middleware |
| P15-3: Settings UX | `useSettingsForm` hook, `useUnsavedChangesWarning` hook, `UnsavedIndicator` component |
| P15-4: Multi-Entity | `EntityEvent` junction table, `EventCard` multi-badge, entity assignment UI |
| P15-5: AI Annotations | `FrameAnnotationService`, `bounding_boxes` field, annotation toggle UI |

---

## Phase 15 Performance Considerations

### Authentication Performance
- Password hashing: ~250ms (bcrypt cost 12)
- JWT validation: <1ms (stateless)
- Session lookup: <5ms (indexed by token_hash)
- Middleware overhead: ~10ms per authenticated request

### Entity Modal Performance
- Virtual scrolling: Constant memory regardless of event count
- Initial render: <100ms for any list size
- Scroll performance: 60fps maintained
- Memory usage: ~50 DOM nodes vs 1000+ without virtualization

### Frame Annotation Performance
- Bounding box drawing: ~50ms per frame (Pillow)
- Storage overhead: ~30% increase for annotated frames
- Processing: Async, doesn't block event creation

### Database Indexes
New indexes for Phase 15:
- `idx_users_email` - Email lookup for login
- `idx_users_role` - Role-based queries
- `idx_sessions_user_id` - User's sessions list
- `idx_sessions_token_hash` - Token validation
- `idx_sessions_expires_at` - Cleanup query

---

## Phase 15 Validation Checklist

### Security Requirements
- [ ] Passwords hashed with bcrypt cost 12 (NFR1)
- [ ] Password reset tokens expire after 24h (NFR2)
- [ ] Session tokens use 256-bit secure random (NFR3)
- [ ] Failed logins rate-limited (NFR4)
- [ ] All auth events logged (NFR5)

### Performance Requirements
- [ ] Entity modal loads <500ms with 1000+ events (NFR7)
- [ ] Session list API responds <100ms (NFR8)
- [ ] Settings save completes <1s (NFR9)

### Functional Requirements Coverage
- [ ] FR1-FR9: User Account & Authentication
- [ ] FR10-FR16: Session Management
- [ ] FR17-FR22: Role-Based Access Control
- [ ] FR23-FR27: Entity UX Improvements
- [ ] FR28-FR32: Settings UX
- [ ] FR33-FR37: Multi-Entity Events
- [ ] FR38-FR44: AI Visual Annotations

### API Contracts
- [ ] User CRUD endpoints documented
- [ ] Session management endpoints documented
- [ ] Multi-entity event endpoints documented
- [ ] Bounding box response schema documented

### Frontend Components
- [ ] Virtual scrolling implemented for entity events
- [ ] Settings form hook created and tested
- [ ] Unsaved changes warning implemented
- [ ] Multi-entity badges on event cards
- [ ] Annotation toggle in event detail

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-12-30_
