# Epic Technical Specification: Mobile Device Registration

Date: 2025-12-26
Author: Brent
Epic ID: P12-2
Status: Draft

---

## Overview

Epic P12-2 extends the Phase 11 Device model with mobile-specific registration capabilities, implementing device CRUD endpoints and a management UI. This establishes the foundation for Epic P12-3's authentication and pairing flow by providing proper device lifecycle tracking.

**PRD Reference:** docs/PRD-phase12.md (FRs 9-17, 39-42)
**Architecture:** docs/architecture/phase-12-additions.md

## Objectives and Scope

**In Scope:**
- Extend Device model with `pairing_confirmed`, `device_model` fields
- Implement device CRUD endpoints (POST/GET/PUT/DELETE /api/v1/devices)
- Build DeviceManager UI component in Settings
- Associate push tokens with device records
- Implement device lifecycle tracking (last_seen_at, inactive warning)
- Add bulk cleanup for inactive devices

**Out of Scope:**
- Pairing code flow (Epic P12-3)
- Token management (Epic P12-3)
- Push notification delivery (Phase 11)

## System Architecture Alignment

**Components Affected:**
- `backend/app/models/device.py` - Extend with pairing_confirmed, device_model
- `backend/app/api/v1/devices.py` - Device CRUD router
- `backend/app/services/device_service.py` - Device business logic
- `backend/app/middleware/last_seen.py` - Update last_seen on requests
- `frontend/components/settings/DeviceManager.tsx` - Device list UI

**Architecture Constraints:**
- Must maintain backward compatibility with Phase 11 Device model
- Device operations must complete in <200ms
- Support up to 10 devices per user, 100 per instance

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs |
|--------|----------------|--------|---------|
| Device Model | Store device registration | - | Device fields |
| DeviceService | CRUD operations, lifecycle | DeviceCreate/Update | Device |
| DeviceRouter | HTTP endpoints | HTTP requests | JSON responses |
| LastSeenMiddleware | Track device activity | Request with device_id | Updated timestamp |
| DeviceManager | UI for device management | User interaction | Device list display |

### Data Models and Contracts

**Device Model Extension:**

```python
# backend/app/models/device.py

class Device(Base):
    """
    Mobile device registration for push notifications and auth.

    Extended in P12-2 from Phase 11 base.
    """
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    device_id = Column(String(255), nullable=False, unique=True)  # Hardware ID
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    platform = Column(String(20), nullable=False)  # ios, android, web
    name = Column(String(100), nullable=True)  # User-friendly name
    push_token = Column(Text, nullable=True)  # Encrypted FCM/APNS token

    # P12-2 additions
    device_model = Column(String(100), nullable=True)  # "iPhone 15 Pro", "Pixel 8"
    pairing_confirmed = Column(Boolean, default=False)  # True after pairing flow

    # Lifecycle tracking
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="devices")
    refresh_tokens = relationship("RefreshToken", back_populates="device", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_devices_user_id', 'user_id'),
        Index('idx_devices_platform', 'platform'),
        Index('idx_devices_last_seen', 'last_seen_at'),
    )

    @property
    def is_inactive(self) -> bool:
        """Device inactive if not seen in 90+ days."""
        if not self.last_seen_at:
            return True
        return (datetime.now(timezone.utc) - self.last_seen_at).days > 90
```

**Migration:**

```python
# alembic/versions/xxxx_extend_device_model.py

def upgrade():
    op.add_column('devices', sa.Column('device_model', sa.String(100), nullable=True))
    op.add_column('devices', sa.Column('pairing_confirmed', sa.Boolean(), server_default='false'))
    op.create_index('idx_devices_last_seen', 'devices', ['last_seen_at'])

def downgrade():
    op.drop_index('idx_devices_last_seen', 'devices')
    op.drop_column('devices', 'pairing_confirmed')
    op.drop_column('devices', 'device_model')
```

**Pydantic Schemas:**

```python
# backend/app/schemas/device.py

class DeviceCreate(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)
    platform: Literal['ios', 'android', 'web']
    name: Optional[str] = Field(None, max_length=100)
    device_model: Optional[str] = Field(None, max_length=100)
    push_token: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    push_token: Optional[str] = None

class DeviceResponse(BaseModel):
    id: str
    device_id: str
    platform: str
    name: Optional[str]
    device_model: Optional[str]
    pairing_confirmed: bool
    last_seen_at: Optional[datetime]
    created_at: datetime
    inactive_warning: bool = False

    class Config:
        from_attributes = True

    @validator('inactive_warning', pre=True, always=True)
    def check_inactive(cls, v, values):
        last_seen = values.get('last_seen_at')
        if not last_seen:
            return True
        return (datetime.now(timezone.utc) - last_seen).days > 90
```

### APIs and Interfaces

```yaml
POST /api/v1/devices:
  summary: Register a new device
  security:
    - bearerAuth: []
  requestBody:
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/DeviceCreate'
  responses:
    201:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/DeviceResponse'
    409:
      description: Device already registered

GET /api/v1/devices:
  summary: List user's registered devices
  security:
    - bearerAuth: []
  responses:
    200:
      content:
        application/json:
          schema:
            type: object
            properties:
              devices:
                type: array
                items:
                  $ref: '#/components/schemas/DeviceResponse'
              total:
                type: integer

PUT /api/v1/devices/{id}:
  summary: Update device (rename)
  security:
    - bearerAuth: []
  parameters:
    - name: id
      in: path
      required: true
  requestBody:
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/DeviceUpdate'
  responses:
    200:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/DeviceResponse'

DELETE /api/v1/devices/{id}:
  summary: Revoke device registration
  security:
    - bearerAuth: []
  responses:
    204:
      description: Device deleted
    404:
      description: Device not found

DELETE /api/v1/devices/inactive:
  summary: Remove all inactive devices (90+ days)
  security:
    - bearerAuth: []
  responses:
    200:
      content:
        application/json:
          schema:
            type: object
            properties:
              removed_count:
                type: integer
```

**Implementation:**

```python
# backend/app/api/v1/devices.py

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("", response_model=DeviceResponse, status_code=201)
async def register_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new device for the current user."""
    service = DeviceService(db)
    device = await service.create_device(current_user.id, device_data)
    return device

@router.get("", response_model=dict)
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all devices for current user."""
    devices = db.query(Device).filter(Device.user_id == current_user.id).all()
    return {
        "devices": [DeviceResponse.from_orm(d) for d in devices],
        "total": len(devices)
    }

@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update device name or push token."""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device_data.name is not None:
        device.name = device_data.name
    if device_data.push_token is not None:
        device.push_token = encrypt_token(device_data.push_token)

    db.commit()
    db.refresh(device)
    return device

@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete device and revoke all tokens."""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.user_id == current_user.id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Cascade delete handles refresh_tokens
    db.delete(device)
    db.commit()
    return None
```

### Workflows and Sequencing

**Device Registration Flow:**

```
Mobile App                 ArgusAI Backend
    │                           │
    │  POST /devices            │
    │  {device_id, platform,    │
    │   name, device_model}     │
    │──────────────────────────►│
    │                           │
    │                           │─► Validate device_id unique
    │                           │─► Check user device limit (10)
    │                           │─► Create Device record
    │                           │─► pairing_confirmed = false
    │                           │
    │  {id, device_id, ...}     │
    │◄──────────────────────────│
```

**Last Seen Update Middleware:**

```python
# backend/app/middleware/last_seen.py

class LastSeenMiddleware:
    """Update device last_seen_at on authenticated requests."""

    async def __call__(self, request: Request, call_next):
        response = await call_next(request)

        # Update last_seen if device_id in token
        if hasattr(request.state, 'device_id'):
            device_id = request.state.device_id
            await self._update_last_seen(device_id)

        return response

    async def _update_last_seen(self, device_id: str):
        """Async update with debouncing (max once per minute)."""
        cache_key = f"device_seen:{device_id}"
        if not await cache.exists(cache_key):
            await db.execute(
                update(Device)
                .where(Device.id == device_id)
                .values(last_seen_at=datetime.now(timezone.utc))
            )
            await cache.set(cache_key, "1", ex=60)  # 1 minute debounce
```

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Device registration | <200ms | API response time |
| Device list | <100ms | Query with index |
| Last seen update | <5ms | Debounced, async |

### Security

- Push tokens stored encrypted (Fernet)
- Device deletion cascades to revoke all refresh tokens
- User can only access own devices (user_id filter)

### Reliability/Availability

- Device limit enforced (10 per user) to prevent abuse
- Cascade delete ensures no orphaned tokens
- Inactive device cleanup prevents data bloat

### Observability

- Log device registrations with user_id, platform
- Metric: `devices_registered_total{platform}` counter
- Alert on >100 devices per instance

## Dependencies and Integrations

**Backend Dependencies (existing):**
```
sqlalchemy>=2.0.0
cryptography  # For token encryption
```

**Integration Points:**
- User model (relationship)
- RefreshToken model (P12-3, cascade relationship)
- PushDispatchService (Phase 11, queries by device)

## Acceptance Criteria (Authoritative)

1. **AC1:** POST /api/v1/devices creates device with all fields stored correctly
2. **AC2:** Device registration captures platform, name, device_model, device_id
3. **AC3:** GET /api/v1/devices returns all user's devices with inactive_warning flag
4. **AC4:** PUT /api/v1/devices/{id} allows renaming device
5. **AC5:** DELETE /api/v1/devices/{id} removes device and revokes all tokens
6. **AC6:** Push tokens are encrypted before storage
7. **AC7:** last_seen_at updates on authenticated API requests
8. **AC8:** Devices inactive 90+ days show inactive_warning=true
9. **AC9:** DELETE /api/v1/devices/inactive removes all inactive devices
10. **AC10:** Device operations complete in <200ms

## Traceability Mapping

| AC | Spec Section | Component/API | Test Idea |
|----|--------------|---------------|-----------|
| AC1 | APIs | POST /devices | Create device, verify fields |
| AC2 | Data Models | DeviceCreate schema | Schema validation test |
| AC3 | APIs | GET /devices | List with inactive device |
| AC4 | APIs | PUT /devices/{id} | Rename, verify update |
| AC5 | APIs, Workflows | DELETE /devices/{id} | Delete, verify tokens revoked |
| AC6 | Data Models | Device.push_token | Verify encryption |
| AC7 | Workflows | LastSeenMiddleware | Make request, check timestamp |
| AC8 | Data Models | DeviceResponse.inactive_warning | 91-day-old device |
| AC9 | APIs | DELETE /devices/inactive | Bulk cleanup test |
| AC10 | Performance | All endpoints | Response time <200ms |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1:** High device registration rate could hit limits
  - *Mitigation:* 10 device limit per user, clear messaging

**Assumptions:**
- **A1:** Phase 11 Device model exists with basic fields
- **A2:** Push token encryption uses existing Fernet key

**Open Questions:**
- **Q1:** Should device_id be editable? (Suggested: No, hardware ID)
- **Q2:** Should inactive cleanup be automatic via cron? (Suggested: Manual for now)

## Test Strategy Summary

**Unit Tests:**
- `test_device_create` - All fields stored correctly
- `test_device_inactive_warning` - 90+ day calculation
- `test_push_token_encryption` - Token encrypted/decrypted

**Integration Tests:**
- `test_device_crud_endpoints` - Full CRUD flow
- `test_device_delete_cascades_tokens` - Token revocation
- `test_last_seen_update` - Middleware updates timestamp

**Frontend Tests:**
- `DeviceManager.test.tsx` - List renders, actions work

---

**Created:** 2025-12-26
**Stories:** P12-2.1, P12-2.2, P12-2.3, P12-2.4, P12-2.5
