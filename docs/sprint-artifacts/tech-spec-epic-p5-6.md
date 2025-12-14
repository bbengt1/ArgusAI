# Epic Technical Specification: MQTT Enhancements

Date: 2025-12-14
Author: Brent
Epic ID: P5-6
Status: Draft

---

## Overview

Epic P5-6 enhances ArgusAI's MQTT integration with MQTT 5.0 features: message expiry for event messages and birth/will messages for connection state monitoring. These improvements make the Home Assistant integration more robust by preventing stale messages and providing clear online/offline status.

This epic builds on the Phase 4 MQTT implementation (Epic P4-2) by adding protocol-level features that improve reliability and user experience for Home Assistant users.

**PRD Reference:** docs/PRD-phase5.md (FR37-FR38)
**Backlog Items:** FF-012, FF-013

## Objectives and Scope

**In Scope:**
- MQTT 5.0 message expiry interval on event messages
- Configurable expiry time in settings
- Birth message published on successful MQTT connection
- Will (Last Will and Testament) message for unexpected disconnection
- Home Assistant availability topic integration
- Settings UI for expiry time configuration

**Out of Scope:**
- MQTT 5.0 shared subscriptions (no subscribers in ArgusAI)
- MQTT 5.0 topic aliases
- MQTT 5.0 user properties
- Request/response pattern
- Full MQTT 5.0 feature set (focus on expiry + birth/will only)

## System Architecture Alignment

**Architecture Reference:** docs/architecture/phase-4-additions.md (MQTT section)

This epic extends the existing MQTT service:
- `mqtt_service.py` - Add expiry and birth/will support
- MQTT settings - Add expiry configuration
- Availability topic - Standard Home Assistant pattern

**Existing Integration Points:**
- `mqtt_service.py` - Core MQTT client (aiomqtt/paho-mqtt)
- `event_processor.py` - Event publishing to MQTT
- Settings page - MQTT configuration UI

## Detailed Design

### Services and Modules

| Component | Changes | Location |
|-----------|---------|----------|
| mqtt_service.py | Add expiry, birth/will | backend/app/services/ |
| MQTTSettings | Add expiry_seconds field | backend/app/models/settings.py |
| MQTTSettings.tsx | Add expiry configuration | frontend/components/settings/ |

### Data Models and Contracts

**MQTT Settings Extension:**
```python
class MQTTSettings(BaseModel):
    # Existing fields...
    broker_host: str
    broker_port: int = 1883
    username: Optional[str]
    password: Optional[str]  # Encrypted
    topic_prefix: str = "argusai"

    # New Phase 5 fields
    message_expiry_seconds: int = 300  # 5 minutes default
    availability_topic: str = "argusai/status"
    birth_message: str = "online"
    will_message: str = "offline"
```

**Message Structure with Expiry (MQTT 5.0):**
```python
# Event publish with expiry
publish(
    topic="argusai/events/camera_front_door",
    payload=json.dumps(event_data),
    qos=1,
    properties=Properties(PacketTypes.PUBLISH)
)
properties.MessageExpiryInterval = settings.message_expiry_seconds
```

**Birth/Will Messages:**
```python
# Will message (set at connect time)
will = Will(
    topic=settings.availability_topic,
    payload=settings.will_message,
    qos=1,
    retain=True
)

# Birth message (published after connect)
publish(
    topic=settings.availability_topic,
    payload=settings.birth_message,
    qos=1,
    retain=True
)
```

### APIs and Interfaces

**Settings API Extension:**

Existing `/api/v1/settings/mqtt` endpoint extended with new fields:

```json
{
  "broker_host": "192.168.1.100",
  "broker_port": 1883,
  "username": "homeassistant",
  "topic_prefix": "argusai",
  "message_expiry_seconds": 300,
  "availability_topic": "argusai/status",
  "birth_message": "online",
  "will_message": "offline"
}
```

### Workflows and Sequencing

**MQTT Connection with Birth/Will:**
```
1. Load MQTT settings from database
2. Configure Will message:
   - Topic: availability_topic (e.g., "argusai/status")
   - Payload: will_message (e.g., "offline")
   - QoS: 1, Retain: True
3. Connect to broker with Will
4. On successful connect:
   - Publish birth message to availability_topic
   - Payload: birth_message (e.g., "online")
   - QoS: 1, Retain: True
5. Normal operation (publish events with expiry)
6. On graceful disconnect:
   - Publish offline message manually
   - Disconnect
7. On unexpected disconnect:
   - Broker publishes Will message automatically
```

**Event Publishing with Expiry:**
```
1. Event detected and processed
2. Build MQTT message payload (JSON)
3. Create MQTT 5.0 properties:
   - MessageExpiryInterval = message_expiry_seconds
4. Publish to event topic with properties
5. Broker stores message with TTL
6. If not consumed within TTL:
   - Broker discards message
   - Home Assistant never sees stale event
```

**Home Assistant Integration:**
```yaml
# Home Assistant configuration.yaml (user creates this)
mqtt:
  sensor:
    - name: "ArgusAI Status"
      state_topic: "argusai/status"
      availability_topic: "argusai/status"
      payload_available: "online"
      payload_not_available: "offline"
```

## Non-Functional Requirements

### Reliability

| Requirement | Implementation |
|-------------|----------------|
| Connection state visibility | Birth/will messages with retain |
| Stale message prevention | Message expiry (5 min default) |
| Graceful shutdown | Manual offline message before disconnect |
| Unexpected disconnect | Will message auto-published by broker |

### Compatibility

| Requirement | Details |
|-------------|---------|
| MQTT 5.0 broker | Required for message expiry |
| MQTT 3.1.1 fallback | Birth/will work, expiry silently ignored |
| Mosquitto | 2.0+ recommended for MQTT 5.0 |
| Home Assistant | MQTT integration compatible |

### Configuration

| Setting | Default | Range |
|---------|---------|-------|
| message_expiry_seconds | 300 | 60-3600 (1 min to 1 hour) |
| availability_topic | "argusai/status" | Any valid topic |
| birth_message | "online" | Any string |
| will_message | "offline" | Any string |

## Dependencies and Integrations

### Python Dependencies

| Package | Version | Notes |
|---------|---------|-------|
| aiomqtt | >=2.0.0 | Already installed, supports MQTT 5.0 |
| paho-mqtt | >=2.0.0 | aiomqtt dependency, MQTT 5.0 support |

### External Dependencies

| Component | Requirement |
|-----------|-------------|
| MQTT Broker | MQTT 5.0 support for message expiry |
| Home Assistant | MQTT integration configured |

## Acceptance Criteria (Authoritative)

**Story P5-6.1: Add MQTT 5.0 Message Expiry Support**
1. Event messages include MessageExpiryInterval property
2. Expiry time configurable in MQTT settings (default 300 seconds)
3. Settings UI shows expiry time input with validation (60-3600)
4. Messages published to MQTT 5.0 broker include expiry
5. Messages not consumed within TTL are discarded by broker
6. Works gracefully with MQTT 3.1.1 brokers (expiry ignored)

**Story P5-6.2: Implement MQTT Birth/Will Messages**
1. Will message configured at connection time
2. Will topic is availability_topic from settings
3. Will payload is will_message from settings ("offline" default)
4. Will message has QoS 1 and retain=true
5. Birth message published immediately after successful connect
6. Birth topic same as availability_topic
7. Birth payload is birth_message from settings ("online" default)
8. Home Assistant shows ArgusAI as online/offline correctly

## Traceability Mapping

| AC | Spec Section | Component | Test Idea |
|----|--------------|-----------|-----------|
| P5-6.1-1 | Workflows | mqtt_service.py | Expiry property test |
| P5-6.1-2 | Data Models | MQTTSettings | Settings field test |
| P5-6.1-3 | UI | MQTTSettings.tsx | Input validation test |
| P5-6.1-4 | Workflows | Publish flow | MQTT 5.0 property test |
| P5-6.1-5 | Integration | MQTT broker | Expiry behavior test |
| P5-6.1-6 | Compatibility | MQTT 3.1.1 | Graceful fallback test |
| P5-6.2-1 | Workflows | Connection | Will configuration test |
| P5-6.2-2 | Data Models | Settings | Topic configuration test |
| P5-6.2-3 | Data Models | Settings | Payload configuration test |
| P5-6.2-4 | Workflows | Will message | QoS and retain test |
| P5-6.2-5 | Workflows | Connection | Birth publish test |
| P5-6.2-6 | Workflows | Birth message | Topic match test |
| P5-6.2-7 | Data Models | Settings | Birth payload test |
| P5-6.2-8 | Integration | Home Assistant | Availability test |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1: Broker compatibility** - MQTT 5.0 required for expiry; older brokers may not support
- **R2: Library support** - aiomqtt MQTT 5.0 support may have edge cases
- **R3: Home Assistant config** - Users must configure availability_topic correctly

**Assumptions:**
- **A1:** Most modern MQTT brokers (Mosquitto 2.0+) support MQTT 5.0
- **A2:** aiomqtt/paho-mqtt 2.0+ properly implements MQTT 5.0 properties
- **A3:** 5-minute default expiry appropriate for most event use cases
- **A4:** Users understand Home Assistant MQTT availability patterns

**Open Questions:**
- **Q1:** Should we auto-detect MQTT 5.0 support? → Yes, check protocol version at connect
- **Q2:** Per-event-type expiry times? → No, single global setting is sufficient
- **Q3:** Custom availability payloads (JSON)? → No, stick with simple strings for compatibility

## Test Strategy Summary

**Unit Tests:**
- `test_mqtt_service.py` - Message expiry property setting
- `test_mqtt_service.py` - Birth/will configuration
- Settings model validation tests

**Integration Tests:**
- MQTT connection with will message
- Birth message publish verification
- Event publish with expiry property
- Settings API update with new fields

**Manual Tests (Required):**
- Full flow with Mosquitto 2.0+ broker
- Home Assistant availability entity test
- Message expiry verification (wait for TTL)
- Unexpected disconnect (kill process) → will message test
- Graceful shutdown → offline message test

**Test Environment:**
- Mosquitto 2.0+ in test environment (Docker)
- MQTT 5.0 protocol version specified
- Home Assistant (optional) for availability verification
