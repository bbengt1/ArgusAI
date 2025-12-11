# Story P4-2.2: Home Assistant Discovery

Status: done

## Story

As a **Home Assistant user**,
I want **the AI classifier to automatically register sensors via MQTT Discovery**,
so that **my cameras and their AI-detected events appear in Home Assistant without manual configuration**.

## Acceptance Criteria

| # | Criteria | Verification |
|---|----------|--------------|
| 1 | Discovery config published to `homeassistant/sensor/<device_id>/config` on connect | Integration test subscribing to discovery topic |
| 2 | Sensor entity appears in Home Assistant automatically after discovery publish | Manual test with HA instance |
| 3 | Device grouping shows all camera sensors together under one device | HA UI verification - check device page |
| 4 | Sensor removal works when camera deleted (empty payload to discovery topic) | Delete camera, verify HA sensor disappears |
| 5 | Discovery republished when MQTT reconnects after disconnection | Test reconnect scenario, verify discovery sent |
| 6 | Discovery can be disabled via configuration toggle | API test with discovery_enabled=false |
| 7 | Entity availability published on connect/disconnect | Verify availability topic updates |

## Tasks / Subtasks

- [x] **Task 1: Implement discovery config generation** (AC: 1, 3) ✅
  - [x] Create `MQTTDiscoveryService` class in `backend/app/services/mqtt_discovery_service.py`
  - [x] Implement `generate_sensor_config(camera)` returning HA discovery payload
  - [x] Include device info for grouping: identifiers, name, manufacturer, model, sw_version
  - [x] Set unique_id as `liveobject_{camera_id}_event` for sensor uniqueness
  - [x] Configure state_topic as `{topic_prefix}/camera/{camera_id}/event`
  - [x] Add json_attributes_topic for full event payload access

- [x] **Task 2: Implement discovery publishing** (AC: 1, 5) ✅
  - [x] Add `publish_discovery_config(camera)` method to MQTTDiscoveryService
  - [x] Publish to `{discovery_prefix}/sensor/liveobject_{camera_id}_event/config`
  - [x] Use QoS 1 and retain=true for discovery messages
  - [x] Add `publish_all_discovery_configs()` for all enabled cameras
  - [x] Call discovery publish after successful MQTT connect

- [x] **Task 3: Implement sensor removal** (AC: 4) ✅
  - [x] Add `remove_discovery_config(camera_id)` method
  - [x] Publish empty payload ("") to discovery topic to remove sensor
  - [x] Hook into camera delete flow to trigger removal
  - [x] Hook into camera disable flow to trigger removal

- [x] **Task 4: Add availability support** (AC: 7) ✅
  - [x] Add availability_topic to discovery config: `{topic_prefix}/status`
  - [x] Publish "online" to status topic after successful connect
  - [x] Configure Last Will and Testament (LWT) to publish "offline" on disconnect
  - [x] Set payload_available="online" and payload_not_available="offline" in discovery

- [x] **Task 5: Add discovery toggle** (AC: 6) ✅
  - [x] Use existing `discovery_enabled` field in MQTTConfig model
  - [x] Skip discovery publishing when discovery_enabled=false
  - [x] Remove all discovery configs when discovery is disabled

- [x] **Task 6: Integrate with MQTTService** (AC: 1, 5) ✅
  - [x] Modify MQTTService.on_connect callback to trigger discovery
  - [x] Ensure discovery runs after connection is stable
  - [x] Add logging for discovery publish success/failure

- [x] **Task 7: Add API endpoint for manual discovery trigger** (AC: 1) ✅
  - [x] Add `POST /api/v1/integrations/mqtt/publish-discovery` endpoint
  - [x] Allow manual republish of all discovery configs
  - [x] Return count of cameras published

- [x] **Task 8: Write tests** (AC: all) ✅
  - [x] Unit tests for discovery config generation (verify payload structure)
  - [x] Unit tests for sensor removal (verify empty payload)
  - [x] Integration test: discovery published on connect
  - [x] Integration test: discovery skipped when disabled
  - [x] Test camera delete triggers removal

## Dev Notes

### Architecture Alignment

This story extends the MQTTService from P4-2.1 with Home Assistant Discovery protocol support. The discovery service is separate to maintain single-responsibility principle.

**Component Integration:**
```
Camera Change → CameraService → MQTTDiscoveryService → MQTTService → MQTT Broker
                                       ↓                              ↓
                                 Generate Config              Publish to HA Topic
```

### Key Implementation Details

**Discovery Topic Structure (Home Assistant Standard):**
```
<discovery_prefix>/<component>/[<node_id>/]<object_id>/config
```
For this implementation:
```
homeassistant/sensor/liveobject_{camera_id}_event/config
```

**Sensor Discovery Payload:**
```json
{
  "name": "{camera_name} AI Events",
  "unique_id": "liveobject_{camera_id}_event",
  "state_topic": "liveobject/camera/{camera_id}/event",
  "value_template": "{{ value_json.description[:255] }}",
  "json_attributes_topic": "liveobject/camera/{camera_id}/event",
  "availability_topic": "liveobject/status",
  "payload_available": "online",
  "payload_not_available": "offline",
  "icon": "mdi:cctv",
  "device": {
    "identifiers": ["liveobject_{camera_id}"],
    "name": "{camera_name}",
    "manufacturer": "Live Object AI",
    "model": "AI Classifier",
    "sw_version": "4.0.0"
  }
}
```

**Last Will and Testament (LWT):**
Configure Paho client with will message before connect:
```python
client.will_set(
    topic=f"{topic_prefix}/status",
    payload="offline",
    qos=1,
    retain=True
)
```

### Project Structure Notes

New files to create:
- `backend/app/services/mqtt_discovery_service.py` - Discovery config generation and publishing

Files to modify:
- `backend/app/services/mqtt_service.py` - Add LWT, integrate discovery on connect
- `backend/app/api/v1/integrations.py` - Add publish-discovery endpoint
- `backend/app/services/camera_service.py` - Hook camera delete to discovery removal
- `backend/tests/test_services/test_mqtt_service.py` - Add discovery tests
- `backend/tests/test_api/test_integrations.py` - Add publish-discovery API test

### Learnings from Previous Story

**From Story P4-2.1 (MQTT Client Implementation):**

- **MQTTService Available**: `backend/app/services/mqtt_service.py` with connect(), disconnect(), publish() - REUSE this
- **MQTTConfig Model**: Already has `discovery_enabled` and `discovery_prefix` fields
- **Event Serializer**: `serialize_event_for_mqtt()` in mqtt_service.py - consistent with discovery payloads
- **Prometheus Metrics**: mqtt_messages_published_total exists - use for discovery publishes too
- **Auto-Reconnect**: on_connect callback already exists - add discovery trigger there
- **Pattern to Follow**: Service class instantiated in main.py, exposed via dependency injection

[Source: docs/sprint-artifacts/p4-2-1-mqtt-client-implementation.md#Dev-Agent-Record]

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-p4-2.md#Story-P4-2.2-Home-Assistant-Discovery]
- [Source: docs/sprint-artifacts/tech-spec-epic-p4-2.md#Workflows-and-Sequencing]
- [Source: docs/epics-phase4.md#Story-P4-2.2-Home-Assistant-Discovery]
- [Home Assistant MQTT Discovery Docs](https://www.home-assistant.io/integrations/mqtt/#mqtt-discovery)

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/p4-2-2-home-assistant-discovery.context.xml`

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2025-12-10 | Claude Opus 4.5 | Initial story draft |
