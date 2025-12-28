# Epic Technical Specification: API Key Management

**Epic ID:** P13-1
**Phase:** 13 - Platform Maturity & External Integration
**Priority:** P2
**Generated:** 2025-12-28
**PRD Reference:** docs/PRD-phase13.md
**Epic Reference:** docs/epics-phase13.md

---

## Executive Summary

This epic implements a complete API key management system enabling secure programmatic access to ArgusAI for third-party integrations, automation scripts, and external dashboards. API keys provide an alternative authentication mechanism to JWT tokens, specifically designed for machine-to-machine communication.

**Functional Requirements Coverage:** FR1-FR10 (10 requirements)

---

## Architecture Overview

### High-Level Design

```
External Client          ArgusAI Backend               Database
     │                        │                           │
     │  Authorization: Bearer argus_xxxx...               │
     │─────────────────────────►                          │
     │                        │                           │
     │               ┌────────┴────────┐                  │
     │               │ API Key Middleware                 │
     │               │ - Extract key from header          │
     │               │ - Hash and lookup                  │
     │               │ - Validate scope/expiry            │
     │               │ - Check rate limit                 │
     │               └────────┬────────┘                  │
     │                        │                           │
     │                        │  SELECT by prefix+hash    │
     │                        │────────────────────────────►
     │                        │                           │
     │                        │  Update last_used_at      │
     │                        │────────────────────────────►
     │                        │                           │
     │                ┌───────┴───────┐                   │
     │                │ Route Handler  │                   │
     │                │ (with scopes)  │                   │
     │                └───────┬───────┘                   │
     │                        │                           │
     │◄────────────────────────                           │
     │  Response                                          │
```

### Component Architecture

```
backend/app/
├── models/
│   └── api_key.py              # NEW: APIKey model
├── schemas/
│   └── api_key.py              # NEW: Request/Response schemas
├── api/v1/
│   └── api_keys.py             # NEW: API key management endpoints
├── core/
│   └── security.py             # MODIFY: Add API key auth
├── middleware/
│   └── api_key_auth.py         # NEW: API key middleware
└── services/
    └── api_key_service.py      # NEW: API key business logic
```

---

## Story Specifications

### Story P13-1.1: Create APIKey Database Model and Migration

**Acceptance Criteria:**
- AC-1.1.1: Given the migration runs, when I check the database, then `api_keys` table exists with all required columns
- AC-1.1.2: Given an API key is created, when hashing is applied, then only the bcrypt hash is stored (plaintext never stored)
- AC-1.1.3: Given an API key prefix, when querying, then I can identify the key without revealing the full key

**Technical Specification:**

```python
# backend/app/models/api_key.py
from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class APIKey(Base):
    """
    API Key model for external integrations.

    Security: The full key is never stored. Only the prefix (first 8 chars)
    and bcrypt hash are stored. Key displayed once at creation only.
    """
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)  # Descriptive name
    prefix = Column(String(8), nullable=False, index=True)  # First 8 chars for identification
    key_hash = Column(String(255), nullable=False)  # bcrypt hash of full key

    # Scopes as JSON array: ["read:events", "read:cameras", "write:cameras", "admin"]
    scopes = Column(JSON, nullable=False, default=list)

    # Status and lifecycle
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration

    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    last_used_ip = Column(String(45), nullable=True)  # IPv6 compatible
    usage_count = Column(Integer, default=0, nullable=False)

    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=100, nullable=False)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(36), nullable=True)  # User ID who created
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(String(36), nullable=True)  # User ID who revoked
```

**Migration:**
```python
# alembic/versions/xxx_add_api_keys_table.py
def upgrade():
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('prefix', sa.String(8), nullable=False, index=True),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('scopes', sa.JSON, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_ip', sa.String(45), nullable=True),
        sa.Column('usage_count', sa.Integer, default=0, nullable=False),
        sa.Column('rate_limit_per_minute', sa.Integer, default=100, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(36), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_api_keys_prefix', 'api_keys', ['prefix'])
```

**Files to Create/Modify:**
- `backend/app/models/api_key.py` (NEW)
- `backend/app/models/__init__.py` (MODIFY: add import)
- `backend/alembic/versions/xxx_add_api_keys_table.py` (NEW)

---

### Story P13-1.2: Implement API Key Generation Endpoint

**Acceptance Criteria:**
- AC-1.2.1: Given valid admin credentials, when creating an API key, then a 32-character key prefixed with "argus_" is returned
- AC-1.2.2: Given a key is created, when the response is returned, then the full key is displayed ONLY in this response (never again)
- AC-1.2.3: Given scopes are specified, when the key is created, then only those scopes are stored with the key

**Technical Specification:**

```python
# backend/app/services/api_key_service.py
import secrets
import bcrypt
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.api_key import APIKey

class APIKeyService:
    """Service for API key management operations."""

    KEY_PREFIX = "argus_"
    KEY_LENGTH = 32  # Excluding prefix

    def generate_api_key(
        self,
        db: Session,
        name: str,
        scopes: list[str],
        created_by: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        rate_limit_per_minute: int = 100,
    ) -> tuple[APIKey, str]:
        """
        Generate a new API key.

        Returns:
            Tuple of (APIKey model, plaintext_key)
            The plaintext_key is ONLY returned here and never stored.
        """
        # Generate cryptographically secure random key
        random_part = secrets.token_urlsafe(self.KEY_LENGTH)
        plaintext_key = f"{self.KEY_PREFIX}{random_part}"

        # Extract prefix for identification (first 8 chars after argus_)
        prefix = random_part[:8]

        # Hash the full key with bcrypt
        key_hash = bcrypt.hashpw(
            plaintext_key.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')

        api_key = APIKey(
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            scopes=scopes,
            created_by=created_by,
            expires_at=expires_at,
            rate_limit_per_minute=rate_limit_per_minute,
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        return api_key, plaintext_key
```

**API Endpoint:**
```python
# backend/app/api/v1/api_keys.py
@router.post(
    "/",
    response_model=APIKeyCreateResponse,
    status_code=201,
    summary="Create new API key",
)
async def create_api_key(
    request: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new API key. Returns the key ONLY ONCE.

    Requires admin authentication.
    """
    # Validate scopes
    valid_scopes = {"read:events", "read:cameras", "write:cameras", "admin"}
    if not set(request.scopes).issubset(valid_scopes):
        raise HTTPException(400, "Invalid scope specified")

    api_key, plaintext_key = api_key_service.generate_api_key(
        db=db,
        name=request.name,
        scopes=request.scopes,
        created_by=current_user.id,
        expires_at=request.expires_at,
    )

    return APIKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=plaintext_key,  # Only time the full key is returned
        prefix=api_key.prefix,
        scopes=api_key.scopes,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )
```

**Files to Create/Modify:**
- `backend/app/services/api_key_service.py` (NEW)
- `backend/app/api/v1/api_keys.py` (NEW)
- `backend/app/schemas/api_key.py` (NEW)
- `backend/app/api/v1/__init__.py` (MODIFY: add router)

---

### Story P13-1.3: Implement API Key List and Revoke Endpoints

**Acceptance Criteria:**
- AC-1.3.1: Given admin credentials, when listing keys, then all keys are returned with prefix, name, created date, last used, and status (no full key)
- AC-1.3.2: Given a valid key ID, when revoking, then the key is immediately marked as revoked
- AC-1.3.3: Given a revoked key, when listed, then it shows as revoked with revocation timestamp

**Technical Specification:**

```python
# backend/app/api/v1/api_keys.py
@router.get("/", response_model=list[APIKeyListResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all API keys (without exposing the key itself)."""
    keys = db.query(APIKey).order_by(APIKey.created_at.desc()).all()
    return [
        APIKeyListResponse(
            id=key.id,
            name=key.name,
            prefix=f"argus_{key.prefix}...",  # Show partial for identification
            scopes=key.scopes,
            is_active=key.is_active,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            created_at=key.created_at,
            revoked_at=key.revoked_at,
        )
        for key in keys
    ]

@router.delete("/{key_id}", response_model=MessageResponse)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke an API key immediately."""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(404, "API key not found")

    api_key.is_active = False
    api_key.revoked_at = datetime.now(timezone.utc)
    api_key.revoked_by = current_user.id
    db.commit()

    return MessageResponse(message="API key revoked successfully")
```

**Files to Modify:**
- `backend/app/api/v1/api_keys.py` (MODIFY)
- `backend/app/schemas/api_key.py` (MODIFY)

---

### Story P13-1.4: Implement API Key Authentication Middleware

**Acceptance Criteria:**
- AC-1.4.1: Given a request with `Authorization: Bearer argus_xxx`, when the key is valid, then the request proceeds with scope context
- AC-1.4.2: Given an expired or revoked key, when authenticating, then 401 Unauthorized is returned
- AC-1.4.3: Given a key without required scope, when accessing protected endpoint, then 403 Forbidden is returned

**Technical Specification:**

```python
# backend/app/middleware/api_key_auth.py
import bcrypt
from datetime import datetime, timezone
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from app.models.api_key import APIKey

class APIKeyAuth:
    """API Key authentication handler."""

    async def authenticate(
        self,
        request: Request,
        db: Session,
    ) -> tuple[bool, APIKey | None]:
        """
        Authenticate request via API key.

        Returns:
            Tuple of (is_api_key_auth, api_key_model)
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer argus_"):
            return False, None

        plaintext_key = auth_header[7:]  # Remove "Bearer "

        # Extract prefix for initial lookup
        if not plaintext_key.startswith("argus_"):
            return False, None

        prefix = plaintext_key[6:14]  # 8 chars after "argus_"

        # Find potential matches by prefix
        potential_keys = db.query(APIKey).filter(
            APIKey.prefix == prefix,
            APIKey.is_active == True,
        ).all()

        # Verify hash against each potential match
        for api_key in potential_keys:
            if bcrypt.checkpw(
                plaintext_key.encode('utf-8'),
                api_key.key_hash.encode('utf-8')
            ):
                # Check expiration
                if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
                    raise HTTPException(401, "API key expired")

                # Update usage tracking
                api_key.last_used_at = datetime.now(timezone.utc)
                api_key.last_used_ip = request.client.host if request.client else None
                api_key.usage_count += 1
                db.commit()

                return True, api_key

        return False, None

def require_scope(scope: str):
    """Decorator to require specific API key scope."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            api_key = getattr(request.state, 'api_key', None)

            if api_key and scope not in api_key.scopes and "admin" not in api_key.scopes:
                raise HTTPException(403, f"Scope '{scope}' required")

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Integration with existing auth:**
```python
# backend/app/api/v1/auth.py - MODIFY get_current_user
async def get_current_user_or_api_key(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Unified auth dependency supporting both JWT and API keys.
    """
    # Try API key first
    is_api_key, api_key = await api_key_auth.authenticate(request, db)
    if is_api_key and api_key:
        request.state.api_key = api_key
        request.state.auth_type = "api_key"
        return api_key  # Return API key for scope checking

    # Fall back to JWT auth
    return await get_current_user(request, db)
```

**Files to Create/Modify:**
- `backend/app/middleware/api_key_auth.py` (NEW)
- `backend/app/api/v1/auth.py` (MODIFY)

---

### Story P13-1.5: Implement API Key Rate Limiting

**Acceptance Criteria:**
- AC-1.5.1: Given a key with 100 req/min limit, when 101st request is made within a minute, then 429 Too Many Requests is returned
- AC-1.5.2: Given rate limit exceeded, when response is returned, then Retry-After header is included
- AC-1.5.3: Given different keys, when rate limits are checked, then each key has independent limits

**Technical Specification:**

```python
# backend/app/middleware/api_key_rate_limiter.py
from datetime import datetime, timezone
from collections import defaultdict
import asyncio

class APIKeyRateLimiter:
    """In-memory rate limiter for API keys."""

    def __init__(self):
        self._requests: dict[str, list[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        api_key_id: str,
        limit_per_minute: int,
    ) -> tuple[bool, int]:
        """
        Check if request is within rate limit.

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            window_start = now.timestamp() - 60

            # Clean old requests
            self._requests[api_key_id] = [
                ts for ts in self._requests[api_key_id]
                if ts.timestamp() > window_start
            ]

            if len(self._requests[api_key_id]) >= limit_per_minute:
                oldest = min(self._requests[api_key_id])
                retry_after = int(60 - (now.timestamp() - oldest.timestamp()))
                return False, max(retry_after, 1)

            self._requests[api_key_id].append(now)
            return True, 0

# Middleware integration
@app.middleware("http")
async def api_key_rate_limit_middleware(request: Request, call_next):
    api_key = getattr(request.state, 'api_key', None)

    if api_key:
        allowed, retry_after = await rate_limiter.check_rate_limit(
            api_key.id,
            api_key.rate_limit_per_minute,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

    return await call_next(request)
```

**Files to Create:**
- `backend/app/middleware/api_key_rate_limiter.py` (NEW)
- `backend/main.py` (MODIFY: add middleware)

---

### Story P13-1.6: Create API Keys Settings UI

**Acceptance Criteria:**
- AC-1.6.1: Given the Settings page, when navigating to API Keys tab, then a list of existing keys is displayed
- AC-1.6.2: Given the create dialog, when submitting valid data, then the new key is shown ONCE with copy button
- AC-1.6.3: Given a key in the list, when clicking revoke, then confirmation dialog appears and key is revoked on confirm

**Technical Specification:**

```typescript
// frontend/components/settings/APIKeysSection.tsx
interface APIKey {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  usage_count: number;
  created_at: string;
  revoked_at: string | null;
}

export function APIKeysSection() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);

  // ... implementation
}

// Create dialog with one-time key display
function CreateAPIKeyDialog({ onKeyCreated }) {
  const [name, setName] = useState('');
  const [scopes, setScopes] = useState<string[]>(['read:events']);
  const [createdKey, setCreatedKey] = useState<string | null>(null);

  // Show key only once after creation with copy button
  // Warning: This key will not be shown again
}
```

**Files to Create:**
- `frontend/components/settings/APIKeysSection.tsx` (NEW)
- `frontend/app/settings/api-keys/page.tsx` (NEW)

---

## API Contracts

### Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/api-keys` | Create new API key | Admin JWT |
| GET | `/api/v1/api-keys` | List all API keys | Admin JWT |
| DELETE | `/api/v1/api-keys/{id}` | Revoke API key | Admin JWT |
| GET | `/api/v1/api-keys/{id}/usage` | Get usage stats | Admin JWT |

### Request/Response Schemas

```python
# backend/app/schemas/api_key.py
class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] = Field(default=["read:events"])
    expires_at: Optional[datetime] = None

class APIKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str  # Full key - ONLY returned here
    prefix: str
    scopes: list[str]
    expires_at: Optional[datetime]
    created_at: datetime

class APIKeyListResponse(BaseModel):
    id: str
    name: str
    prefix: str  # Partial key for identification
    scopes: list[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime
    revoked_at: Optional[datetime]
```

---

## Security Considerations

### NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR1 | Keys hashed with bcrypt/Argon2 | bcrypt with 12 rounds |
| NFR3 | Admin auth required | `get_current_user` dependency |
| NFR4 | Rate limiting (100 req/min) | In-memory rate limiter |
| NFR7 | 90-day audit log retention | Usage tracking in DB |
| NFR8 | <10ms auth latency | Prefix-based lookup + bcrypt |

### Key Security

1. **Key Format:** `argus_` prefix + 32-char random (44 chars total)
2. **Storage:** Only bcrypt hash stored, never plaintext
3. **Display:** Full key shown ONLY at creation time
4. **Revocation:** Immediate effect (no caching)

---

## Testing Strategy

### Unit Tests
- APIKeyService.generate_api_key() generates valid keys
- bcrypt hash verification works correctly
- Scope validation rejects invalid scopes
- Rate limiter correctly tracks and limits requests

### Integration Tests
- Full key creation flow with database
- Key authentication middleware
- Rate limiting across multiple requests
- Revocation immediately blocks access

### Security Tests
- Verify keys cannot be retrieved after creation
- Verify expired keys are rejected
- Verify revoked keys are rejected
- Verify scope enforcement works

---

## Dependencies

### Python Packages
- `bcrypt>=4.0.0` (already in project)
- No new dependencies required

### Frontend Packages
- No new dependencies required

---

## Migration Notes

- Migration is additive (new table only)
- No existing data modifications required
- Rollback: Simply drop `api_keys` table
