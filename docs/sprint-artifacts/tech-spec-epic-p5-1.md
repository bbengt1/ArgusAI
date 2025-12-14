# Epic Technical Specification: Native HomeKit Integration

Date: 2025-12-14
Author: Brent
Epic ID: P5-1
Status: Draft

---

## Overview

Epic P5-1 implements native HomeKit integration for ArgusAI, enabling Apple ecosystem users to view camera streams and receive motion/doorbell notifications directly in the Apple Home app without requiring Home Assistant as middleware.

This epic leverages HAP-python to implement the HomeKit Accessory Protocol (HAP), creating a bridge that exposes ArgusAI cameras as HomeKit Camera accessories with associated Motion Sensors, Occupancy Sensors, and Doorbell accessories. The integration runs independently of the web UI, ensuring HomeKit remains responsive even when the dashboard isn't in use.

**PRD Reference:** docs/PRD-phase5.md (FR1-FR12, NFR1-NFR2, NFR4, NFR6-NFR9, NFR12-NFR13, NFR16-NFR17)

## Objectives and Scope

**In Scope:**
- HAP-python bridge initialization and lifecycle management
- HomeKit pairing via QR code and manual PIN
- Camera accessories with RTSP-to-SRTP streaming via ffmpeg
- Motion Sensor accessories triggered by ArgusAI motion detection
- Occupancy Sensor accessories for person detection (with 5-minute timeout)
- Vehicle/Animal/Package detection triggering motion sensors
- Doorbell accessory for Protect doorbell ring events
- HomeKit Settings UI (enable/disable, QR code, pairing management)
- Persistence of HomeKit state across restarts
- Multi-user HomeKit access (shared accessories)

**Out of Scope:**
- HomeKit Secure Video (HKSV) with iCloud recording - future phase
- Audio streaming from cameras (video only in P5-1)
- Custom HomeKit scenes or automation configuration
- Two-way audio for doorbells

## System Architecture Alignment

**Architecture Reference:** docs/architecture/phase-5-additions.md

This epic aligns with the Phase 5 HomeKit Architecture section:
- **HAP Bridge Design** - Bridge accessory (AID=1) with camera, motion, occupancy, and doorbell accessories
- **Camera Streaming Pipeline** - RTSP → ffmpeg → SRTP to HomeKit clients
- **Sensor State Management** - Event processor integration for sensor updates
- **Database Schema** - homekit_config and homekit_accessories tables

**Key Integration Points:**
- `event_processor.py` - Notify HomeKit sensors on event detection
- `camera_service.py` - Provide RTSP URLs for camera streaming
- `protect_event_handler.py` - Source doorbell ring events

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs |
|---------------|----------------|--------|---------|
| `homekit_service.py` | HAP bridge lifecycle, accessory management | Camera configs, events | HomeKit state updates |
| `homekit_camera.py` | Camera accessory with streaming | RTSP URL, credentials | SRTP stream to HomeKit |
| `homekit_sensors.py` | Motion, occupancy, doorbell accessories | Event notifications | HAP characteristic updates |
| `api/v1/homekit.py` | REST endpoints for HomeKit management | HTTP requests | JSON responses |

### Data Models and Contracts

**HomeKit Config Model (SQLAlchemy):**
```python
class HomeKitConfig(Base):
    __tablename__ = "homekit_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    enabled: Mapped[bool] = mapped_column(default=False)
    bridge_name: Mapped[str] = mapped_column(String(64), default="ArgusAI")
    pin_code: Mapped[str] = mapped_column(String(10), nullable=True)  # Encrypted
    port: Mapped[int] = mapped_column(default=51826)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
```

**HomeKit Accessories Model:**
```python
class HomeKitAccessory(Base):
    __tablename__ = "homekit_accessories"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id"))
    accessory_aid: Mapped[int] = mapped_column(nullable=False)
    accessory_type: Mapped[str] = mapped_column(String(32))  # camera, motion, occupancy, doorbell
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    camera = relationship("Camera", back_populates="homekit_accessories")
```

### APIs and Interfaces

**HomeKit API Endpoints:**

| Method | Path | Request | Response | Description |
|--------|------|---------|----------|-------------|
| POST | /api/v1/homekit/enable | - | `{"enabled": true, "setup_uri": "..."}` | Enable bridge, return pairing URI |
| POST | /api/v1/homekit/disable | - | `{"enabled": false}` | Disable bridge |
| GET | /api/v1/homekit/status | - | HomeKitStatus | Bridge status, accessories |
| GET | /api/v1/homekit/qrcode | - | PNG image | Pairing QR code |
| GET | /api/v1/homekit/accessories | - | `[Accessory]` | List all accessories |
| PUT | /api/v1/homekit/accessories/{id} | `{"enabled": bool}` | Accessory | Enable/disable accessory |
| DELETE | /api/v1/homekit/pairings/{id} | - | - | Remove pairing |

**HomeKitStatus Schema:**
```json
{
  "enabled": true,
  "bridge_name": "ArgusAI",
  "paired": true,
  "paired_clients": 2,
  "port": 51826,
  "setup_uri": "X-HM://...",
  "accessories": [
    {
      "id": 1,
      "aid": 2,
      "name": "Front Door Camera",
      "type": "camera",
      "camera_id": "abc-123",
      "enabled": true
    }
  ]
}
```

### Workflows and Sequencing

**Bridge Startup Sequence:**
```
1. Backend startup
2. Load HomeKitConfig from database
3. If enabled:
   a. Initialize HAP AccessoryDriver
   b. Load persisted state from backend/homekit/accessory.state
   c. Create Bridge accessory (AID=1)
   d. For each enabled camera:
      - Create Camera accessory
      - Create Motion Sensor accessory
      - Create Occupancy Sensor accessory
      - If doorbell camera: Create Doorbell accessory
   e. Start HAP driver (async)
4. Register shutdown handler for cleanup
```

**Event → Sensor Update Flow:**
```
1. Event detected in event_processor.py
2. Check if homekit_service.is_enabled()
3. Call homekit_service.notify_event(camera_id, event_type, is_doorbell)
4. HomeKit service:
   a. If event_type == 'person':
      - Set OccupancySensor.occupancy_detected = True
      - Schedule reset after 5 minutes
   b. If event_type in ['motion', 'vehicle', 'animal', 'package']:
      - Set MotionSensor.motion_detected = True
      - Schedule reset after 3 seconds
   c. If is_doorbell:
      - Trigger Doorbell programmable switch event
5. HAP-python broadcasts characteristic change to paired clients
```

**Camera Streaming Flow:**
```
1. HomeKit client requests stream (RTP session)
2. HAP-python calls Camera.start_stream(session_info)
3. homekit_camera.py:
   a. Get RTSP URL for camera
   b. Spawn ffmpeg subprocess with transcoding command
   c. ffmpeg streams SRTP to HomeKit client address
4. On stop_stream:
   a. Terminate ffmpeg subprocess
   b. Clean up resources
```

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Stream latency | <500ms additional | End-to-end from RTSP source to Home app |
| Sensor update propagation | <2 seconds | Time from ArgusAI event to Home app notification |
| Bridge startup | <30 seconds | Time from backend start to HAP ready |
| CPU usage (streaming) | <50% average | Single camera stream active |

### Security

- **SRP Protocol** - HomeKit pairing uses Secure Remote Password per HAP spec (NFR7)
- **ChaCha20-Poly1305** - All HomeKit communication encrypted (NFR8)
- **PIN Security** - Setup code not logged after initial pairing (NFR9)
- **State File Protection** - `backend/homekit/accessory.state` contains pairing keys, restrict file permissions

### Reliability/Availability

- **Auto-reconnect** - HAP driver handles network interruptions (NFR12)
- **Persistence** - Pairings survive restarts via accessory.state file (NFR13)
- **Independent operation** - Bridge runs in background thread, not dependent on web UI

### Observability

- **Logging** - HAP events logged at INFO level (pairing, streaming start/stop)
- **Metrics** - `homekit_paired_clients`, `homekit_active_streams`, `homekit_sensor_updates_total`
- **Health endpoint** - `/api/v1/homekit/status` includes bridge health

## Dependencies and Integrations

### Python Dependencies (backend/requirements.txt additions)

| Package | Version | Purpose |
|---------|---------|---------|
| HAP-python | >=4.9.0 | HomeKit Accessory Protocol implementation |
| zeroconf | >=0.131.0 | mDNS/Bonjour for HomeKit discovery |
| cryptography | >=41.0.0 | HAP encryption (already installed) |
| qrcode | >=7.4.0 | QR code generation for pairing |
| Pillow | >=10.0.0 | Image processing for QR codes |

### System Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| ffmpeg | >=6.0 | RTSP to SRTP transcoding |

### Internal Integrations

| Component | Integration Point | Data Flow |
|-----------|-------------------|-----------|
| event_processor.py | `notify_event()` call | Events → HomeKit sensors |
| camera_service.py | `get_rtsp_url()` | Camera config → Streaming |
| protect_event_handler.py | Doorbell events | Ring events → Doorbell accessory |

## Acceptance Criteria (Authoritative)

**Story P5-1.1: HAP-python Bridge Infrastructure**
1. HAP-python installed and importable in backend environment
2. Bridge accessory initializes on backend startup when enabled
3. State persists in `backend/homekit/` directory across restarts
4. Bridge runs in background, responsive when web UI closed

**Story P5-1.2: HomeKit Pairing with QR Code**
1. Setup code generated in XXX-XX-XXX format on first enable
2. QR code PNG returned from `/api/v1/homekit/qrcode`
3. Pairing completes successfully with Apple Home app
4. PIN not logged or stored in plain text

**Story P5-1.3: Camera Accessory with Streaming**
1. Each enabled camera appears as Camera accessory in Home app
2. Live stream viewable with <500ms additional latency
3. ffmpeg process started/stopped correctly per stream request
4. Multiple cameras can stream simultaneously (up to 2 concurrent)

**Story P5-1.4: Motion Sensor Accessories**
1. Motion sensor accessory created for each camera
2. Sensor triggers within 2 seconds of ArgusAI motion detection
3. State auto-resets after 3 seconds
4. HomeKit automations can trigger on motion

**Story P5-1.5: Occupancy Sensor for Person Detection**
1. Occupancy sensor separate from motion sensor
2. Only triggers on person detection events
3. Occupancy state has 5-minute timeout before reset
4. Distinct icon in Home app

**Story P5-1.6: Vehicle/Animal/Package Sensors**
1. Vehicle detection triggers motion sensor
2. Animal detection triggers motion sensor
3. Package detection triggers motion sensor
4. Each can trigger separate HomeKit automations

**Story P5-1.7: Doorbell Accessory**
1. Doorbell accessory appears for Protect doorbell cameras
2. Ring events trigger doorbell notification
3. Notification appears on all paired iOS devices
4. Can trigger HomeKit automations

**Story P5-1.8: HomeKit Settings UI**
1. Toggle to enable/disable HomeKit bridge
2. QR code displayed when enabled and not paired
3. List of current pairings with remove option
4. Status shows connected/disconnected state

## Traceability Mapping

| AC | Spec Section | Component/API | Test Idea |
|----|--------------|---------------|-----------|
| P5-1.1-1 | Dependencies | requirements.txt | Import test |
| P5-1.1-2 | Workflows | homekit_service.py | Startup integration test |
| P5-1.1-3 | Data Models | backend/homekit/ | Restart persistence test |
| P5-1.1-4 | Architecture | Background thread | UI-closed operation test |
| P5-1.2-1 | Data Models | HomeKitConfig | PIN format validation |
| P5-1.2-2 | APIs | /api/v1/homekit/qrcode | QR endpoint test |
| P5-1.2-3 | Workflows | HAP pairing | Manual pairing test |
| P5-1.2-4 | Security | Logging config | Log audit for PIN |
| P5-1.3-1 | Data Models | HomeKitAccessory | Camera enumeration test |
| P5-1.3-2 | Performance | Streaming pipeline | Latency measurement |
| P5-1.3-3 | Workflows | ffmpeg lifecycle | Stream start/stop test |
| P5-1.3-4 | Performance | Concurrent streams | Multi-stream test |
| P5-1.4-1 | Data Models | Motion sensor | Accessory creation test |
| P5-1.4-2 | Performance | Event propagation | Timing measurement |
| P5-1.4-3 | Workflows | Sensor reset | Timeout verification |
| P5-1.4-4 | Integration | HomeKit automations | Manual automation test |
| P5-1.5-1 | Data Models | Occupancy sensor | Separate accessory test |
| P5-1.5-2 | Workflows | Event filtering | Person-only trigger test |
| P5-1.5-3 | Workflows | Timeout logic | 5-minute timeout test |
| P5-1.5-4 | UI | Home app | Visual verification |
| P5-1.6-1 | Workflows | Event routing | Vehicle trigger test |
| P5-1.6-2 | Workflows | Event routing | Animal trigger test |
| P5-1.6-3 | Workflows | Event routing | Package trigger test |
| P5-1.6-4 | Integration | HomeKit automations | Separate automation test |
| P5-1.7-1 | Data Models | Doorbell accessory | Accessory creation test |
| P5-1.7-2 | Workflows | Ring event | Notification trigger test |
| P5-1.7-3 | Integration | iOS notification | Multi-device test |
| P5-1.7-4 | Integration | HomeKit automations | Ring automation test |
| P5-1.8-1 | APIs | /api/v1/homekit/enable | Toggle endpoint test |
| P5-1.8-2 | UI | HomeKitSettings.tsx | QR display test |
| P5-1.8-3 | APIs | /api/v1/homekit/pairings | Pairing list test |
| P5-1.8-4 | APIs | /api/v1/homekit/status | Status response test |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1: ffmpeg availability** - ffmpeg must be installed on host system; provide installation docs
- **R2: Network port conflicts** - HAP uses port 51826 by default; make configurable
- **R3: Camera streaming CPU** - Multiple concurrent streams may exceed CPU capacity; enforce limits

**Assumptions:**
- **A1:** Users have Apple Home hub (Apple TV, HomePod) for remote access
- **A2:** Cameras provide H.264 RTSP streams (most common format)
- **A3:** ffmpeg 6.0+ available on Linux/macOS deployment targets
- **A4:** HAP-python 4.9+ stable for production use

**Open Questions:**
- **Q1:** Should we support hardware video encoding (vaapi, nvenc)? → Defer to growth phase
- **Q2:** Maximum concurrent streams? → Start with 2, evaluate performance
- **Q3:** Should doorbell show camera stream or just ring? → Just ring initially, camera via separate accessory

## Test Strategy Summary

**Unit Tests:**
- `test_homekit_service.py` - Bridge lifecycle, accessory creation
- `test_homekit_sensors.py` - Sensor state management, timeouts
- Mock HAP-python driver for isolated testing

**Integration Tests:**
- Bridge startup with real HAP driver (local only, no pairing)
- Event processor → HomeKit sensor notification flow
- API endpoint tests for all HomeKit routes

**Manual Tests (Required):**
- Full pairing flow with Apple Home app
- Live streaming verification in Home app
- Motion/occupancy sensor triggering
- Doorbell ring notification
- Multi-device notification delivery

**Test Environment:**
- ffmpeg installed in CI (ubuntu-latest has it)
- SQLite test database
- Mock camera RTSP URLs for streaming tests
