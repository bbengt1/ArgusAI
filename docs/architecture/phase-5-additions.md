# Phase 5 Additions

> **Phase 5 Update:** This section documents architectural additions for native HomeKit integration, ONVIF camera discovery, CI/CD pipeline, and quality/accessibility improvements. Phase 5 addresses accumulated backlog items while expanding platform support.

**Key Architectural Changes:**
1. **HomeKit Bridge** - Native HAP (HomeKit Accessory Protocol) implementation for Apple ecosystem
2. **ONVIF Discovery** - WS-Discovery for automatic camera detection on local network
3. **CI/CD Pipeline** - GitHub Actions for automated testing on PRs
4. **Frontend Testing** - Vitest + React Testing Library integration

---

## Phase 5 Technology Stack Additions

| Category | Decision | Version | Rationale |
|----------|----------|---------|-----------|
| **HomeKit Protocol** | HAP-python | 4.9+ | Mature Python HAP implementation, camera streaming support |
| **Camera Discovery** | onvif-zeep | Latest | ONVIF WS-Discovery with zeep SOAP client |
| **WS-Discovery** | WSDiscovery | 2.0+ | Multicast discovery for ONVIF cameras |
| **Video Transcoding** | ffmpeg | 6.0+ | RTSP to HLS transcoding for HomeKit cameras |
| **Frontend Testing** | Vitest | 2.0+ | Fast test runner, Vite-native, Jest-compatible |
| **Component Testing** | React Testing Library | 16+ | DOM testing utilities for React components |
| **JSDOM** | jsdom | 24+ | Browser environment simulation for tests |

---

## Phase 5 Project Structure Additions

```
backend/
├── app/
│   ├── services/
│   │   ├── homekit_service.py         # HAP bridge management, accessory lifecycle
│   │   ├── homekit_camera.py          # Camera accessory with RTSP-to-HLS streaming
│   │   ├── homekit_sensors.py         # Motion, occupancy, doorbell accessories
│   │   └── onvif_discovery_service.py # WS-Discovery, ONVIF device enumeration
│   ├── api/v1/
│   │   ├── homekit.py                 # GET/POST /api/v1/homekit/*, pairing management
│   │   └── discovery.py               # POST /api/v1/cameras/discover, /test
│   └── models/
│       └── homekit.py                 # HomeKitPairing model for persistent pairings
├── homekit/                           # HAP-python state directory
│   ├── accessory.state               # Pairing state and keys
│   └── accessory.json                # Accessory configuration
└── tests/
    └── test_services/
        ├── test_homekit_service.py
        └── test_onvif_discovery.py

frontend/
├── vitest.config.ts                   # Vitest configuration
├── vitest.setup.ts                    # Test setup file (jest-dom matchers)
├── __tests__/                         # Test files (co-located alternative)
│   └── components/
│       └── events/
│           └── FeedbackButtons.test.tsx
├── components/
│   ├── settings/
│   │   ├── HomeKitSettings.tsx       # HomeKit enable/disable, QR code display
│   │   └── CameraDiscovery.tsx       # ONVIF discovery UI, one-click add
│   └── cameras/
│       └── ZonePresets.tsx           # Detection zone preset templates

.github/
└── workflows/
    └── ci.yml                         # GitHub Actions workflow for PR checks

docs/
└── performance-baselines.md           # CPU/memory benchmarks for reference configs
```

---

## Phase 5 Database Schema Additions

### HomeKit Pairings Table

```sql
-- Stores HomeKit pairing state (HAP-python manages most state in files)
CREATE TABLE homekit_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enabled BOOLEAN DEFAULT FALSE,
    bridge_name VARCHAR(64) DEFAULT 'ArgusAI',
    pin_code VARCHAR(10),  -- Setup code (encrypted), e.g., "123-45-678"
    port INTEGER DEFAULT 51826,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maps ArgusAI cameras to HomeKit accessory IDs
CREATE TABLE homekit_accessories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id VARCHAR(36) REFERENCES cameras(id),
    accessory_aid INTEGER NOT NULL,  -- HAP accessory ID
    accessory_type VARCHAR(32) NOT NULL,  -- 'camera', 'motion', 'occupancy', 'doorbell'
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Detection Schedule Extensions

```sql
-- Add support for multiple time ranges per day
CREATE TABLE detection_schedule_ranges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id VARCHAR(36) REFERENCES cameras(id),
    day_of_week INTEGER NOT NULL,  -- 0=Sunday, 6=Saturday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(camera_id, day_of_week, start_time)
);
```

### Detection Zone Presets

```sql
-- Predefined zone templates
CREATE TABLE zone_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    points JSON NOT NULL,  -- Normalized coordinates [[x,y], ...]
    is_system BOOLEAN DEFAULT FALSE  -- TRUE for built-in presets
);

-- Default presets (inserted via migration)
-- Rectangle: [[0,0], [1,0], [1,1], [0,1]]
-- Top Half: [[0,0], [1,0], [1,0.5], [0,0.5]]
-- Bottom Half: [[0,0.5], [1,0.5], [1,1], [0,1]]
-- Center: [[0.25,0.25], [0.75,0.25], [0.75,0.75], [0.25,0.75]]
-- L-shape: [[0,0], [0.5,0], [0.5,0.5], [1,0.5], [1,1], [0,1]]
```

---

## Phase 5 HomeKit Architecture

### HAP Bridge Design

```
┌─────────────────────────────────────────────────────────────┐
│                    HomeKit Bridge                            │
│                   (HAP-python Driver)                        │
├─────────────────────────────────────────────────────────────┤
│  Bridge Accessory (AID=1)                                   │
│  └── Accessory Information Service                          │
├─────────────────────────────────────────────────────────────┤
│  Camera Accessory (AID=2+)          Per configured camera   │
│  ├── Accessory Information                                  │
│  ├── Camera RTP Stream Management   Live streaming          │
│  └── Microphone (optional)          If camera has audio     │
├─────────────────────────────────────────────────────────────┤
│  Motion Sensor (AID per camera)     Triggers on any motion  │
│  └── Motion Detected: true/false                            │
├─────────────────────────────────────────────────────────────┤
│  Occupancy Sensor (AID per camera)  Person detection only   │
│  └── Occupancy Detected: true/false (with timeout)          │
├─────────────────────────────────────────────────────────────┤
│  Doorbell (AID for Protect doorbells)                       │
│  └── Programmable Switch Event: Single Press                │
└─────────────────────────────────────────────────────────────┘
```

### Camera Streaming Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  RTSP Camera │────▶│   ffmpeg     │────▶│  HomeKit     │
│  (H.264)     │     │  transcoder  │     │  Client      │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                     ┌──────┴──────┐
                     │ HLS/SRTP    │
                     │ H.264 720p  │
                     │ AAC Audio   │
                     └─────────────┘
```

**Transcoding Command (HAP-python default):**
```bash
ffmpeg -re -i {rtsp_url} \
  -vcodec libx264 -pix_fmt yuv420p \
  -r 30 -f rawvideo \
  -tune zerolatency \
  -vf scale=1280:720 \
  -b:v 299k -bufsize 299k \
  -payload_type 99 \
  -ssrc {video_ssrc} \
  -f rtp -srtp_out_suite AES_CM_128_HMAC_SHA1_80 \
  -srtp_out_params {video_key} \
  srtp://{target}:{video_port}?rtcpport={video_port}&pkt_size=1316
```

### Sensor State Management

```python
# Sensor update flow
Event Detected (ArgusAI)
    │
    ▼
homekit_service.update_sensor_state(camera_id, event_type)
    │
    ├── event_type == 'person' → Update OccupancySensor (occupied=True)
    │                            └── Start 5-minute timeout
    │
    ├── event_type in ['motion', 'vehicle', 'animal', 'package']
    │   └── Update MotionSensor (motion_detected=True)
    │       └── Auto-reset after 3 seconds
    │
    └── event_type == 'doorbell_ring'
        └── Trigger Doorbell.set_value(0)  # Single press event
```

---

## Phase 5 ONVIF Discovery Architecture

### WS-Discovery Flow

```
┌─────────────┐                    ┌─────────────────┐
│   ArgusAI   │                    │  ONVIF Camera   │
│   Backend   │                    │  (Network)      │
└──────┬──────┘                    └────────┬────────┘
       │                                    │
       │  1. WS-Discovery Probe (UDP)       │
       │  ────────────────────────────────▶ │
       │  To: 239.255.255.250:3702          │
       │                                    │
       │  2. ProbeMatch Response            │
       │  ◀──────────────────────────────── │
       │  Contains: XAddrs (device URL)     │
       │                                    │
       │  3. GetDeviceInformation           │
       │  ────────────────────────────────▶ │
       │  SOAP to device service URL        │
       │                                    │
       │  4. Device Info Response           │
       │  ◀──────────────────────────────── │
       │  Model, Manufacturer, FirmwareVer  │
       │                                    │
       │  5. GetProfiles                    │
       │  ────────────────────────────────▶ │
       │  SOAP to media service URL         │
       │                                    │
       │  6. Media Profiles Response        │
       │  ◀──────────────────────────────── │
       │  Stream URIs, resolutions          │
       │                                    │
```

### Discovery Service Implementation

```python
# backend/app/services/onvif_discovery_service.py

class ONVIFDiscoveryService:
    """
    Discovers ONVIF-compatible cameras on local network.
    Uses WS-Discovery protocol (UDP multicast).
    """

    DISCOVERY_TIMEOUT = 10  # seconds
    MULTICAST_GROUP = "239.255.255.250"
    MULTICAST_PORT = 3702

    async def discover_cameras(self) -> List[DiscoveredCamera]:
        """
        Scan network for ONVIF cameras.
        Returns list of discovered cameras with metadata.
        """
        # 1. Send WS-Discovery probe
        # 2. Collect responses (with timeout)
        # 3. Query each device for details
        # 4. Extract RTSP stream URLs
        # 5. Return normalized results

    async def get_camera_details(self, device_url: str) -> CameraDetails:
        """
        Query specific camera for full details.
        Requires credentials for authenticated cameras.
        """

    async def test_connection(self, rtsp_url: str,
                              username: str = None,
                              password: str = None) -> TestResult:
        """
        Test RTSP connection without saving camera.
        Returns success/failure with diagnostic info.
        """
```

---

## Phase 5 CI/CD Architecture

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, development]
  pull_request:
    branches: [main, development]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run linting
        run: ruff check .

      - name: Run tests with coverage
        run: |
          pytest --cov=app --cov-report=xml --cov-report=term-missing
        env:
          DATABASE_URL: sqlite:///./test.db
          ENCRYPTION_KEY: ${{ secrets.TEST_ENCRYPTION_KEY }}

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: backend

  frontend-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run linting
        run: npm run lint

      - name: Type check
        run: npx tsc --noEmit

      - name: Run tests with coverage
        run: npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
          flags: frontend
```

### Frontend Test Configuration

```typescript
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    include: ['**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'lcov'],
      exclude: ['node_modules/', '**/*.d.ts', 'vitest.*.ts']
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './')
    }
  }
})
```

```typescript
// frontend/vitest.setup.ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
```

---

## Phase 5 API Additions

### HomeKit Endpoints

```
POST   /api/v1/homekit/enable           # Enable HomeKit bridge
POST   /api/v1/homekit/disable          # Disable HomeKit bridge
GET    /api/v1/homekit/status           # Get bridge status, pairing info
GET    /api/v1/homekit/qrcode           # Get pairing QR code (PNG)
GET    /api/v1/homekit/accessories      # List all accessories
PUT    /api/v1/homekit/accessories/{id} # Enable/disable accessory
DELETE /api/v1/homekit/pairings/{id}    # Remove a pairing
```

**HomeKit Status Response:**
```json
{
  "enabled": true,
  "bridge_name": "ArgusAI",
  "paired": true,
  "paired_clients": 2,
  "accessories": [
    {
      "aid": 2,
      "name": "Front Door Camera",
      "type": "camera",
      "camera_id": "abc-123",
      "enabled": true
    },
    {
      "aid": 3,
      "name": "Front Door Motion",
      "type": "motion_sensor",
      "camera_id": "abc-123",
      "enabled": true
    }
  ],
  "port": 51826,
  "setup_uri": "X-HM://..."
}
```

### Camera Discovery Endpoints

```
POST   /api/v1/cameras/discover         # Trigger ONVIF discovery scan
GET    /api/v1/cameras/discover/results # Get discovery results (poll)
POST   /api/v1/cameras/test             # Test connection (no save)
```

**Discovery Response:**
```json
{
  "status": "complete",
  "duration_ms": 8234,
  "cameras": [
    {
      "name": "IPC-HDW2431T",
      "manufacturer": "Dahua",
      "model": "IPC-HDW2431T-AS-S2",
      "ip_address": "192.168.1.100",
      "rtsp_url": "rtsp://192.168.1.100:554/cam/realmonitor?channel=1&subtype=0",
      "requires_auth": true,
      "profiles": [
        {"name": "mainStream", "resolution": "2688x1520", "fps": 25},
        {"name": "subStream", "resolution": "704x480", "fps": 25}
      ]
    }
  ]
}
```

**Test Connection Request/Response:**
```json
// Request
{
  "rtsp_url": "rtsp://192.168.1.100:554/stream",
  "username": "admin",
  "password": "password123"
}

// Response
{
  "success": true,
  "latency_ms": 234,
  "resolution": "1920x1080",
  "fps": 30,
  "codec": "H.264"
}
```

---

## Phase 5 Implementation Patterns

### HomeKit Event Integration

```python
# Integration with existing event pipeline
# backend/app/services/event_processor.py

async def process_event(self, event: Event):
    # ... existing processing ...

    # Notify HomeKit sensors (Phase 5)
    if self.homekit_service.is_enabled():
        await self.homekit_service.notify_event(
            camera_id=event.camera_id,
            event_type=event.smart_detection_type or 'motion',
            is_doorbell=event.is_doorbell_ring
        )
```

### Accessibility Patterns

```typescript
// Pattern for accessible interactive components
// All Phase 5 UI components must follow this pattern

interface AccessibleButtonProps {
  onClick: () => void;
  label: string;  // Always required for screen readers
  description?: string;  // Optional extended description
  disabled?: boolean;
}

export function AccessibleButton({
  onClick,
  label,
  description,
  disabled = false
}: AccessibleButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      aria-describedby={description ? 'btn-desc' : undefined}
      className="focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
    >
      {label}
      {description && (
        <span id="btn-desc" className="sr-only">{description}</span>
      )}
    </button>
  );
}
```

### Zone Preset Application

```typescript
// Pattern for applying zone presets
// frontend/components/cameras/ZonePresets.tsx

const ZONE_PRESETS = {
  rectangle: { name: "Full Frame", points: [[0,0], [1,0], [1,1], [0,1]] },
  top_half: { name: "Top Half", points: [[0,0], [1,0], [1,0.5], [0,0.5]] },
  bottom_half: { name: "Bottom Half", points: [[0,0.5], [1,0.5], [1,1], [0,1]] },
  center: { name: "Center", points: [[0.25,0.25], [0.75,0.25], [0.75,0.75], [0.25,0.75]] },
  l_shape: { name: "L-Shape", points: [[0,0], [0.5,0], [0.5,0.5], [1,0.5], [1,1], [0,1]] }
};

function applyPreset(presetKey: string, canvasWidth: number, canvasHeight: number) {
  const preset = ZONE_PRESETS[presetKey];
  return preset.points.map(([x, y]) => ({
    x: x * canvasWidth,
    y: y * canvasHeight
  }));
}
```

---

## Phase 5 Performance Considerations

**HomeKit Streaming:**
- Target: <500ms additional latency
- ffmpeg transcoding runs as subprocess
- Limit concurrent streams (default: 2)
- Use hardware encoding if available (vaapi, nvenc)

**ONVIF Discovery:**
- Target: <10 seconds for full scan
- Parallel device queries (max 10 concurrent)
- Timeout per device: 2 seconds
- Cache discovery results for 5 minutes

**CI Pipeline:**
- Target: <10 minutes total
- Parallel backend/frontend jobs
- Dependency caching enabled
- Skip unchanged paths (future optimization)

---

## Phase 5 Validation Checklist

- [ ] PRD Phase 5 functional requirements have architectural support
- [ ] HomeKit bridge architecture supports all accessory types (FR1-FR12)
- [ ] ONVIF discovery handles WS-Discovery protocol (FR13-FR19)
- [ ] CI/CD pipeline covers all required checks (FR20-FR26)
- [ ] Performance validation methodology documented (FR27-FR30)
- [ ] Accessibility patterns defined for all new UI (FR31-FR36)
- [ ] MQTT enhancements integrated with existing service (FR37-FR38)
- [ ] Database schema supports HomeKit pairings and zone presets
- [ ] API contracts defined for all new endpoints
- [ ] Integration points with existing event pipeline defined

---

**Phase 5 Architecture Update:**
- **Updated by:** Claude Code
- **Date:** 2025-12-14
- **PRD Reference:** `docs/PRD-phase5.md`
