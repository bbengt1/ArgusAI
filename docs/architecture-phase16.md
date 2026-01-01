# ArgusAI Phase 16 - Architecture Additions

**Date:** 2026-01-01
**Phase:** 16 - User Experience & Access Management
**Type:** Incremental Architecture Update

---

## Executive Summary

Phase 16 extends ArgusAI's existing architecture to support multi-user access, live camera streaming, and enhanced entity management. This document defines **additions only** - all existing architecture patterns and conventions remain unchanged.

**Key Additions:**
- User roles and permissions system
- Session tracking and management
- Live video streaming proxy
- Entity metadata update API
- Optional email invitation service

---

## 1. Database Schema Additions

### 1.1 User Model Extensions

Extend existing `users` table with new columns:

```sql
-- Add to existing users table (Alembic migration)
ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'viewer';
ALTER TABLE users ADD COLUMN email TEXT UNIQUE;
ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN invited_by TEXT REFERENCES users(id);
ALTER TABLE users ADD COLUMN invited_at TIMESTAMP;
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;

-- Role constraint
-- Valid roles: 'admin', 'operator', 'viewer'
```

**Role Definitions:**
| Role | Permissions |
|------|-------------|
| admin | Full access: user management, settings, cameras, events, entities |
| operator | Camera control, event management, entity editing, alerts |
| viewer | Read-only: view events, entities, cameras (no modifications) |

### 1.2 New Session Model

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                    -- UUID
    user_id TEXT NOT NULL,                  -- FK to users.id
    token_hash TEXT NOT NULL,               -- SHA256 of JWT token
    device_info TEXT,                       -- User-Agent parsed info
    ip_address TEXT,                        -- Client IP
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,       -- Computed field for UI
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

### 1.3 User Audit Log (Optional)

```sql
CREATE TABLE user_audit_log (
    id TEXT PRIMARY KEY,                    -- UUID
    user_id TEXT NOT NULL,                  -- Who performed action
    target_user_id TEXT,                    -- Who was affected (if applicable)
    action TEXT NOT NULL,                   -- 'create_user', 'delete_user', 'change_role', etc.
    details TEXT,                           -- JSON with action details
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_user_audit_log_user_id ON user_audit_log(user_id);
CREATE INDEX idx_user_audit_log_created_at ON user_audit_log(created_at DESC);
```

---

## 2. API Endpoints

### 2.1 User Management API

**Base path:** `/api/v1/users`

| Method | Endpoint | Role Required | Description |
|--------|----------|---------------|-------------|
| GET | `/users` | admin | List all users |
| POST | `/users` | admin | Create new user |
| GET | `/users/{id}` | admin | Get user details |
| PUT | `/users/{id}` | admin | Update user |
| DELETE | `/users/{id}` | admin | Delete user |
| POST | `/users/{id}/reset-password` | admin | Generate new temp password |
| POST | `/users/invite` | admin | Send email invitation |

**Create User Request:**
```json
{
  "username": "string",
  "email": "string (optional)",
  "role": "admin | operator | viewer",
  "send_invitation": false
}
```

**Create User Response:**
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string | null",
  "role": "string",
  "temporary_password": "string (only on create)",
  "must_change_password": true,
  "created_at": "ISO timestamp"
}
```

### 2.2 Session Management API

**Base path:** `/api/v1/auth/sessions`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sessions` | List current user's active sessions |
| DELETE | `/sessions/{id}` | Revoke specific session |
| DELETE | `/sessions` | Revoke all sessions except current |

**Session Response:**
```json
{
  "id": "uuid",
  "device_info": "Chrome on macOS",
  "ip_address": "192.168.1.100",
  "created_at": "ISO timestamp",
  "last_active_at": "ISO timestamp",
  "is_current": true
}
```

### 2.3 Live Streaming API

**Base path:** `/api/v1/protect/controllers/{controller_id}/cameras/{camera_id}`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stream` | Get live stream URL/proxy |
| GET | `/stream/snapshot` | Get current frame as JPEG |

**Stream Response:**
```json
{
  "stream_url": "wss://... or /api/v1/protect/.../stream/ws",
  "stream_type": "websocket | hls | mjpeg",
  "quality_options": ["low", "medium", "high"],
  "requires_proxy": true
}
```

**Implementation Options (to be determined during implementation):**
1. **WebSocket proxy** - Backend proxies RTSP to WebSocket
2. **HLS proxy** - Backend converts to HLS segments
3. **Direct RTSP** - Frontend uses RTSP player (limited browser support)
4. **MJPEG fallback** - Snapshot refresh at high frequency

### 2.4 Entity Update API

**Endpoint:** `PUT /api/v1/context/entities/{id}`

**Request:**
```json
{
  "name": "string (optional)",
  "entity_type": "person | vehicle | unknown (optional)",
  "is_vip": "boolean (optional)",
  "is_blocked": "boolean (optional)",
  "notes": "string (optional)"
}
```

**Response:** Updated entity object

**Validation:**
- `entity_type` must be one of: person, vehicle, unknown
- `is_vip` and `is_blocked` are mutually exclusive (warn if both true)
- `name` max length: 255 characters
- `notes` max length: 2000 characters

---

## 3. Backend Services

### 3.1 New Services

```
backend/app/services/
├── user_service.py          # User CRUD, role management
├── session_service.py       # Session tracking, revocation
├── email_service.py         # Optional SMTP for invitations
└── stream_proxy_service.py  # Live video streaming proxy
```

### 3.2 Service Specifications

**UserService:**
```python
class UserService:
    def create_user(username, email, role, created_by) -> User
    def update_user(user_id, updates) -> User
    def delete_user(user_id, deleted_by) -> bool
    def generate_temp_password() -> str  # 16 char random
    def change_role(user_id, new_role, changed_by) -> User
    def list_users(skip, limit) -> List[User]
```

**SessionService:**
```python
class SessionService:
    def create_session(user_id, token, request) -> Session
    def get_user_sessions(user_id) -> List[Session]
    def revoke_session(session_id, user_id) -> bool
    def revoke_all_except_current(user_id, current_token) -> int
    def update_last_active(token_hash) -> None
    def cleanup_expired() -> int  # Cron job
```

**StreamProxyService:**
```python
class StreamProxyService:
    async def get_stream_url(controller_id, camera_id, quality) -> StreamInfo
    async def proxy_websocket(websocket, controller_id, camera_id) -> None
    async def get_snapshot(controller_id, camera_id) -> bytes
```

### 3.3 Middleware Additions

**Role-based Authorization Middleware:**
```python
def require_role(allowed_roles: List[str]):
    """Decorator for role-based endpoint protection"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage:
@router.post("/users")
@require_role(["admin"])
async def create_user(...):
    ...
```

**Session Activity Middleware:**
```python
# Update last_active_at on each authenticated request
@app.middleware("http")
async def update_session_activity(request, call_next):
    response = await call_next(request)
    if hasattr(request.state, "token_hash"):
        await session_service.update_last_active(request.state.token_hash)
    return response
```

---

## 4. Frontend Components

### 4.1 New Components

```
frontend/components/
├── users/
│   ├── UserManagement.tsx      # Main user list/management page
│   ├── UserCreateModal.tsx     # Create user dialog
│   ├── UserEditModal.tsx       # Edit user dialog
│   └── UserRoleBadge.tsx       # Role display component
├── sessions/
│   ├── ActiveSessions.tsx      # Session list in settings
│   └── SessionCard.tsx         # Individual session display
├── streaming/
│   ├── LiveStreamPlayer.tsx    # Video player component
│   ├── LiveStreamModal.tsx     # Fullscreen stream modal
│   └── StreamQualitySelector.tsx
└── entities/
    ├── EntityEditModal.tsx     # Edit entity properties
    └── EntityAssignConfirm.tsx # Re-classification warning dialog
```

### 4.2 Component Specifications

**LiveStreamPlayer Props:**
```typescript
interface LiveStreamPlayerProps {
  controllerId: string;
  cameraId: string;
  quality?: 'low' | 'medium' | 'high';
  autoPlay?: boolean;
  muted?: boolean;
  onError?: (error: Error) => void;
  onStreamStart?: () => void;
}
```

**EntityEditModal Props:**
```typescript
interface EntityEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  entity: IEntity;
  onSave: (updates: Partial<IEntity>) => Promise<void>;
}
```

### 4.3 New Hooks

```typescript
// frontend/hooks/useUsers.ts
export function useUsers(): UseQueryResult<User[]>;
export function useCreateUser(): UseMutationResult<User, Error, CreateUserInput>;
export function useUpdateUser(): UseMutationResult<User, Error, UpdateUserInput>;
export function useDeleteUser(): UseMutationResult<void, Error, string>;

// frontend/hooks/useSessions.ts
export function useSessions(): UseQueryResult<Session[]>;
export function useRevokeSession(): UseMutationResult<void, Error, string>;
export function useRevokeAllSessions(): UseMutationResult<number, Error, void>;

// frontend/hooks/useEntityMutations.ts
export function useUpdateEntity(): UseMutationResult<IEntity, Error, UpdateEntityInput>;
```

---

## 5. Security Considerations

### 5.1 Authentication Flow Updates

```
Current: username/password → JWT → stored in httpOnly cookie
Phase 16 Addition: JWT creation → create Session record → track activity
```

### 5.2 Password Requirements

- Temporary passwords: 16 characters, cryptographically random
- Must change on first login if `must_change_password = true`
- Bcrypt cost factor: 12 (existing standard)

### 5.3 Session Security

- Session tokens stored as SHA256 hash (never store raw JWT)
- Sessions expire after 7 days of inactivity (configurable)
- Password change invalidates all sessions except current
- Maximum 10 concurrent sessions per user (configurable)

### 5.4 Role Enforcement

- All protected endpoints must check role
- Admin-only endpoints: user management, system settings
- Operator endpoints: camera control, event management, entity editing
- Viewer endpoints: read-only access to all data

---

## 6. Configuration Additions

### 6.1 New Environment Variables

```bash
# Email (Optional - for invitations)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=<encrypted>
SMTP_FROM_NAME=ArgusAI
SMTP_ENABLED=false

# Session Settings
SESSION_MAX_AGE_DAYS=7
SESSION_MAX_PER_USER=10

# Streaming Settings
STREAM_PROXY_ENABLED=true
STREAM_MAX_CONCURRENT=10
STREAM_DEFAULT_QUALITY=medium
```

### 6.2 Settings Schema Additions

```python
# Add to existing settings model
class SystemSettings(BaseModel):
    # ... existing fields ...

    # Phase 16 additions
    session_max_age_days: int = 7
    session_max_per_user: int = 10
    smtp_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    stream_max_concurrent: int = 10
```

---

## 7. Migration Strategy

### 7.1 Database Migrations

```
migrations/
├── versions/
│   ├── xxxx_add_user_role_columns.py      # Extend users table
│   ├── xxxx_create_sessions_table.py      # New sessions table
│   └── xxxx_create_audit_log_table.py     # New audit log table
```

### 7.2 Migration Order

1. Add columns to users table (role, email, must_change_password)
2. Set existing users to role='admin' (preserve access)
3. Create sessions table
4. Create audit log table (optional)

### 7.3 Backward Compatibility

- Existing admin user retains full access
- No breaking changes to existing API endpoints
- New endpoints added alongside existing ones

---

## 8. Epic to Architecture Mapping

| Epic | Primary Components | Database Changes | New Endpoints |
|------|-------------------|------------------|---------------|
| P16-1: User Management | UserService, UserManagement.tsx | users table extensions | /api/v1/users/* |
| P16-2: Live Streaming | StreamProxyService, LiveStreamPlayer.tsx | None | /api/v1/protect/.../stream |
| P16-3: Entity Editing | EntityEditModal.tsx | None | PUT /api/v1/context/entities/{id} |
| P16-4: Assignment UX | EntityAssignConfirm.tsx | None | None (frontend only) |
| P16-5: Active Sessions | SessionService, ActiveSessions.tsx | sessions table | /api/v1/auth/sessions |
| P16-6: Multi-Entity | (Research needed) | Possible events table change | TBD |

---

## 9. Implementation Patterns

### 9.1 Naming Conventions (Unchanged)

- Tables: snake_case plural (users, sessions)
- Columns: snake_case (user_id, created_at)
- API endpoints: kebab-case (/api/v1/auth/sessions)
- Components: PascalCase (UserManagement.tsx)
- Hooks: camelCase with use prefix (useUsers)

### 9.2 Error Response Format (Unchanged)

```json
{
  "detail": "Error message",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "field": "role"  // Optional, for validation errors
}
```

### 9.3 New Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INSUFFICIENT_PERMISSIONS | 403 | User lacks required role |
| SESSION_EXPIRED | 401 | Session no longer valid |
| SESSION_LIMIT_EXCEEDED | 400 | Too many active sessions |
| USER_DISABLED | 403 | Account is disabled |
| PASSWORD_CHANGE_REQUIRED | 403 | Must change temp password |
| STREAM_UNAVAILABLE | 503 | Camera stream not available |
| STREAM_LIMIT_EXCEEDED | 429 | Too many concurrent streams |

---

## 10. Testing Requirements

### 10.1 New Test Files

```
backend/tests/
├── test_services/
│   ├── test_user_service.py
│   ├── test_session_service.py
│   └── test_stream_proxy_service.py
├── test_api/
│   ├── test_users_api.py
│   ├── test_sessions_api.py
│   └── test_streaming_api.py
└── test_middleware/
    └── test_role_authorization.py

frontend/__tests__/
├── components/
│   ├── UserManagement.test.tsx
│   ├── ActiveSessions.test.tsx
│   ├── LiveStreamPlayer.test.tsx
│   └── EntityEditModal.test.tsx
└── hooks/
    ├── useUsers.test.ts
    └── useSessions.test.ts
```

### 10.2 Test Coverage Targets

- New backend services: 80%+ coverage
- New API endpoints: 90%+ coverage (including auth/role tests)
- New frontend components: 70%+ coverage

---

## 11. Open Questions for Implementation

1. **Live Streaming Protocol:** WebSocket proxy vs HLS vs MJPEG? (Recommend WebSocket for lowest latency, MJPEG as fallback)

2. **Multi-Entity Events (Epic P16-6):**
   - Change `matched_entity_ids` from JSON string to proper junction table?
   - Or keep JSON for backward compatibility?

3. **Email Service:**
   - Required or optional?
   - If optional, how to deliver temp passwords without email?

---

## References

- Existing Architecture: `docs/architecture/`
- Phase 16 PRD: `docs/PRD-phase16.md`
- User Model: `backend/app/models/user.py`
- Auth Service: `backend/app/services/auth_service.py`

---

_This document extends the existing ArgusAI architecture for Phase 16. All patterns and conventions from the base architecture apply unless explicitly overridden here._
