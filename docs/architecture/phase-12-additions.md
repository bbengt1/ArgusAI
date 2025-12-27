# Phase 12 Architecture Additions

**Phase:** 12 - Mobile Backend Infrastructure & Entity-Based Alerts
**Date:** 2025-12-26
**PRD:** docs/PRD-phase12.md
**Epics:** docs/epics-phase12.md (to be created)

---

## Phase 12 Executive Summary

Phase 12 delivers personalized alerting and mobile app backend infrastructure:

- **Entity-Based Alert Rules** - Create alerts that trigger for specific recognized people or vehicles
- **Mobile Device Registration** - Backend device management for future native apps
- **Mobile Authentication & Pairing** - Secure 6-digit code pairing flow with JWT tokens
- **Query-Adaptive Optimization** - Enhanced frame selection with batch processing and diversity filtering

---

## Phase 12 Technology Stack Additions

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Rate Limiting | slowapi | 0.1.9+ | Pairing attempt rate limiting |
| Token Rotation | python-jose | 3.3+ | JWT refresh token rotation |
| Batch Processing | numpy | 1.26+ | Batch embedding operations |

---

## Phase 12 Project Structure Additions

```
backend/
├── app/
│   ├── services/
│   │   ├── mobile/
│   │   │   ├── __init__.py
│   │   │   ├── device_service.py      # P12-2: Device management
│   │   │   ├── pairing_service.py     # P12-3: Pairing code flow
│   │   │   └── token_service.py       # P12-3: JWT refresh/rotation
│   │   └── query_adaptive/
│   │       ├── __init__.py
│   │       ├── batch_embedder.py      # P12-4.1: Batch embedding
│   │       ├── diversity_filter.py    # P12-4.2: Duplicate prevention
│   │       └── query_cache.py         # P12-4.3: Result caching
│   ├── api/v1/
│   │   ├── mobile_auth.py             # P12-3: Pairing endpoints
│   │   └── devices.py                 # P12-2: Device CRUD (extends P11)
│   └── models/
│       └── pairing_code.py            # P12-3: Temporary pairing codes

frontend/
├── components/
│   ├── settings/
│   │   ├── DeviceManager.tsx          # P12-2: Device list management
│   │   └── PairingConfirmation.tsx    # P12-3: Confirm pairing codes
│   └── rules/
│       └── EntityRuleSelector.tsx     # P12-1: Entity selection in rules
```

---

## Phase 12 Database Schema Additions

### AlertRule Extension (P12-1)

```sql
-- Add entity_id column to alert_rules table
ALTER TABLE alert_rules ADD COLUMN entity_id TEXT;
ALTER TABLE alert_rules ADD COLUMN entity_match_mode TEXT DEFAULT 'specific';
-- entity_match_mode: 'specific' (exact entity), 'unknown' (any unrecognized), 'any' (any entity)

ALTER TABLE alert_rules ADD CONSTRAINT fk_alert_rules_entity
    FOREIGN KEY (entity_id) REFERENCES recognized_entities(id) ON DELETE SET NULL;

CREATE INDEX idx_alert_rules_entity_id ON alert_rules(entity_id);
```

**Extended Conditions JSON structure:**
```json
{
  "object_types": ["person"],
  "confidence_min": 70,
  "entity_id": "uuid-of-specific-entity",      // NEW: Specific entity filter
  "entity_match_mode": "specific",             // NEW: 'specific', 'unknown', 'any'
  "time_range": { "start": "09:00", "end": "18:00" },
  "cameras": ["camera-uuid-1"]
}
```

### PairingCode Model (P12-3)

```python
class PairingCode(Base):
    __tablename__ = "pairing_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(6), unique=True, nullable=False)  # 6-digit code
    device_id = Column(String(255), nullable=False)        # Device requesting pairing
    user_id = Column(String(36), ForeignKey("users.id"))   # NULL until confirmed
    platform = Column(String(20), nullable=False)          # ios, android
    device_name = Column(String(100))                      # User-friendly name
    expires_at = Column(DateTime, nullable=False)          # 5-minute expiry
    confirmed_at = Column(DateTime)                        # When user confirmed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite index for lookups
    __table_args__ = (
        Index('ix_pairing_codes_code_expires', 'code', 'expires_at'),
    )
```

```sql
CREATE TABLE pairing_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    device_id TEXT NOT NULL,
    user_id TEXT,
    platform TEXT NOT NULL,
    device_name TEXT,
    expires_at TIMESTAMP NOT NULL,
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_pairing_codes_code_expires ON pairing_codes(code, expires_at);
```

### RefreshToken Model (P12-3)

```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False)
    token_hash = Column(String(64), nullable=False)        # SHA-256 hash
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)                          # NULL if valid
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    device = relationship("Device", back_populates="refresh_tokens")
```

### Device Model Extension (P12-2)

```python
# Extends the Phase 11 Device model
class Device(Base):
    # ... existing fields from P11 ...

    # New Phase 12 additions
    pairing_confirmed = Column(Boolean, default=False)     # Pairing flow completed
    refresh_tokens = relationship("RefreshToken", back_populates="device", cascade="all, delete-orphan")
```

---

## Phase 12 Service Architecture

### Entity Alert Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Event Created                                 │
│                              │                                       │
│                              ▼                                       │
│                   ┌─────────────────────┐                           │
│                   │   AlertRuleEngine   │                           │
│                   └──────────┬──────────┘                           │
│                              │                                       │
│           ┌──────────────────┼──────────────────┐                   │
│           ▼                  ▼                  ▼                   │
│   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│   │ Standard Rule │  │ Entity Rule   │  │ Unknown Rule  │          │
│   │ (no entity)   │  │ (specific ID) │  │ (stranger)    │          │
│   └───────┬───────┘  └───────┬───────┘  └───────┬───────┘          │
│           │                  │                  │                   │
│           ▼                  ▼                  ▼                   │
│     Check object       Check event.       Check event has          │
│     types, time,      entity_id matches   no matched entity        │
│     cameras, etc.     rule.entity_id      (entity_id IS NULL)      │
│           │                  │                  │                   │
│           └──────────────────┼──────────────────┘                   │
│                              ▼                                       │
│                    Trigger Notifications                             │
│                    (include entity name)                             │
└─────────────────────────────────────────────────────────────────────┘
```

### Entity Alert Engine Extension (P12-1)

```python
class AlertRuleEngine:
    """Extended to support entity-based filtering."""

    async def evaluate_rule(
        self,
        rule: AlertRule,
        event: Event,
        entity: Optional[RecognizedEntity] = None,
    ) -> bool:
        """
        Evaluate if rule matches event.

        Entity matching modes:
        - 'specific': rule.entity_id must match event's matched entity
        - 'unknown': event must have NO matched entity (stranger detection)
        - 'any': any entity match, or no entity check (default behavior)
        """
        # Standard condition checks first
        if not self._check_standard_conditions(rule, event):
            return False

        # Entity-specific checks
        entity_mode = rule.conditions.get('entity_match_mode', 'any')
        rule_entity_id = rule.entity_id

        if entity_mode == 'specific' and rule_entity_id:
            # Must match specific entity
            if not entity or entity.id != rule_entity_id:
                return False

        elif entity_mode == 'unknown':
            # Stranger detection - must NOT have a matched entity
            if entity is not None:
                return False

        # 'any' mode or no entity filter - proceed normally
        return True

    def format_notification(
        self,
        rule: AlertRule,
        event: Event,
        entity: Optional[RecognizedEntity] = None,
    ) -> EventNotification:
        """Include entity name in notification if entity-based rule."""
        base_notification = self._create_base_notification(rule, event)

        if entity:
            base_notification.title = f"{entity.name} detected"
            base_notification.body = f"{entity.name}: {event.description}"
            base_notification.metadata['entity_id'] = entity.id
            base_notification.metadata['entity_name'] = entity.name
        elif rule.conditions.get('entity_match_mode') == 'unknown':
            base_notification.title = "Unknown person detected"

        return base_notification
```

### Mobile Device Pairing Flow (P12-3)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Mobile Device Pairing Flow                       │
│                                                                      │
│   Mobile App                    ArgusAI Server           Web Dashboard│
│       │                              │                        │      │
│       │  POST /mobile/auth/pair      │                        │      │
│       │  {device_id, platform}       │                        │      │
│       │─────────────────────────────►│                        │      │
│       │                              │                        │      │
│       │   {code: "482916",           │                        │      │
│       │    expires_in: 300}          │   WebSocket:           │      │
│       │◄─────────────────────────────│   PAIRING_REQUESTED    │      │
│       │                              │───────────────────────►│      │
│       │                              │                        │      │
│       │                              │                        │      │
│       │     User sees code           │     User sees prompt   │      │
│       │     on mobile screen         │     "Enter code: ____" │      │
│       │                              │                        │      │
│       │                              │   POST /mobile/auth/   │      │
│       │                              │   confirm {code}       │      │
│       │                              │◄───────────────────────│      │
│       │                              │                        │      │
│       │                              │   {confirmed: true}    │      │
│       │                              │───────────────────────►│      │
│       │                              │                        │      │
│       │  POST /mobile/auth/verify    │                        │      │
│       │  {code: "482916"}            │                        │      │
│       │─────────────────────────────►│                        │      │
│       │                              │                        │      │
│       │  {access_token, refresh_token,                        │      │
│       │   device_id, expires_in}     │                        │      │
│       │◄─────────────────────────────│                        │      │
│       │                              │                        │      │
└─────────────────────────────────────────────────────────────────────┘
```

### Pairing Service (P12-3)

```python
class PairingService:
    """Handles mobile device pairing via 6-digit codes."""

    CODE_EXPIRY_SECONDS = 300  # 5 minutes
    MAX_ATTEMPTS_PER_MINUTE = 5

    def __init__(self, db: AsyncSession, rate_limiter: RateLimiter):
        self.db = db
        self.rate_limiter = rate_limiter

    async def generate_pairing_code(
        self,
        device_id: str,
        platform: str,
        device_name: Optional[str] = None,
    ) -> PairingCodeResponse:
        """
        Generate a 6-digit pairing code for mobile device.

        Returns code that user must confirm on web dashboard.
        """
        # Generate cryptographically random 6-digit code
        code = ''.join(secrets.choice('0123456789') for _ in range(6))

        # Ensure uniqueness (regenerate if collision)
        while await self._code_exists(code):
            code = ''.join(secrets.choice('0123456789') for _ in range(6))

        expires_at = datetime.utcnow() + timedelta(seconds=self.CODE_EXPIRY_SECONDS)

        pairing = PairingCode(
            code=code,
            device_id=device_id,
            platform=platform,
            device_name=device_name,
            expires_at=expires_at,
        )

        self.db.add(pairing)
        await self.db.commit()

        # Notify web dashboard via WebSocket
        await self._broadcast_pairing_request(code, device_name, platform)

        return PairingCodeResponse(
            code=code,
            expires_in=self.CODE_EXPIRY_SECONDS,
        )

    async def confirm_pairing(
        self,
        code: str,
        user_id: str,
    ) -> bool:
        """
        User confirms pairing code from web dashboard.

        Called when user enters the 6-digit code on the web UI.
        """
        pairing = await self._get_valid_pairing(code)
        if not pairing:
            return False

        pairing.user_id = user_id
        pairing.confirmed_at = datetime.utcnow()
        await self.db.commit()

        return True

    async def verify_and_exchange(
        self,
        code: str,
    ) -> Optional[TokenPair]:
        """
        Mobile app exchanges confirmed code for JWT tokens.

        Only works if user has confirmed the code on dashboard.
        """
        pairing = await self._get_confirmed_pairing(code)
        if not pairing:
            return None

        # Create or update device record
        device = await self._get_or_create_device(
            device_id=pairing.device_id,
            user_id=pairing.user_id,
            platform=pairing.platform,
            name=pairing.device_name,
        )

        # Generate token pair
        token_pair = await self.token_service.generate_token_pair(device)

        # Delete used pairing code
        await self.db.delete(pairing)
        await self.db.commit()

        return token_pair
```

### Token Service with Refresh Rotation (P12-3)

```python
class TokenService:
    """JWT token management with refresh token rotation."""

    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 30
    REFRESH_GRACE_PERIOD_MINUTES = 5

    def __init__(self, db: AsyncSession, secret_key: str):
        self.db = db
        self.secret_key = secret_key

    async def generate_token_pair(self, device: Device) -> TokenPair:
        """Generate access token and refresh token for device."""
        access_token = self._create_access_token(device)
        refresh_token, refresh_record = await self._create_refresh_token(device)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            device_id=device.device_id,
        )

    def _create_access_token(self, device: Device) -> str:
        """Create short-lived access token with device claim."""
        expire = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": device.user_id,
            "device_id": device.id,
            "platform": device.platform,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    async def _create_refresh_token(self, device: Device) -> Tuple[str, RefreshToken]:
        """Create long-lived refresh token with rotation support."""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        refresh = RefreshToken(
            device_id=device.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        self.db.add(refresh)
        await self.db.commit()

        return token, refresh

    async def refresh_tokens(
        self,
        refresh_token: str,
        device_id: str,
    ) -> Optional[TokenPair]:
        """
        Refresh tokens with rotation.

        - Old refresh token is revoked
        - New access + refresh tokens issued
        - Sliding window extends expiration by 24 hours
        """
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        # Find valid refresh token
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

        # Revoke old refresh token (rotation)
        refresh.revoked_at = datetime.utcnow()

        # Generate new token pair
        new_pair = await self.generate_token_pair(device)

        await self.db.commit()
        return new_pair

    async def revoke_all_device_tokens(self, device_id: str) -> int:
        """Revoke all tokens for a device (used on device removal)."""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.device_id == device_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount

    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a user (used on password change)."""
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

### Query-Adaptive Batch Embedder (P12-4)

```python
class BatchEmbedder:
    """Batch processing for frame embeddings with 40%+ overhead reduction."""

    BATCH_SIZE = 8  # Optimal batch size for CLIP

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def embed_frames_batch(
        self,
        frames: List[np.ndarray],
        event_id: str,
    ) -> List[FrameEmbedding]:
        """
        Generate embeddings for multiple frames in batches.

        ~40% faster than sequential processing.
        """
        embeddings = []

        for i in range(0, len(frames), self.BATCH_SIZE):
            batch = frames[i:i + self.BATCH_SIZE]
            batch_embeddings = await self._process_batch(batch)

            for j, embedding in enumerate(batch_embeddings):
                frame_embedding = FrameEmbedding(
                    event_id=event_id,
                    frame_index=i + j,
                    embedding=embedding.tolist(),
                    model_version=self.embedding_service.model_version,
                )
                embeddings.append(frame_embedding)

        return embeddings

    async def _process_batch(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """Process a batch of frames through CLIP."""
        # Stack frames into batch tensor
        preprocessed = [self.embedding_service.preprocess(f) for f in frames]
        batch_tensor = torch.stack(preprocessed)

        # Single forward pass for batch
        with torch.no_grad():
            embeddings = self.embedding_service.model.encode_image(batch_tensor)

        return [e.cpu().numpy() for e in embeddings]
```

### Diversity Filter (P12-4)

```python
class DiversityFilter:
    """Prevents selection of near-duplicate frames."""

    SIMILARITY_THRESHOLD = 0.92  # Frames more similar than this are duplicates

    def filter_diverse_frames(
        self,
        embeddings: List[np.ndarray],
        scores: List[float],
        top_k: int = 5,
    ) -> List[int]:
        """
        Select top-k frames while maintaining diversity.

        Uses greedy selection: pick highest score, then filter similar frames.
        """
        if len(embeddings) <= top_k:
            return list(range(len(embeddings)))

        # Sort by score descending
        scored_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )

        selected = []
        selected_embeddings = []

        for idx in scored_indices:
            if len(selected) >= top_k:
                break

            # Check similarity to already selected frames
            is_diverse = True
            for sel_emb in selected_embeddings:
                similarity = self._cosine_similarity(embeddings[idx], sel_emb)
                if similarity > self.SIMILARITY_THRESHOLD:
                    is_diverse = False
                    break

            if is_diverse:
                selected.append(idx)
                selected_embeddings.append(embeddings[idx])

        return selected

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
```

---

## Phase 12 API Contracts

### Entity Alert Rules API (P12-1)

```yaml
/api/v1/alert-rules:
  post:
    summary: Create alert rule with optional entity filter
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required: [name, conditions, actions]
            properties:
              name:
                type: string
              entity_id:
                type: string
                description: Optional specific entity to filter
              conditions:
                type: object
                properties:
                  entity_match_mode:
                    type: string
                    enum: [specific, unknown, any]
                    default: any
                  # ... other existing conditions
              actions:
                type: object

/api/v1/context/entities/{entity_id}/alert-rules:
  get:
    summary: List alert rules associated with an entity
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                rules:
                  type: array
                  items:
                    $ref: '#/components/schemas/AlertRule'
```

### Mobile Pairing API (P12-3)

```yaml
/api/v1/mobile/auth/pair:
  post:
    summary: Request pairing code for mobile device
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required: [device_id, platform]
            properties:
              device_id:
                type: string
                description: Unique device identifier
              platform:
                type: string
                enum: [ios, android]
              device_name:
                type: string
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: string
                  pattern: '^\d{6}$'
                expires_in:
                  type: integer
                  description: Seconds until code expires
      429:
        description: Rate limit exceeded (5 attempts/minute)

/api/v1/mobile/auth/confirm:
  post:
    summary: Confirm pairing code (called from web dashboard)
    security:
      - bearerAuth: []
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required: [code]
            properties:
              code:
                type: string
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                confirmed:
                  type: boolean
                device_name:
                  type: string
                platform:
                  type: string

/api/v1/mobile/auth/verify:
  post:
    summary: Exchange confirmed code for tokens
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required: [code]
            properties:
              code:
                type: string
    responses:
      200:
        content:
          application/json:
            schema:
              type: object
              properties:
                access_token:
                  type: string
                refresh_token:
                  type: string
                token_type:
                  type: string
                expires_in:
                  type: integer
                device_id:
                  type: string
      401:
        description: Invalid or unconfirmed code

/api/v1/auth/refresh:
  post:
    summary: Refresh access token
    requestBody:
      content:
        application/json:
          schema:
            type: object
            required: [refresh_token, device_id]
            properties:
              refresh_token:
                type: string
              device_id:
                type: string
    responses:
      200:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenPair'
      401:
        description: Invalid or revoked refresh token
```

### Device Management API Extension (P12-2)

```yaml
/api/v1/devices:
  get:
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
                    type: object
                    properties:
                      id:
                        type: string
                      device_id:
                        type: string
                      platform:
                        type: string
                      name:
                        type: string
                      last_seen_at:
                        type: string
                        format: date-time
                      pairing_confirmed:
                        type: boolean
                      inactive_warning:
                        type: boolean
                        description: True if inactive >90 days

  put:
    path: /api/v1/devices/{id}
    summary: Update device (rename)
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
    responses:
      200:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Device'
```

---

## Phase 12 ADRs

### ADR-P12-001: 6-Digit Pairing Codes over QR Codes

**Status:** Accepted

**Context:** Need secure way for mobile apps to authenticate with local ArgusAI instance.

**Decision:** Use 6-digit numeric pairing codes with 5-minute expiry.

**Rationale:**
- Simpler UX than QR scanning (works over phone/remote)
- 6 digits = 1M combinations, sufficient with rate limiting
- Time-limited codes prevent replay attacks
- Dashboard confirmation adds human-in-the-loop verification
- Compatible with all device types (no camera needed)

**Consequences:**
- Requires WebSocket for real-time code confirmation
- Rate limiting essential to prevent brute-force
- Users must be logged into web dashboard to confirm

---

### ADR-P12-002: Refresh Token Rotation

**Status:** Accepted

**Context:** Need secure long-lived sessions for mobile apps without exposing long-lived tokens.

**Decision:** Implement refresh token rotation - old token is revoked when new one is issued.

**Rationale:**
- Limits window of token theft impact
- Provides detection of token compromise (rotation fails)
- Industry best practice for mobile auth
- Sliding window maintains session without re-authentication

**Consequences:**
- More complex token management
- Single-use refresh tokens require careful storage
- Concurrent requests with same token can cause issues (mitigated with grace period)

---

### ADR-P12-003: Entity Match Modes for Alert Rules

**Status:** Accepted

**Context:** Entity-based alerts need to support multiple use cases.

**Decision:** Implement three match modes: 'specific', 'unknown', 'any'.

**Rationale:**
- 'specific': Alert for known person/vehicle (e.g., "When John arrives")
- 'unknown': Stranger detection (e.g., "Alert for unrecognized people")
- 'any': Standard behavior, entity filter disabled

**Consequences:**
- Additional logic in alert evaluation
- Clear UI needed to explain modes
- 'unknown' mode depends on entity recognition quality

---

### ADR-P12-004: Batch Embedding with Diversity Filtering

**Status:** Accepted

**Context:** Query-adaptive frame selection needs optimization.

**Decision:** Batch process embeddings and filter near-duplicates.

**Rationale:**
- Batch processing reduces per-frame overhead by ~40%
- Diversity filtering ensures selected frames show different content
- Greedy selection balances relevance and diversity

**Consequences:**
- Requires numpy for efficient batch operations
- May occasionally filter out relevant near-duplicate frames
- Similarity threshold needs tuning based on real-world testing

---

## Phase 12 Performance Considerations

### Entity Alert Evaluation

| Metric | Target | Measurement |
|--------|--------|-------------|
| Entity lookup | <5ms | Database query with index |
| Rule evaluation | <10ms | Additional overhead per entity rule |
| Total alert processing | <50ms | Standard + entity rules combined |

### Mobile Pairing

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code generation | <50ms | Crypto random + DB write |
| Code verification | <100ms | Lookup + token generation |
| Token refresh | <100ms | Hash verify + rotation |

### Batch Embedding

| Metric | Target | Measurement |
|--------|--------|-------------|
| Sequential (baseline) | ~100ms/frame | Current P11 implementation |
| Batch (8 frames) | ~60ms/frame | 40% reduction target |
| Diversity filter | <10ms | Similarity comparisons |

---

## Phase 12 Epic to Architecture Mapping

| Epic | Components | Services |
|------|------------|----------|
| P12-1: Entity Alerts | AlertRuleForm.tsx, EntityRuleSelector.tsx | AlertRuleEngine (extended) |
| P12-2: Device Registration | DeviceManager.tsx, devices.py | DeviceService |
| P12-3: Mobile Auth | PairingConfirmation.tsx, mobile_auth.py | PairingService, TokenService |
| P12-4: Query-Adaptive | smart-reanalyze endpoint | BatchEmbedder, DiversityFilter |

---

## Phase 12 Validation Checklist

### Entity-Based Alerts (P12-1)
- [ ] entity_id column added to alert_rules table
- [ ] Alert rule UI shows entity selector dropdown
- [ ] 'specific' mode matches exact entity
- [ ] 'unknown' mode triggers for strangers
- [ ] Entity name appears in push notifications
- [ ] Entity name appears in webhook payloads
- [ ] Entity detail page shows associated rules

### Mobile Device Registration (P12-2)
- [ ] Device CRUD endpoints functional
- [ ] Settings UI shows device list
- [ ] Device rename works
- [ ] Device deletion revokes all tokens
- [ ] Inactive device warning (>90 days)

### Mobile Authentication (P12-3)
- [ ] 6-digit code generation is cryptographically random
- [ ] Codes expire after 5 minutes
- [ ] WebSocket notifies dashboard of pairing request
- [ ] Dashboard confirmation links code to user
- [ ] Token exchange only works for confirmed codes
- [ ] Refresh token rotation works
- [ ] Password change revokes all user tokens
- [ ] Rate limiting prevents brute-force (5/min)

### Query-Adaptive Optimization (P12-4)
- [ ] Batch embedding 40% faster than sequential
- [ ] Diversity filter prevents near-duplicates
- [ ] Quality scores factor into selection
- [ ] Metrics track selection effectiveness
- [ ] Query cache reduces repeated lookups

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-26 | Initial Phase 12 architecture document |
