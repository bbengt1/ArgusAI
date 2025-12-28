# ArgusAI Native Home Assistant Integration Design

**Version:** 1.0
**Date:** December 2025
**Status:** Design Review

---

## Executive Summary

This document outlines the design for a native Home Assistant custom integration for ArgusAI. While ArgusAI currently supports Home Assistant via MQTT auto-discovery, a native integration provides significant advantages:

- **Richer Entity Types**: Camera streaming, media browser, device triggers
- **Bidirectional Control**: Trigger analysis, manage rules, control cameras from HA
- **Better UX**: Config flow UI, options flow, diagnostics
- **Real-time Events**: Native HA event bus integration via WebSocket
- **Deeper Integration**: Services, automations, scripts with full context

---

## 1. Integration Overview

### 1.1 Integration Type

| Property | Value |
|----------|-------|
| **Domain** | `argusai` |
| **Integration Type** | `hub` |
| **IoT Class** | `local_push` |
| **Config Flow** | Yes (UI-based setup) |
| **Options Flow** | Yes (runtime configuration) |

### 1.2 Supported Platforms

| Platform | Entity Types |
|----------|-------------|
| `camera` | Live camera streams, snapshots |
| `binary_sensor` | Motion, person, vehicle, package, animal, doorbell |
| `sensor` | Event counts, last event, AI confidence, anomaly score |
| `image` | Event thumbnails, latest snapshot |
| `event` | HA event entities for automations |
| `button` | Trigger analysis, reconnect camera |
| `switch` | Enable/disable camera, enable/disable motion detection |
| `select` | Analysis mode selection |
| `number` | Motion sensitivity, cooldown settings |

---

## 2. File Structure

```
custom_components/argusai/
├── __init__.py              # Integration entry point
├── manifest.json            # Integration metadata
├── config_flow.py           # UI configuration flow
├── options_flow.py          # Runtime options
├── strings.json             # UI translations
├── const.py                 # Constants and defaults
├── coordinator.py           # DataUpdateCoordinator
├── api.py                   # ArgusAI API client
├── websocket.py             # WebSocket event listener
├── entity.py                # Base entity classes
├── camera.py                # Camera platform
├── binary_sensor.py         # Detection sensors
├── sensor.py                # Statistics sensors
├── image.py                 # Thumbnail/snapshot images
├── event.py                 # HA event entities
├── button.py                # Action buttons
├── switch.py                # Enable/disable switches
├── select.py                # Mode selectors
├── number.py                # Numeric settings
├── services.yaml            # Custom service definitions
├── services.py              # Service handlers
├── diagnostics.py           # Debug/diagnostics endpoint
└── icons.json               # Custom icons (optional)
```

---

## 3. Configuration Flow

### 3.1 User Setup Flow

```
┌─────────────────────────────────────────────┐
│            Step 1: Connection               │
├─────────────────────────────────────────────┤
│  Host: [_________________________]          │
│  Port: [8000___]                            │
│  Use SSL: [ ]                               │
│                                             │
│  [Test Connection]  [Next →]                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│          Step 2: Authentication             │
├─────────────────────────────────────────────┤
│  ○ No Authentication                        │
│  ● API Key                                  │
│  ○ Username/Password                        │
│                                             │
│  API Key: [_________________________]       │
│                                             │
│  [← Back]  [Submit]                         │
└─────────────────────────────────────────────┘
```

### 3.2 Config Flow Implementation

```python
# config_flow.py
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT, default=8000): int,
    vol.Optional(CONF_SSL, default=False): bool,
})

STEP_AUTH_DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_API_KEY): str,
})
```

### 3.3 Options Flow (Runtime Configuration)

```python
# Configurable at runtime without reconfiguration
OPTIONS_SCHEMA = vol.Schema({
    vol.Optional("scan_interval", default=30): vol.All(int, vol.Range(min=10, max=300)),
    vol.Optional("enable_cameras", default=True): bool,
    vol.Optional("enable_motion_sensors", default=True): bool,
    vol.Optional("enable_smart_detection", default=True): bool,
    vol.Optional("enable_event_entities", default=True): bool,
    vol.Optional("websocket_reconnect", default=True): bool,
})
```

---

## 4. Entity Design

### 4.1 Device Hierarchy

```
ArgusAI Hub (Main Device)
├── Camera: Front Door
│   ├── camera.argusai_front_door
│   ├── binary_sensor.argusai_front_door_motion
│   ├── binary_sensor.argusai_front_door_person
│   ├── binary_sensor.argusai_front_door_vehicle
│   ├── binary_sensor.argusai_front_door_package
│   ├── binary_sensor.argusai_front_door_animal
│   ├── sensor.argusai_front_door_events_today
│   ├── sensor.argusai_front_door_events_week
│   ├── sensor.argusai_front_door_last_event
│   ├── sensor.argusai_front_door_ai_confidence
│   ├── image.argusai_front_door_thumbnail
│   ├── button.argusai_front_door_analyze
│   ├── switch.argusai_front_door_enabled
│   ├── switch.argusai_front_door_motion_detection
│   ├── select.argusai_front_door_analysis_mode
│   └── number.argusai_front_door_sensitivity
│
├── Camera: Backyard
│   └── (same entity pattern)
│
└── System Sensors
    ├── sensor.argusai_total_events_today
    ├── sensor.argusai_storage_used
    ├── sensor.argusai_ai_calls_today
    ├── binary_sensor.argusai_connected
    └── button.argusai_generate_summary
```

### 4.2 Entity Naming Convention

```
{domain}_{camera_name_slug}_{entity_type}

Examples:
- camera.argusai_front_door
- binary_sensor.argusai_front_door_person
- sensor.argusai_front_door_events_today
```

### 4.3 Unique ID Format

```
argusai_{instance_id}_{camera_id}_{entity_suffix}

Examples:
- argusai_192168110_cam001_camera
- argusai_192168110_cam001_motion
- argusai_192168110_cam001_person
```

---

## 5. Platform Implementations

### 5.1 Camera Platform

```python
class ArgusAICamera(Camera):
    """ArgusAI camera entity with live streaming."""

    _attr_supported_features = (
        CameraEntityFeature.STREAM |
        CameraEntityFeature.ON_OFF
    )

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return current camera snapshot."""
        return await self.coordinator.api.get_camera_preview(self._camera_id)

    async def stream_source(self) -> str | None:
        """Return RTSP stream URL for camera."""
        camera = self.coordinator.data["cameras"].get(self._camera_id)
        if camera and camera.get("rtsp_url"):
            return camera["rtsp_url"]
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional camera attributes."""
        camera = self.coordinator.data["cameras"].get(self._camera_id, {})
        return {
            "source_type": camera.get("source_type"),
            "motion_detection_enabled": camera.get("motion_detection_enabled"),
            "analysis_mode": camera.get("analysis_mode"),
            "last_event_id": camera.get("last_event_id"),
        }
```

### 5.2 Binary Sensor Platform

```python
DETECTION_TYPES = {
    "motion": BinarySensorDeviceClass.MOTION,
    "person": BinarySensorDeviceClass.OCCUPANCY,
    "vehicle": BinarySensorDeviceClass.MOTION,
    "package": BinarySensorDeviceClass.MOTION,
    "animal": BinarySensorDeviceClass.MOTION,
    "doorbell": BinarySensorDeviceClass.OCCUPANCY,
}

class ArgusAIDetectionSensor(BinarySensorEntity):
    """Detection binary sensor with auto-off timer."""

    def __init__(self, coordinator, camera_id, detection_type):
        self._camera_id = camera_id
        self._detection_type = detection_type
        self._attr_device_class = DETECTION_TYPES.get(detection_type)
        self._attr_unique_id = f"argusai_{camera_id}_{detection_type}"
        self._last_triggered = None
        self._auto_off_seconds = 300  # 5 minutes

    @property
    def is_on(self) -> bool:
        """Return True if detection is active."""
        events = self.coordinator.data.get("recent_events", {}).get(self._camera_id, [])
        for event in events:
            if self._detection_type in event.get("objects_detected", []):
                event_time = datetime.fromisoformat(event["timestamp"])
                if (datetime.now(timezone.utc) - event_time).seconds < self._auto_off_seconds:
                    return True
        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return detection attributes."""
        return {
            "last_triggered": self._last_triggered,
            "confidence": self._get_last_confidence(),
            "description": self._get_last_description(),
        }
```

### 5.3 Sensor Platform

```python
class ArgusAIEventCountSensor(SensorEntity):
    """Daily/weekly event count sensor."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "events"

    @property
    def native_value(self) -> int:
        """Return event count."""
        counts = self.coordinator.data.get("event_counts", {})
        camera_counts = counts.get(self._camera_id, {})
        return camera_counts.get(self._period, 0)  # "today" or "week"


class ArgusAILastEventSensor(SensorEntity):
    """Last event description sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Return last event timestamp."""
        events = self.coordinator.data.get("recent_events", {}).get(self._camera_id, [])
        if events:
            return datetime.fromisoformat(events[0]["timestamp"])
        return None

    @property
    def extra_state_attributes(self) -> dict:
        """Return last event details."""
        events = self.coordinator.data.get("recent_events", {}).get(self._camera_id, [])
        if events:
            event = events[0]
            return {
                "description": event.get("description"),
                "objects_detected": event.get("objects_detected"),
                "confidence": event.get("confidence"),
                "smart_detection_type": event.get("smart_detection_type"),
                "thumbnail_url": event.get("thumbnail_url"),
                "event_id": event.get("id"),
            }
        return {}
```

### 5.4 Event Platform (HA 2024.4+)

```python
class ArgusAIEventEntity(EventEntity):
    """Event entity for HA automations."""

    _attr_event_types = [
        "motion_detected",
        "person_detected",
        "vehicle_detected",
        "package_detected",
        "animal_detected",
        "doorbell_ring",
    ]

    def handle_event(self, event_data: dict) -> None:
        """Handle incoming ArgusAI event."""
        event_type = self._map_detection_to_event(event_data)
        self._trigger_event(
            event_type,
            {
                "description": event_data.get("description"),
                "confidence": event_data.get("confidence"),
                "objects": event_data.get("objects_detected"),
                "thumbnail_url": event_data.get("thumbnail_url"),
            }
        )
```

### 5.5 Button Platform

```python
class ArgusAIAnalyzeButton(ButtonEntity):
    """Button to trigger manual AI analysis."""

    _attr_icon = "mdi:image-search"

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.api.trigger_analysis(self._camera_id)
        await self.coordinator.async_request_refresh()


class ArgusAIReconnectButton(ButtonEntity):
    """Button to reconnect camera."""

    _attr_icon = "mdi:connection"

    async def async_press(self) -> None:
        """Handle button press."""
        await self.coordinator.api.reconnect_camera(self._camera_id)
```

### 5.6 Switch Platform

```python
class ArgusAICameraEnabledSwitch(SwitchEntity):
    """Switch to enable/disable camera."""

    _attr_icon = "mdi:camera"

    @property
    def is_on(self) -> bool:
        """Return camera enabled state."""
        camera = self.coordinator.data["cameras"].get(self._camera_id, {})
        return camera.get("enabled", False)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable camera."""
        await self.coordinator.api.update_camera(self._camera_id, {"enabled": True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Disable camera."""
        await self.coordinator.api.update_camera(self._camera_id, {"enabled": False})
        await self.coordinator.async_request_refresh()
```

### 5.7 Select Platform

```python
ANALYSIS_MODES = {
    "single_frame": "Single Frame",
    "multi_frame": "Multi Frame",
    "video_native": "Video Native",
}

class ArgusAIAnalysisModeSelect(SelectEntity):
    """Select entity for analysis mode."""

    _attr_options = list(ANALYSIS_MODES.values())
    _attr_icon = "mdi:movie-filter"

    @property
    def current_option(self) -> str:
        """Return current analysis mode."""
        camera = self.coordinator.data["cameras"].get(self._camera_id, {})
        mode = camera.get("analysis_mode", "single_frame")
        return ANALYSIS_MODES.get(mode, "Single Frame")

    async def async_select_option(self, option: str) -> None:
        """Set analysis mode."""
        mode_key = next(k for k, v in ANALYSIS_MODES.items() if v == option)
        await self.coordinator.api.update_camera(
            self._camera_id,
            {"analysis_mode": mode_key}
        )
        await self.coordinator.async_request_refresh()
```

---

## 6. Data Coordinator

### 6.1 Coordinator Implementation

```python
class ArgusAICoordinator(DataUpdateCoordinator):
    """Coordinate data updates from ArgusAI."""

    def __init__(self, hass: HomeAssistant, api: ArgusAIAPI, config_entry):
        super().__init__(
            hass,
            _LOGGER,
            name="ArgusAI",
            update_interval=timedelta(seconds=config_entry.options.get("scan_interval", 30)),
            always_update=False,
        )
        self.api = api
        self.config_entry = config_entry
        self._websocket_task = None

    async def _async_update_data(self) -> dict:
        """Fetch data from ArgusAI API."""
        try:
            async with asyncio.timeout(10):
                cameras = await self.api.get_cameras()
                events = await self.api.get_recent_events(limit=100)
                stats = await self.api.get_event_stats()

                # Group events by camera
                events_by_camera = {}
                for event in events:
                    cam_id = event["camera_id"]
                    if cam_id not in events_by_camera:
                        events_by_camera[cam_id] = []
                    events_by_camera[cam_id].append(event)

                return {
                    "cameras": {c["id"]: c for c in cameras},
                    "recent_events": events_by_camera,
                    "event_counts": stats.get("counts_by_camera", {}),
                    "system_stats": stats,
                }
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout connecting to ArgusAI") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with ArgusAI: {err}") from err

    async def start_websocket(self) -> None:
        """Start WebSocket listener for real-time updates."""
        self._websocket_task = self.hass.async_create_task(
            self._websocket_listener()
        )

    async def _websocket_listener(self) -> None:
        """Listen for WebSocket events."""
        while True:
            try:
                async for event in self.api.subscribe_events():
                    await self._handle_event(event)
            except Exception as err:
                _LOGGER.warning("WebSocket error: %s, reconnecting...", err)
                await asyncio.sleep(5)

    async def _handle_event(self, event: dict) -> None:
        """Handle incoming WebSocket event."""
        event_type = event.get("type")

        if event_type == "new_event":
            # Update coordinator data
            camera_id = event["data"]["camera_id"]
            if camera_id not in self.data["recent_events"]:
                self.data["recent_events"][camera_id] = []
            self.data["recent_events"][camera_id].insert(0, event["data"])

            # Fire HA event for automations
            self.hass.bus.async_fire(
                "argusai_event",
                {
                    "camera_id": camera_id,
                    "camera_name": event["data"].get("camera_name"),
                    "event_type": event["data"].get("smart_detection_type", "motion"),
                    "description": event["data"].get("description"),
                    "confidence": event["data"].get("confidence"),
                    "objects": event["data"].get("objects_detected"),
                    "thumbnail_url": event["data"].get("thumbnail_url"),
                }
            )

            # Notify entities of update
            self.async_set_updated_data(self.data)
```

---

## 7. API Client

### 7.1 API Client Implementation

```python
class ArgusAIAPI:
    """ArgusAI API client."""

    def __init__(self, hass: HomeAssistant, host: str, port: int, ssl: bool, api_key: str = None):
        self.hass = hass
        self.base_url = f"{'https' if ssl else 'http'}://{host}:{port}/api/v1"
        self.api_key = api_key
        self._session = None

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = async_get_clientsession(self.hass)
        return self._session

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def test_connection(self) -> bool:
        """Test connection to ArgusAI."""
        try:
            async with self.session.get(
                f"{self.base_url}/system/health",
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def get_cameras(self) -> list[dict]:
        """Get all cameras."""
        async with self.session.get(
            f"{self.base_url}/cameras",
            headers=self._headers(),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_recent_events(self, limit: int = 100) -> list[dict]:
        """Get recent events."""
        async with self.session.get(
            f"{self.base_url}/events",
            params={"limit": limit, "sort": "-timestamp"},
            headers=self._headers(),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("items", data)

    async def get_event_stats(self) -> dict:
        """Get event statistics."""
        async with self.session.get(
            f"{self.base_url}/events/stats",
            headers=self._headers(),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_camera_preview(self, camera_id: str) -> bytes:
        """Get camera preview image."""
        async with self.session.get(
            f"{self.base_url}/cameras/{camera_id}/preview",
            headers=self._headers(),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            # Decode base64 image
            import base64
            return base64.b64decode(data.get("image", ""))

    async def trigger_analysis(self, camera_id: str) -> dict:
        """Trigger manual analysis."""
        async with self.session.post(
            f"{self.base_url}/cameras/{camera_id}/analyze",
            headers=self._headers(),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def update_camera(self, camera_id: str, data: dict) -> dict:
        """Update camera settings."""
        async with self.session.put(
            f"{self.base_url}/cameras/{camera_id}",
            headers=self._headers(),
            json=data,
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def reconnect_camera(self, camera_id: str) -> dict:
        """Reconnect camera."""
        async with self.session.post(
            f"{self.base_url}/cameras/{camera_id}/reconnect",
            headers=self._headers(),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def generate_summary(self, hours: int = 24) -> dict:
        """Generate activity summary."""
        async with self.session.post(
            f"{self.base_url}/summaries/generate",
            headers=self._headers(),
            json={"hours": hours},
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def subscribe_events(self):
        """Subscribe to WebSocket events."""
        ws_url = self.base_url.replace("http", "ws").replace("/api/v1", "/ws")
        async with self.session.ws_connect(ws_url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    yield json.loads(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    raise Exception(f"WebSocket error: {ws.exception()}")
```

---

## 8. Services

### 8.1 Service Definitions

```yaml
# services.yaml
generate_summary:
  name: Generate Summary
  description: Generate an activity summary for the specified time period
  fields:
    hours:
      name: Hours
      description: Number of hours to summarize
      required: false
      default: 24
      selector:
        number:
          min: 1
          max: 168
          unit_of_measurement: hours
    camera_id:
      name: Camera
      description: Specific camera to summarize (optional)
      required: false
      selector:
        entity:
          filter:
            domain: camera
            integration: argusai

trigger_analysis:
  name: Trigger Analysis
  description: Trigger AI analysis on a camera
  target:
    entity:
      domain: camera
      integration: argusai

find_similar_events:
  name: Find Similar Events
  description: Find events similar to a specific event
  fields:
    event_id:
      name: Event ID
      description: The event ID to find similar events for
      required: true
      selector:
        text:
    limit:
      name: Limit
      description: Maximum number of similar events to return
      required: false
      default: 10
      selector:
        number:
          min: 1
          max: 50

set_motion_sensitivity:
  name: Set Motion Sensitivity
  description: Adjust motion detection sensitivity for a camera
  target:
    entity:
      domain: camera
      integration: argusai
  fields:
    sensitivity:
      name: Sensitivity
      description: Motion sensitivity (1-100)
      required: true
      selector:
        number:
          min: 1
          max: 100
```

### 8.2 Service Handlers

```python
# services.py
async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up ArgusAI services."""

    async def handle_generate_summary(call: ServiceCall) -> None:
        """Handle generate summary service call."""
        hours = call.data.get("hours", 24)
        camera_id = call.data.get("camera_id")

        entry_id = list(hass.data[DOMAIN].keys())[0]
        coordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        result = await coordinator.api.generate_summary(hours, camera_id)

        # Fire event with summary
        hass.bus.async_fire(
            "argusai_summary_generated",
            {"summary": result.get("summary"), "event_count": result.get("event_count")}
        )

    async def handle_trigger_analysis(call: ServiceCall) -> None:
        """Handle trigger analysis service call."""
        entity_ids = call.data.get("entity_id", [])
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        for entity_id in entity_ids:
            # Extract camera_id from entity
            state = hass.states.get(entity_id)
            if state and (camera_id := state.attributes.get("camera_id")):
                entry_id = list(hass.data[DOMAIN].keys())[0]
                coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
                await coordinator.api.trigger_analysis(camera_id)

    hass.services.async_register(
        DOMAIN, "generate_summary", handle_generate_summary
    )
    hass.services.async_register(
        DOMAIN, "trigger_analysis", handle_trigger_analysis
    )
```

---

## 9. Events

### 9.1 HA Events Fired

| Event | Trigger | Data |
|-------|---------|------|
| `argusai_event` | New detection event | camera_id, camera_name, event_type, description, confidence, objects, thumbnail_url |
| `argusai_doorbell` | Doorbell ring | camera_id, camera_name, timestamp |
| `argusai_camera_status` | Camera online/offline | camera_id, status |
| `argusai_summary_generated` | Summary created | summary, event_count |

### 9.2 Automation Examples Using Events

```yaml
# Automation using argusai_event
automation:
  - alias: "ArgusAI Person Alert via Event"
    trigger:
      - platform: event
        event_type: argusai_event
        event_data:
          event_type: person
    action:
      - service: notify.mobile_app
        data:
          title: "{{ trigger.event.data.camera_name }}"
          message: "{{ trigger.event.data.description }}"
          data:
            image: "{{ trigger.event.data.thumbnail_url }}"
```

---

## 10. Diagnostics

### 10.1 Diagnostics Implementation

```python
# diagnostics.py
async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": entry.options,
        },
        "coordinator_data": {
            "cameras_count": len(coordinator.data.get("cameras", {})),
            "cameras": [
                {
                    "id": c["id"],
                    "name": c["name"],
                    "type": c.get("source_type"),
                    "enabled": c.get("enabled"),
                }
                for c in coordinator.data.get("cameras", {}).values()
            ],
            "total_events_cached": sum(
                len(events)
                for events in coordinator.data.get("recent_events", {}).values()
            ),
            "last_update": coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time else None,
        },
        "websocket_connected": coordinator._websocket_task is not None
            and not coordinator._websocket_task.done(),
    }

TO_REDACT = {"api_key", "password", "host"}
```

---

## 11. Manifest

```json
{
  "domain": "argusai",
  "name": "ArgusAI",
  "codeowners": ["@bbengt1"],
  "config_flow": true,
  "documentation": "https://github.com/project-argusai/ArgusAI",
  "integration_type": "hub",
  "iot_class": "local_push",
  "issue_tracker": "https://github.com/project-argusai/ArgusAI/issues",
  "requirements": [
    "aiohttp>=3.8.0"
  ],
  "version": "1.0.0",
  "quality_scale": "bronze"
}
```

---

## 12. Comparison: Native Integration vs MQTT

| Feature | MQTT (Current) | Native Integration |
|---------|---------------|-------------------|
| **Setup** | Configure broker separately | Single config flow |
| **Camera Streams** | Not supported | Full RTSP streaming |
| **Snapshots** | Via thumbnail URL | Native image entities |
| **Real-time Events** | Push via MQTT | Push via WebSocket |
| **Camera Control** | Not supported | Enable/disable, settings |
| **Analysis Trigger** | Not supported | Button + service |
| **Motion Sensitivity** | Not supported | Number entity |
| **Analysis Mode** | Not supported | Select entity |
| **Event Entities** | Not supported | Native HA events |
| **Diagnostics** | Not supported | Full diagnostics |
| **Discovery** | Auto via MQTT | Config flow UI |
| **Bidirectional** | Publish only | Full control |

---

## 13. Implementation Phases

### Phase 1: Core Integration (MVP)
- [ ] Integration setup (`__init__.py`, `manifest.json`)
- [ ] Config flow (host, port, API key)
- [ ] API client with basic endpoints
- [ ] DataUpdateCoordinator
- [ ] Camera platform (streaming, snapshots)
- [ ] Binary sensors (motion, person, vehicle)
- [ ] Basic sensors (event counts, last event)

### Phase 2: Enhanced Entities
- [ ] Event entities for automations
- [ ] Button entities (analyze, reconnect)
- [ ] Switch entities (enable/disable)
- [ ] Select entities (analysis mode)
- [ ] Number entities (sensitivity)
- [ ] Image entities (thumbnails)

### Phase 3: Real-time & Services
- [ ] WebSocket integration
- [ ] Custom services
- [ ] HA events firing
- [ ] Options flow

### Phase 4: Polish
- [ ] Diagnostics
- [ ] Device triggers
- [ ] Translations
- [ ] Documentation
- [ ] HACS integration

---

## 14. Distribution

### 14.1 HACS Integration

```json
// hacs.json
{
  "name": "ArgusAI",
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

### 14.2 Repository Structure

```
argusai-hass/
├── custom_components/
│   └── argusai/
│       └── (all integration files)
├── hacs.json
├── README.md
├── LICENSE
└── .github/
    └── workflows/
        └── validate.yml
```

---

## 15. Open Questions

1. **Authentication**: Should we support multiple auth methods (API key, username/password, OAuth)?
2. **Multi-instance**: Support multiple ArgusAI servers in one HA instance?
3. **Camera Streams**: Direct RTSP pass-through or proxy through ArgusAI?
4. **Event History**: How much event history to cache in coordinator?
5. **Entity IDs**: Use camera name or camera UUID for entity IDs?

---

## 16. References

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [UniFi Protect Integration](https://github.com/briis/unifiprotect)
- [Frigate HASS Integration](https://github.com/blakeblackshear/frigate-hass-integration)
- [HACS Integration Guide](https://hacs.xyz/docs/publish/integration)
