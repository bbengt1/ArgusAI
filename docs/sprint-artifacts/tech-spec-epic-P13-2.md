# Epic Technical Specification: Cloud Relay

**Epic ID:** P13-2
**Phase:** 13 - Platform Maturity & External Integration
**Priority:** P3
**Generated:** 2025-12-28
**PRD Reference:** docs/PRD-phase13.md
**Epic Reference:** docs/epics-phase13.md
**Architecture Reference:** docs/architecture/cloud-relay-architecture.md

---

## Executive Summary

This epic extends the existing Cloudflare Tunnel implementation (Phase 11) with additional configuration UI, connectivity testing, and WebSocket relay support. The tunnel service already exists (`backend/app/services/tunnel_service.py`) - this epic focuses on improving the user experience and reliability.

**Functional Requirements Coverage:** FR11-FR18 (8 requirements)
**Dependency:** Requires P13-1 (API Key Management) for external API authentication

---

## Architecture Overview

### Current State (Phase 11)

The tunnel service already implements:
- Cloudflared subprocess management
- Connection status monitoring (TunnelStatus enum)
- Health check loop (30-second intervals)
- Auto-reconnect with exponential backoff
- Prometheus metrics integration

### Phase 13 Additions

```
                          Phase 11 (Existing)                    Phase 13 (New)
                    ┌─────────────────────────────┐     ┌────────────────────────────┐
                    │      TunnelService          │     │   TunnelConfigManager      │
                    │  - start(token)             │     │  - Store encrypted token   │
                    │  - stop()                   │     │  - Load on startup         │
                    │  - get_status_dict()        │     │  - Settings UI binding     │
                    │  - _health_check_loop()     │     └────────────┬───────────────┘
                    │  - _reconnect()             │                  │
                    └──────────────┬──────────────┘                  │
                                   │                                 │
                    ┌──────────────▼──────────────────────────────────▼─────────────┐
                    │                        API Layer                                │
                    │   GET  /api/v1/system/tunnel-status   (existing)               │
                    │   POST /api/v1/system/tunnel/test     (NEW)                    │
                    │   PUT  /api/v1/system/tunnel/config   (NEW)                    │
                    └───────────────────────────────────────────────────────────────┘
                                              │
                    ┌─────────────────────────▼────────────────────────────┐
                    │                  WebSocket Relay                      │
                    │   Existing WS endpoints work through tunnel           │
                    │   No code changes needed - Cloudflare handles it      │
                    └──────────────────────────────────────────────────────┘
```

### Component Architecture

```
backend/app/
├── services/
│   └── tunnel_service.py        # EXISTING: Core tunnel management
│   └── tunnel_config_service.py # NEW: Encrypted token storage
├── api/v1/
│   └── system.py                # MODIFY: Add tunnel config/test endpoints
└── core/
    └── startup.py               # MODIFY: Auto-start tunnel on boot

frontend/
├── components/settings/
│   └── TunnelSettings.tsx       # NEW: Tunnel configuration UI
└── hooks/
    └── useTunnelStatus.ts       # NEW: Real-time tunnel status
```

---

## Story Specifications

### Story P13-2.1: Add Tunnel Configuration to Settings

**Acceptance Criteria:**
- AC-2.1.1: Given the Settings page, when viewing the Tunnel section, then I can enter/update the Cloudflare tunnel token
- AC-2.1.2: Given a tunnel token is saved, when the token is stored, then it is encrypted with Fernet before database storage
- AC-2.1.3: Given the Settings UI, when tunnel is configured, then current connection status is displayed

**Technical Specification:**

```python
# backend/app/services/tunnel_config_service.py
from cryptography.fernet import Fernet
from app.core.config import settings
from app.models.system_setting import SystemSetting
from sqlalchemy.orm import Session

class TunnelConfigService:
    """Manages encrypted storage of tunnel configuration."""

    SETTING_KEY_TOKEN = "tunnel_token"
    SETTING_KEY_ENABLED = "tunnel_enabled"

    def __init__(self):
        self._fernet = Fernet(settings.ENCRYPTION_KEY.encode())

    def save_token(self, db: Session, token: str) -> None:
        """
        Save tunnel token encrypted in database.

        The token is encrypted with Fernet using the same key
        used for AI API keys (ENCRYPTION_KEY env var).
        """
        encrypted_token = self._fernet.encrypt(token.encode()).decode()

        setting = db.query(SystemSetting).filter(
            SystemSetting.key == self.SETTING_KEY_TOKEN
        ).first()

        if setting:
            setting.value = f"encrypted:{encrypted_token}"
        else:
            setting = SystemSetting(
                key=self.SETTING_KEY_TOKEN,
                value=f"encrypted:{encrypted_token}",
                description="Cloudflare Tunnel token (encrypted)",
            )
            db.add(setting)

        db.commit()

    def get_token(self, db: Session) -> str | None:
        """Retrieve and decrypt tunnel token."""
        setting = db.query(SystemSetting).filter(
            SystemSetting.key == self.SETTING_KEY_TOKEN
        ).first()

        if not setting or not setting.value.startswith("encrypted:"):
            return None

        encrypted = setting.value[10:]  # Remove "encrypted:" prefix
        return self._fernet.decrypt(encrypted.encode()).decode()

    def is_enabled(self, db: Session) -> bool:
        """Check if tunnel is enabled in settings."""
        setting = db.query(SystemSetting).filter(
            SystemSetting.key == self.SETTING_KEY_ENABLED
        ).first()
        return setting and setting.value.lower() == "true"

    def set_enabled(self, db: Session, enabled: bool) -> None:
        """Set tunnel enabled/disabled status."""
        setting = db.query(SystemSetting).filter(
            SystemSetting.key == self.SETTING_KEY_ENABLED
        ).first()

        if setting:
            setting.value = str(enabled).lower()
        else:
            setting = SystemSetting(
                key=self.SETTING_KEY_ENABLED,
                value=str(enabled).lower(),
                description="Whether Cloudflare Tunnel is enabled",
            )
            db.add(setting)

        db.commit()
```

**API Endpoint:**
```python
# backend/app/api/v1/system.py - Add to existing file
@router.put("/tunnel/config", response_model=MessageResponse)
async def update_tunnel_config(
    config: TunnelConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update tunnel configuration.

    Saves the token encrypted and optionally starts/stops the tunnel.
    """
    tunnel_config_service.save_token(db, config.token)
    tunnel_config_service.set_enabled(db, config.enabled)

    tunnel_service = get_tunnel_service()

    if config.enabled:
        if not tunnel_service.is_running:
            await tunnel_service.start(config.token)
    else:
        if tunnel_service.is_running:
            await tunnel_service.stop()

    return MessageResponse(message="Tunnel configuration updated")
```

**Files to Create/Modify:**
- `backend/app/services/tunnel_config_service.py` (NEW)
- `backend/app/api/v1/system.py` (MODIFY)
- `backend/app/schemas/system.py` (MODIFY: add TunnelConfigRequest)

---

### Story P13-2.2: Implement Cloudflare Tunnel Service Integration

**Note:** The core TunnelService already exists from Phase 11. This story focuses on integration improvements.

**Acceptance Criteria:**
- AC-2.2.1: Given tunnel is enabled in settings, when the backend starts, then tunnel connection is automatically established
- AC-2.2.2: Given tunnel was previously running, when backend restarts, then tunnel auto-reconnects using saved token
- AC-2.2.3: Given auto-start is configured, when fallback to local fails, then appropriate error is logged

**Technical Specification:**

```python
# backend/app/core/startup.py
async def startup_tunnel():
    """
    Initialize tunnel connection on startup if configured.

    Called during FastAPI lifespan startup.
    """
    from app.core.database import SessionLocal
    from app.services.tunnel_config_service import get_tunnel_config_service
    from app.services.tunnel_service import get_tunnel_service

    db = SessionLocal()
    try:
        config_service = get_tunnel_config_service()

        if not config_service.is_enabled(db):
            logger.info("Tunnel disabled in settings, skipping auto-start")
            return

        token = config_service.get_token(db)
        if not token:
            logger.warning("Tunnel enabled but no token configured")
            return

        tunnel_service = get_tunnel_service()
        success = await tunnel_service.start(token)

        if success:
            logger.info("Tunnel auto-started successfully")
        else:
            logger.error("Tunnel auto-start failed")

    finally:
        db.close()

# Integrate with FastAPI lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await startup_tunnel()
    yield
    # Shutdown
    tunnel_service = get_tunnel_service()
    if tunnel_service.is_running:
        await tunnel_service.stop()
```

**Files to Create/Modify:**
- `backend/app/core/startup.py` (MODIFY)
- `backend/main.py` (MODIFY: add lifespan)

---

### Story P13-2.3: Add Tunnel Status Endpoint

**Note:** Basic status endpoint already exists. This story enhances it.

**Acceptance Criteria:**
- AC-2.3.1: Given the tunnel status endpoint, when called, then returns connection health, uptime, and last connected time
- AC-2.3.2: Given tunnel is connected, when status is requested, then hostname is included in response
- AC-2.3.3: Given tunnel has errors, when status is requested, then error message is included

**Technical Specification:**

```python
# backend/app/api/v1/system.py - Enhance existing endpoint
@router.get("/tunnel-status", response_model=TunnelStatusResponse)
async def get_tunnel_status():
    """
    Get detailed tunnel connection status.

    Returns connection state, hostname, uptime, and error info.
    """
    tunnel_service = get_tunnel_service()
    status = tunnel_service.get_status_dict()

    return TunnelStatusResponse(
        status=status["status"],
        is_connected=status["is_connected"],
        is_running=status["is_running"],
        hostname=status["hostname"],
        error=status.get("error"),
        uptime_seconds=status.get("uptime_seconds", 0),
        last_connected=status.get("last_connected"),
        reconnect_count=status.get("reconnect_count", 0),
    )

# Schema
class TunnelStatusResponse(BaseModel):
    status: str  # disconnected, connecting, connected, error
    is_connected: bool
    is_running: bool
    hostname: str | None
    error: str | None
    uptime_seconds: float
    last_connected: datetime | None
    reconnect_count: int
```

**Files to Modify:**
- `backend/app/api/v1/system.py` (MODIFY)
- `backend/app/schemas/system.py` (MODIFY)

---

### Story P13-2.4: Implement Tunnel Connectivity Test

**Acceptance Criteria:**
- AC-2.4.1: Given a tunnel token, when test endpoint is called, then tunnel connection is attempted and result reported
- AC-2.4.2: Given test succeeds, when result is returned, then includes hostname and latency
- AC-2.4.3: Given test fails, when result is returned, then includes specific error message

**Technical Specification:**

```python
# backend/app/api/v1/system.py
@router.post("/tunnel/test", response_model=TunnelTestResponse)
async def test_tunnel_connectivity(
    request: TunnelTestRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Test tunnel connectivity without persisting configuration.

    Starts tunnel with provided token, waits for connection,
    and returns result. Stops tunnel after test unless it was
    already running with a different configuration.
    """
    import time

    tunnel_service = get_tunnel_service()
    was_running = tunnel_service.is_running
    original_status = tunnel_service.get_status_dict() if was_running else None

    start_time = time.time()

    try:
        # Stop existing tunnel if running
        if was_running:
            await tunnel_service.stop()

        # Start with test token
        success = await tunnel_service.start(request.token)

        if not success:
            return TunnelTestResponse(
                success=False,
                error=tunnel_service.error_message or "Failed to start tunnel",
                latency_ms=None,
                hostname=None,
            )

        # Wait for connection (max 30 seconds)
        for _ in range(30):
            await asyncio.sleep(1)
            if tunnel_service.is_connected:
                break

        latency_ms = int((time.time() - start_time) * 1000)

        if tunnel_service.is_connected:
            return TunnelTestResponse(
                success=True,
                error=None,
                latency_ms=latency_ms,
                hostname=tunnel_service.hostname,
            )
        else:
            return TunnelTestResponse(
                success=False,
                error=tunnel_service.error_message or "Connection timeout",
                latency_ms=latency_ms,
                hostname=None,
            )

    finally:
        # Restore original state
        if not was_running:
            await tunnel_service.stop()

class TunnelTestRequest(BaseModel):
    token: str = Field(..., min_length=50)

class TunnelTestResponse(BaseModel):
    success: bool
    error: str | None
    latency_ms: int | None
    hostname: str | None
```

**Files to Modify:**
- `backend/app/api/v1/system.py` (MODIFY)
- `backend/app/schemas/system.py` (MODIFY)

---

### Story P13-2.5: WebSocket Relay Support

**Acceptance Criteria:**
- AC-2.5.1: Given tunnel is connected, when client connects via tunnel URL, then WebSocket events are received in real-time
- AC-2.5.2: Given local network is available, when connecting locally, then fallback to local WebSocket works
- AC-2.5.3: Given tunnel connection drops, when events occur, then reconnection is attempted automatically

**Technical Specification:**

WebSocket relay works automatically through Cloudflare Tunnel - no code changes needed. Cloudflare handles WebSocket protocol upgrade and proxying.

**Frontend Configuration:**
```typescript
// frontend/lib/websocket.ts
export function getWebSocketUrl(): string {
  // Use relative URL - works for both local and tunnel
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/api/v1/ws`;
}

// Reconnection with fallback
export function createReconnectingWebSocket(path: string) {
  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 10;

  function connect() {
    const url = getWebSocketUrl();
    ws = new WebSocket(url);

    ws.onopen = () => {
      reconnectAttempts = 0;
      console.log('WebSocket connected via', url);
    };

    ws.onclose = () => {
      if (reconnectAttempts < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        setTimeout(connect, delay);
        reconnectAttempts++;
      }
    };
  }

  connect();
  return ws;
}
```

**Frontend Tunnel Status Component:**
```typescript
// frontend/components/settings/TunnelSettings.tsx
export function TunnelSettings() {
  const [status, setStatus] = useState<TunnelStatus | null>(null);
  const [token, setToken] = useState('');
  const [enabled, setEnabled] = useState(false);
  const [testing, setTesting] = useState(false);

  // Poll status every 10 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch('/api/v1/system/tunnel-status');
      setStatus(await res.json());
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  async function handleTest() {
    setTesting(true);
    try {
      const res = await fetch('/api/v1/system/tunnel/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });
      const result = await res.json();
      // Show result in UI
    } finally {
      setTesting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cloud Relay (Cloudflare Tunnel)</CardTitle>
        <CardDescription>
          Access ArgusAI from anywhere via secure tunnel
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <StatusDot status={status?.status} />
            <span>{status?.status || 'Unknown'}</span>
            {status?.hostname && (
              <Badge variant="outline">{status.hostname}</Badge>
            )}
          </div>

          {/* Token input */}
          <div>
            <Label>Tunnel Token</Label>
            <Input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="eyJ..."
            />
          </div>

          {/* Enable toggle */}
          <div className="flex items-center gap-2">
            <Switch checked={enabled} onCheckedChange={setEnabled} />
            <Label>Enable tunnel on startup</Label>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleTest} disabled={testing}>
              {testing ? 'Testing...' : 'Test Connection'}
            </Button>
            <Button onClick={handleSave}>Save Configuration</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

**Files to Create/Modify:**
- `frontend/components/settings/TunnelSettings.tsx` (NEW)
- `frontend/lib/websocket.ts` (MODIFY)

---

## API Contracts

### Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/system/tunnel-status` | Get tunnel status | JWT or API Key |
| POST | `/api/v1/system/tunnel/test` | Test tunnel connectivity | Admin JWT |
| PUT | `/api/v1/system/tunnel/config` | Update tunnel config | Admin JWT |

---

## Security Considerations

### NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR5 | TLS 1.3 encryption | Handled by Cloudflare |
| NFR6 | Encrypted token storage | Fernet encryption |
| NFR9 | <500ms added latency | Cloudflare edge network |
| NFR13 | Auto-reconnect | Existing exponential backoff |

---

## Dependencies

### Existing Services
- `TunnelService` (Phase 11)
- Fernet encryption (ENCRYPTION_KEY env var)

### External
- cloudflared binary must be installed
- Cloudflare Zero Trust account with tunnel configured

---

## Testing Strategy

### Unit Tests
- Token encryption/decryption
- Auto-start logic
- Status response formatting

### Integration Tests
- Full tunnel start/stop cycle
- Configuration persistence
- Status polling

### Manual Tests
- Remote connection through tunnel
- WebSocket events through tunnel
- Reconnection after network interruption
