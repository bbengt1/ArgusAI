# Epic Technical Specification: Mobile Authentication & Pairing

Date: 2025-12-26
Author: Brent
Epic ID: P12-3
Status: Draft

---

## Overview

Epic P12-3 implements secure device pairing using 6-digit codes and JWT token management with refresh token rotation. This enables future native mobile apps to authenticate securely without exposing credentials, using a human-in-the-loop verification flow via the web dashboard.

**PRD Reference:** docs/PRD-phase12.md (FRs 18-28, 43-45)
**Architecture:** docs/architecture/phase-12-additions.md

## Objectives and Scope

**In Scope:**
- Create PairingCode and RefreshToken models
- Implement 6-digit pairing code generation with 5-minute expiry
- Build pairing confirmation UI in Settings > Devices
- Implement token exchange (code → JWT)
- Implement token refresh with rotation
- Rate limiting for pairing attempts (5/minute)
- Token revocation on password change

**Out of Scope:**
- Device registration (Epic P12-2 - prerequisite)
- Push notification delivery (Phase 11)
- OAuth/social login (future)

## System Architecture Alignment

**Components Affected:**
- `backend/app/models/pairing_code.py` - New model
- `backend/app/models/refresh_token.py` - New model
- `backend/app/services/mobile/pairing_service.py` - Pairing logic
- `backend/app/services/mobile/token_service.py` - JWT management
- `backend/app/api/v1/mobile_auth.py` - Pairing endpoints
- `frontend/components/settings/PairingConfirmation.tsx` - Confirmation UI

**Dependencies:**
- **Requires P12-2:** Device model must exist for token association

**Architecture Constraints:**
- Pairing codes must be cryptographically random
- Refresh tokens stored hashed (SHA-256), never plaintext
- Token refresh must complete in <100ms
- Must support concurrent token refresh (grace period)

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs |
|--------|----------------|--------|---------|
| PairingCode Model | Store temporary codes | - | code, device_id, expires_at |
| RefreshToken Model | Store hashed tokens | - | token_hash, device_id |
| PairingService | Code generation/verification | device_id, code | PairingCode, TokenPair |
| TokenService | JWT creation/refresh | Device, refresh_token | TokenPair |
| MobileAuthRouter | HTTP endpoints | HTTP requests | JSON responses |
| PairingConfirmation | UI for code entry | User input | Confirmation |

### Data Models and Contracts

**PairingCode Model:**

```python
# backend/app/models/pairing_code.py

class PairingCode(Base):
    """
    Temporary pairing codes for mobile device authentication.

    Codes expire after 5 minutes and are deleted after use.
    """
    __tablename__ = "pairing_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(6), unique=True, nullable=False)
    device_id = Column(String(255), nullable=False)  # Requesting device
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # NULL until confirmed
    platform = Column(String(20), nullable=False)  # ios, android
    device_name = Column(String(100), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_pairing_codes_code', 'code'),
        Index('ix_pairing_codes_expires', 'expires_at'),
    )
```

**RefreshToken Model:**

```python
# backend/app/models/refresh_token.py

class RefreshToken(Base):
    """
    Refresh tokens for mobile JWT authentication.

    Tokens are stored as SHA-256 hashes for security.
    Old tokens are revoked on rotation.
    """
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), nullable=False)  # SHA-256 hash
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)  # NULL if valid
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    device = relationship("Device", back_populates="refresh_tokens")

    __table_args__ = (
        Index('ix_refresh_tokens_hash', 'token_hash'),
        Index('ix_refresh_tokens_device', 'device_id'),
    )

    @property
    def is_valid(self) -> bool:
        """Token is valid if not expired and not revoked."""
        if self.revoked_at:
            return False
        return datetime.now(timezone.utc) < self.expires_at
```

**Pydantic Schemas:**

```python
# backend/app/schemas/mobile_auth.py

class PairingRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)
    platform: Literal['ios', 'android']
    device_name: Optional[str] = Field(None, max_length=100)

class PairingCodeResponse(BaseModel):
    code: str
    expires_in: int  # seconds

class PairingConfirmRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

class TokenExchangeRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    device_id: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str
    device_id: str
```

### APIs and Interfaces

```yaml
POST /api/v1/mobile/auth/pair:
  summary: Generate 6-digit pairing code
  description: Mobile app requests pairing code to display to user
  requestBody:
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/PairingRequest'
  responses:
    200:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PairingCodeResponse'
    429:
      description: Rate limit exceeded (5 attempts/minute)

POST /api/v1/mobile/auth/confirm:
  summary: Confirm pairing code (web dashboard)
  security:
    - bearerAuth: []
  requestBody:
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/PairingConfirmRequest'
  responses:
    200:
      content:
        application/json:
          schema:
            type: object
            properties:
              confirmed: boolean
              device_name: string
              platform: string

POST /api/v1/mobile/auth/verify:
  summary: Exchange confirmed code for tokens
  requestBody:
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/TokenExchangeRequest'
  responses:
    200:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/TokenPair'
    401:
      description: Invalid or unconfirmed code

POST /api/v1/auth/refresh:
  summary: Refresh access token
  requestBody:
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/TokenRefreshRequest'
  responses:
    200:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/TokenPair'
    401:
      description: Invalid or revoked refresh token
```

### Workflows and Sequencing

**Complete Pairing Flow:**

```
Mobile App                 ArgusAI Server              Web Dashboard
    │                           │                           │
    │ POST /mobile/auth/pair    │                           │
    │ {device_id, platform}     │                           │
    │──────────────────────────►│                           │
    │                           │                           │
    │                           │──► Generate 6-digit code  │
    │                           │──► Store PairingCode      │
    │                           │──► Set 5-min expiry       │
    │                           │                           │
    │                           │   WebSocket: PAIRING_REQ  │
    │                           │──────────────────────────►│
    │                           │                           │
    │ {code: "482916",          │                           │
    │  expires_in: 300}         │                           │
    │◄──────────────────────────│                           │
    │                           │                           │
    │  User sees code           │      User sees prompt     │
    │  on mobile screen         │      to enter code        │
    │                           │                           │
    │                           │ POST /mobile/auth/confirm │
    │                           │ {code: "482916"}          │
    │                           │◄──────────────────────────│
    │                           │                           │
    │                           │──► Verify code valid      │
    │                           │──► Set confirmed_at       │
    │                           │──► Set user_id            │
    │                           │                           │
    │                           │ {confirmed: true}         │
    │                           │──────────────────────────►│
    │                           │                           │
    │ POST /mobile/auth/verify  │                           │
    │ {code: "482916"}          │                           │
    │──────────────────────────►│                           │
    │                           │                           │
    │                           │──► Verify code confirmed  │
    │                           │──► Create/update Device   │
    │                           │──► Generate JWT pair      │
    │                           │──► Delete pairing code    │
    │                           │                           │
    │ {access_token,            │                           │
    │  refresh_token,           │                           │
    │  device_id}               │                           │
    │◄──────────────────────────│                           │
```

**Token Refresh with Rotation:**

```
Mobile App                 ArgusAI Server
    │                           │
    │ POST /auth/refresh        │
    │ {refresh_token, device_id}│
    │──────────────────────────►│
    │                           │
    │                           │──► Hash incoming token
    │                           │──► Find matching RefreshToken
    │                           │──► Verify not revoked/expired
    │                           │──► Verify device_id matches
    │                           │
    │                           │──► REVOKE old refresh token
    │                           │──► Generate NEW token pair
    │                           │──► Store new refresh token
    │                           │
    │ {new_access_token,        │
    │  new_refresh_token}       │
    │◄──────────────────────────│
```

**Service Implementation:**

```python
# backend/app/services/mobile/pairing_service.py

class PairingService:
    CODE_EXPIRY_SECONDS = 300  # 5 minutes

    async def generate_pairing_code(
        self,
        device_id: str,
        platform: str,
        device_name: Optional[str] = None,
    ) -> PairingCodeResponse:
        """Generate cryptographically random 6-digit code."""
        # Rate limiting check
        if await self._is_rate_limited(device_id):
            raise HTTPException(status_code=429, detail="Too many attempts")

        # Generate random code
        code = ''.join(secrets.choice('0123456789') for _ in range(6))

        # Ensure uniqueness
        while await self._code_exists(code):
            code = ''.join(secrets.choice('0123456789') for _ in range(6))

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.CODE_EXPIRY_SECONDS)

        pairing = PairingCode(
            code=code,
            device_id=device_id,
            platform=platform,
            device_name=device_name,
            expires_at=expires_at,
        )

        self.db.add(pairing)
        await self.db.commit()

        # Broadcast to dashboard
        await self._broadcast_pairing_request(code, device_name, platform)

        return PairingCodeResponse(code=code, expires_in=self.CODE_EXPIRY_SECONDS)

    async def confirm_pairing(self, code: str, user_id: str) -> bool:
        """User confirms code from dashboard."""
        pairing = await self._get_valid_pairing(code)
        if not pairing:
            return False

        pairing.user_id = user_id
        pairing.confirmed_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def verify_and_exchange(self, code: str) -> Optional[TokenPair]:
        """Exchange confirmed code for JWT tokens."""
        pairing = await self._get_confirmed_pairing(code)
        if not pairing:
            return None

        # Create or get device
        device = await self._get_or_create_device(
            device_id=pairing.device_id,
            user_id=pairing.user_id,
            platform=pairing.platform,
            name=pairing.device_name,
        )
        device.pairing_confirmed = True

        # Generate tokens
        token_service = TokenService(self.db, settings.SECRET_KEY)
        token_pair = await token_service.generate_token_pair(device)

        # Delete used code
        await self.db.delete(pairing)
        await self.db.commit()

        return token_pair
```

```python
# backend/app/services/mobile/token_service.py

class TokenService:
    ACCESS_EXPIRE_MINUTES = 15
    REFRESH_EXPIRE_DAYS = 30
    GRACE_PERIOD_SECONDS = 5

    async def generate_token_pair(self, device: Device) -> TokenPair:
        """Generate access + refresh token pair."""
        access_token = self._create_access_token(device)
        refresh_token, _ = await self._create_refresh_token(device)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.ACCESS_EXPIRE_MINUTES * 60,
            device_id=str(device.id),
        )

    def _create_access_token(self, device: Device) -> str:
        """Create short-lived JWT with device claim."""
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_EXPIRE_MINUTES)
        payload = {
            "sub": device.user_id,
            "device_id": str(device.id),
            "platform": device.platform,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    async def _create_refresh_token(self, device: Device) -> Tuple[str, RefreshToken]:
        """Create refresh token with hashed storage."""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        refresh = RefreshToken(
            device_id=device.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=self.REFRESH_EXPIRE_DAYS),
        )

        self.db.add(refresh)
        await self.db.commit()

        return token, refresh

    async def refresh_tokens(
        self,
        refresh_token: str,
        device_id: str,
    ) -> Optional[TokenPair]:
        """Refresh with rotation - old token revoked."""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        # Find valid token
        refresh = await self.db.execute(
            select(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .where(RefreshToken.device_id == device_id)
            .where(RefreshToken.revoked_at.is_(None))
            .where(RefreshToken.expires_at > datetime.utcnow())
        )
        refresh = refresh.scalar_one_or_none()

        if not refresh:
            return None

        device = await self.db.get(Device, device_id)
        if not device:
            return None

        # Revoke old token (rotation)
        refresh.revoked_at = datetime.utcnow()

        # Generate new pair
        new_pair = await self.generate_token_pair(device)

        await self.db.commit()
        return new_pair

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens on password change."""
        devices = await self.db.execute(
            select(Device).where(Device.user_id == user_id)
        )
        device_ids = [d.id for d in devices.scalars().all()]

        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.device_id.in_(device_ids))
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount
```

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pairing code generation | <50ms | API response time |
| Token exchange | <100ms | Code verification + JWT |
| Token refresh | <100ms | Hash lookup + generation |

### Security

- **NFR1:** Pairing codes are cryptographically random (secrets.choice)
- **NFR2:** Refresh tokens stored as SHA-256 hashes
- **NFR3:** Rate limiting: 5 pairing attempts per minute
- **NFR4:** Tokens revoked immediately on password change
- **NFR5:** Old refresh token revoked on rotation
- **NFR6:** Failed pairing attempts logged for security monitoring

### Reliability/Availability

- **NFR7:** Grace period (5s) for concurrent refresh requests
- **NFR8:** Expired codes auto-cleaned by background job
- **NFR9:** Device deletion cascades to revoke all tokens

### Observability

- Log pairing attempts with device_id, platform, success/failure
- Metric: `pairing_attempts_total{status}` counter
- Metric: `token_refreshes_total` counter
- Alert on high rate of failed pairing attempts (brute force detection)

## Dependencies and Integrations

**Backend Dependencies:**
```
python-jose>=3.3.0  # JWT encoding/decoding
slowapi>=0.1.9      # Rate limiting
```

**Integration Points:**
- Device model (P12-2) - token association
- WebSocketManager - pairing notifications
- User model - password change hook

## Acceptance Criteria (Authoritative)

1. **AC1:** POST /mobile/auth/pair returns 6-digit code and expires_in
2. **AC2:** Pairing codes expire after 5 minutes
3. **AC3:** User can confirm pairing code via dashboard UI
4. **AC4:** POST /mobile/auth/verify exchanges confirmed code for JWT pair
5. **AC5:** JWT access token includes device_id claim
6. **AC6:** POST /auth/refresh returns new token pair
7. **AC7:** Old refresh token is revoked on rotation
8. **AC8:** Password change revokes all user tokens
9. **AC9:** Rate limiting returns 429 after 5 attempts/minute
10. **AC10:** WebSocket broadcasts pairing request to dashboard

## Traceability Mapping

| AC | Spec Section | Component/API | Test Idea |
|----|--------------|---------------|-----------|
| AC1 | APIs | POST /mobile/auth/pair | Generate, verify 6 digits |
| AC2 | Data Models | PairingCode.expires_at | Expired code rejected |
| AC3 | Workflows | PairingConfirmation.tsx | UI confirms code |
| AC4 | Workflows | POST /mobile/auth/verify | Full exchange flow |
| AC5 | Workflows | TokenService._create_access_token | Decode, check device_id |
| AC6 | APIs | POST /auth/refresh | Refresh, verify new tokens |
| AC7 | Workflows | TokenService.refresh_tokens | Old token revoked_at set |
| AC8 | Workflows | TokenService.revoke_all_user_tokens | Password change hook |
| AC9 | APIs | Rate limiter | 6th attempt returns 429 |
| AC10 | Workflows | WebSocketManager.broadcast | Dashboard receives event |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1:** Concurrent refresh could cause token reuse
  - *Mitigation:* 5-second grace period, revoke on first use
- **R2:** Brute force pairing attempts
  - *Mitigation:* Rate limiting, 6-digit code = 1M combinations

**Assumptions:**
- **A1:** P12-2 Device model and endpoints are complete
- **A2:** WebSocket infrastructure from Phase 11 is available
- **A3:** SECRET_KEY environment variable is configured

**Open Questions:**
- **Q1:** Should we support multiple concurrent pairings per device? (Suggested: No)
- **Q2:** Should expired codes be cleaned immediately or via cron? (Suggested: Cron every 10 min)

## Test Strategy Summary

**Unit Tests:**
- `test_pairing_code_generation` - Random, unique codes
- `test_pairing_expiry` - 5-minute expiry enforced
- `test_token_rotation` - Old token revoked
- `test_token_hash_storage` - Never plaintext
- `test_rate_limiting` - 6th attempt blocked

**Integration Tests:**
- `test_complete_pairing_flow` - End-to-end pairing
- `test_token_refresh_flow` - Refresh with new tokens
- `test_password_change_revokes_tokens` - All tokens invalid

**Frontend Tests:**
- `PairingConfirmation.test.tsx` - Code entry, confirmation

---

**Created:** 2025-12-26
**Stories:** P12-3.1, P12-3.2, P12-3.3, P12-3.4, P12-3.5, P12-3.6
