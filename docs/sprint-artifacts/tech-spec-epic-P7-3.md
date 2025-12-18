# Epic Technical Specification: HomeKit Camera Streaming

Date: 2025-12-17
Author: Brent
Epic ID: P7-3
Status: Draft

---

## Overview

Epic P7-3 ensures HomeKit camera streaming works reliably in Apple Home app. Phase 5 added camera accessories with RTSP-to-SRTP transcoding via ffmpeg, but this epic verifies the implementation, fixes any compatibility issues, adds snapshot support for camera tiles, and provides streaming diagnostics. The goal is for users to see live camera previews and full streams directly in Apple Home app without external apps.

The implementation builds upon the existing HomeKit camera accessory (`backend/app/services/homekit_camera.py`) and HomeKit service (`backend/app/services/homekit_service.py`) established in Phase 5.

## Objectives and Scope

### In Scope
- Test and verify camera preview works in Apple Home app
- Verify ffmpeg transcoding pipeline (RTSP → SRTP)
- Fix any codec/resolution compatibility issues
- Support multiple concurrent streams (up to 2)
- Add stream quality configuration (low/medium/high)
- Implement get_snapshot() for camera tiles
- Return JPEG snapshot from camera
- Cache snapshot for 5 seconds to reduce load
- Handle camera offline gracefully (return placeholder)
- Log stream start/stop events
- Show active streams in HomeKit status panel
- Display ffmpeg command for debugging
- Add stream test button in camera settings

### Out of Scope
- Two-way audio communication
- Motion zone overlays in stream
- Picture-in-picture support
- Recording in Apple Home app (controlled by Apple)
- HomeKit Secure Video (HSV) integration

## System Architecture Alignment

This epic aligns with the Phase 5 HomeKit camera architecture:

**Components Modified:**
- `backend/app/services/homekit_camera.py` - Fix streaming, add snapshots
- `backend/app/services/homekit_service.py` - Stream monitoring, diagnostics
- `backend/app/api/v1/homekit.py` - Streaming diagnostics endpoint
- `frontend/components/settings/HomeKitSettings.tsx` - Stream status, test button

**Architecture Constraints:**
- ffmpeg 6.0+ required for SRTP output
- Camera must support H.264 codec (or ffmpeg transcodes)
- Maximum 2 concurrent streams per camera (iOS limitation)
- HAP-python handles SRTP negotiation via HAP protocol

**Streaming Pipeline:**
```
RTSP Camera (H.264) → ffmpeg → SRTP (H.264 720p) → HomeKit Client
      ↓                 ↓              ↓                ↓
  Source video    Transcoding    Encrypted      Apple Home/iOS
  H.264/H.265     Scale to 720p  AES-128        Live preview
```

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs |
|----------------|----------------|--------|---------|
| `HomeKitCameraAccessory` | Camera streaming via HAP | RTSP URL | SRTP stream |
| `CameraSnapshotService` | Generate/cache snapshots | Camera ID | JPEG bytes |
| `StreamMonitor` | Track active streams | Stream events | Status data |
| `HomeKitSettings` | Display stream diagnostics | API response | Rendered UI |

### Data Models and Contracts

**StreamQuality enum:**
```python
class StreamQuality(str, Enum):
    LOW = "low"      # 480p, 15fps, 500kbps
    MEDIUM = "medium"  # 720p, 25fps, 1500kbps
    HIGH = "high"    # 1080p, 30fps, 3000kbps
```

**StreamConfig dataclass:**
```python
@dataclass
class StreamConfig:
    quality: StreamQuality = StreamQuality.MEDIUM
    max_concurrent_streams: int = 2
    snapshot_cache_seconds: int = 5
    ffmpeg_extra_args: Optional[str] = None
```

**ActiveStream tracking:**
```python
@dataclass
class ActiveStream:
    camera_id: str
    session_id: str
    start_time: datetime
    client_address: str
    resolution: str
    fps: int
    bitrate: int
```

**CameraAccessory extensions:**
```python
class HomeKitCameraAccessory:
    # Existing fields...
    snapshot_cache: Optional[bytes] = None
    snapshot_timestamp: Optional[datetime] = None
    active_streams: List[ActiveStream] = field(default_factory=list)
```

### APIs and Interfaces

**Updated: GET /api/v1/homekit/status**

Include streaming information:

```json
{
  "enabled": true,
  "running": true,
  "camera_count": 3,
  "active_streams": 2,
  "ffmpeg_available": true,
  "stream_diagnostics": {
    "cameras": [
      {
        "camera_id": "abc-123",
        "camera_name": "Front Door",
        "streaming_enabled": true,
        "snapshot_supported": true,
        "last_snapshot": "2025-12-17T14:30:00Z",
        "active_streams": 1,
        "quality": "medium"
      }
    ]
  }
}
```

**New: POST /api/v1/homekit/cameras/{camera_id}/test-stream**

Test stream capability:

```
POST /api/v1/homekit/cameras/abc-123/test-stream

Response 200:
{
  "success": true,
  "rtsp_accessible": true,
  "ffmpeg_compatible": true,
  "source_resolution": "1920x1080",
  "source_fps": 30,
  "source_codec": "h264",
  "target_resolution": "1280x720",
  "target_fps": 25,
  "target_bitrate": 1500,
  "estimated_latency_ms": 500,
  "ffmpeg_command": "ffmpeg -i rtsp://... -vcodec libx264 ..."
}
```

**New: GET /api/v1/homekit/cameras/{camera_id}/snapshot**

Get camera snapshot (for testing):

```
GET /api/v1/homekit/cameras/abc-123/snapshot

Response 200:
Content-Type: image/jpeg
[JPEG bytes]

Response 503 (camera offline):
{
  "detail": "Camera offline",
  "placeholder_available": true
}
```

**Updated: PUT /api/v1/cameras/{camera_id}**

Add stream quality configuration:

```json
{
  "name": "Front Door",
  "rtsp_url": "rtsp://...",
  "homekit_stream_quality": "high"  // New field
}
```

### Workflows and Sequencing

**Stream Request Flow:**
```
1. iOS Home app requests camera stream
      ↓
2. HAP-python receives RTPStreamManagement request
      ↓
3. HomeKitCameraAccessory.start_stream() called
      ↓
4. Check concurrent stream limit (max 2)
   If exceeded: reject with "resource busy"
      ↓
5. Spawn ffmpeg subprocess:
   ffmpeg -i {rtsp_url} -vcodec libx264 -pix_fmt yuv420p
          -r {fps} -vf scale={width}:{height}
          -b:v {bitrate}k -bufsize {bitrate}k
          -payload_type 99 -ssrc {video_ssrc}
          -f rtp -srtp_out_suite AES_CM_128_HMAC_SHA1_80
          -srtp_out_params {video_key}
          srtp://{target}:{port}?rtcpport={port}&pkt_size=1316
      ↓
6. Track stream in active_streams list
      ↓
7. Log stream start event
      ↓
8. On stream end: cleanup subprocess, remove from list, log stop
```

**Snapshot Request Flow:**
```
1. iOS Home app requests snapshot (for tile preview)
      ↓
2. HomeKitCameraAccessory.get_snapshot() called
      ↓
3. Check cache:
   If cached and < 5 seconds old: return cached
      ↓
4. Capture snapshot from camera:
   - RTSP camera: single frame grab via ffmpeg
   - Protect camera: use existing snapshot API
      ↓
5. Convert to JPEG, resize to 640x480 max
      ↓
6. Cache snapshot bytes with timestamp
      ↓
7. Return JPEG bytes
      ↓
8. On camera offline: return placeholder image
```

**Quality Selection:**
```
Quality   Resolution  FPS   Bitrate
low       640x480     15    500 kbps
medium    1280x720    25    1500 kbps
high      1920x1080   30    3000 kbps
```

## Non-Functional Requirements

### Performance

- Snapshot capture: < 2 seconds (cached: < 50ms)
- Stream start latency: < 3 seconds from request to first frame
- ffmpeg memory usage: < 100MB per stream
- Maximum concurrent streams: 2 per camera, 10 total for bridge

### Security

- SRTP encryption mandatory (AES-128)
- No plain RTP streams allowed
- Camera credentials never exposed to HomeKit clients
- Snapshot requests require authentication

### Reliability/Availability

- ffmpeg process crash recovery (auto-restart stream)
- Camera offline detection with placeholder image
- Graceful stream termination on client disconnect
- Resource cleanup on service shutdown

### Observability

- Log stream start/stop with session details
- Prometheus metrics: `argusai_homekit_streams_active`, `argusai_homekit_snapshots_total`
- ffmpeg stderr captured for debugging
- Stream latency/bitrate monitoring

## Dependencies and Integrations

| Dependency | Version | Purpose |
|------------|---------|---------|
| ffmpeg | 6.0+ | RTSP to SRTP transcoding |
| HAP-python | 4.9+ | HomeKit camera accessory |
| Pillow | 10.0+ | Image processing for snapshots |

**Integration Points:**
- Camera service (existing) - RTSP URL access
- Protect service (existing) - Protect camera snapshots
- HomeKit service (existing) - accessory management
- Settings UI - stream configuration

## Acceptance Criteria (Authoritative)

### Story P7-3.1: Verify RTSP-to-SRTP Streaming Works
1. Camera preview works in Apple Home app
2. ffmpeg transcoding pipeline verified
3. Codec/resolution compatibility issues fixed
4. Multiple concurrent streams supported (up to 2)
5. Stream quality configuration added (low/medium/high)

### Story P7-3.2: Add Camera Snapshot Support
1. get_snapshot() method implemented in camera accessory
2. JPEG snapshot returned from camera
3. Snapshot cached for 5 seconds
4. Camera offline returns placeholder gracefully

### Story P7-3.3: Add Camera Streaming Diagnostics
1. Stream start/stop events logged
2. Active streams shown in HomeKit status panel
3. ffmpeg command displayed for debugging
4. Stream test button added in camera settings

## Traceability Mapping

| AC# | Spec Section | Component/API | Test Idea |
|-----|--------------|---------------|-----------|
| P7-3.1-1 | Workflows / Stream Request | HomeKitCameraAccessory | Manual: view camera in Home app |
| P7-3.1-2 | Workflows / Stream Request | ffmpeg subprocess | Integration: verify ffmpeg command |
| P7-3.1-3 | Detailed Design / StreamConfig | ffmpeg args | Unit: test different codec handling |
| P7-3.1-4 | NFRs / Performance | concurrent streams | Integration: start 2 streams simultaneously |
| P7-3.1-5 | Data Models / StreamQuality | Camera config | Unit: verify quality settings |
| P7-3.2-1 | Workflows / Snapshot | get_snapshot() | Unit: mock camera, verify JPEG returned |
| P7-3.2-2 | Workflows / Snapshot | snapshot format | Unit: verify JPEG output |
| P7-3.2-3 | Workflows / Snapshot | snapshot_cache | Unit: verify cache behavior |
| P7-3.2-4 | Workflows / Snapshot | offline handling | Unit: mock offline, verify placeholder |
| P7-3.3-1 | NFRs / Observability | stream logging | Unit: verify log entries on start/stop |
| P7-3.3-2 | APIs / GET status | stream_diagnostics | Integration: verify response format |
| P7-3.3-3 | APIs / POST test-stream | test endpoint | Integration: verify ffmpeg_command in response |
| P7-3.3-4 | Detailed Design / UI | HomeKitSettings | E2E: click test button, see result |

## Risks, Assumptions, Open Questions

### Risks
- **R1:** ffmpeg transcoding may introduce noticeable latency
  - *Mitigation:* Use `-tune zerolatency`, optimize buffers
- **R2:** Some cameras may not support compatible H.264 profiles
  - *Mitigation:* Force baseline profile in ffmpeg, test with variety of cameras
- **R3:** iOS may timeout slow streams
  - *Mitigation:* Monitor latency, add preload buffer

### Assumptions
- **A1:** ffmpeg 6.0+ is installed on the system
- **A2:** Camera provides H.264 or H.265 RTSP stream
- **A3:** Network bandwidth sufficient for transcoded stream (1.5Mbps minimum)

### Open Questions
- **Q1:** Should we support audio in streams?
  - *Recommendation:* Add in future epic, focus on video first
- **Q2:** What placeholder image for offline cameras?
  - *Recommendation:* Use ArgusAI logo with "Camera Offline" text
- **Q3:** Should quality be per-camera or global?
  - *Recommendation:* Per-camera for flexibility, with global default

## Test Strategy Summary

### Unit Tests
- Snapshot caching behavior (cache hit, cache miss, expiry)
- Quality setting to ffmpeg argument mapping
- Stream tracking (add, remove, count)
- Offline camera placeholder generation

### Integration Tests
- `/api/v1/homekit/cameras/{id}/test-stream` returns valid diagnostics
- `/api/v1/homekit/cameras/{id}/snapshot` returns JPEG
- Stream start logs correct event
- Multiple streams tracked correctly

### Manual Tests
- View camera in Apple Home app on iPhone
- View camera in Apple Home app on iPad
- Start two streams simultaneously
- Camera goes offline during stream (verify graceful failure)
- Change quality setting, verify stream updates

### Tools
- pytest for backend tests
- ffprobe for stream validation
- Apple Home app on iOS device
- Wireshark for SRTP packet inspection (if needed)
