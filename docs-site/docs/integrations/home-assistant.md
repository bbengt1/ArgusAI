---
sidebar_position: 1
---

# Home Assistant Integration

ArgusAI integrates with Home Assistant via MQTT with auto-discovery, enabling powerful automations and notifications based on AI-powered event detection.

## Features

- **Auto-Discovery**: Devices appear automatically in Home Assistant
- **Event Publishing**: Security events published as MQTT messages with AI descriptions
- **Camera Status**: Online/offline status sensors for each camera
- **Motion Sensors**: Per-camera motion detection with 5-minute timeout
- **Event Counters**: Daily and weekly event count sensors
- **Rich Attributes**: Thumbnail URLs, detection types, confidence scores

## Requirements

- Home Assistant with MQTT integration
- MQTT broker (Mosquitto recommended, or Home Assistant's built-in broker)
- Network access between ArgusAI and MQTT broker

## Configuration

### Enable MQTT in ArgusAI

1. Navigate to **Settings > Integrations**
2. Enable **MQTT Integration**
3. Configure connection:

| Field | Description | Default |
|-------|-------------|---------|
| Host | MQTT broker address | — |
| Port | Broker port | 1883 (8883 for TLS) |
| Username | MQTT username | (optional) |
| Password | MQTT password | (optional) |
| Topic Prefix | Base topic for events | `liveobject` |
| Discovery Prefix | HA discovery topic | `homeassistant` |
| Use TLS | Enable encrypted connection | false |

4. Click **Test Connection**
5. Save configuration
6. Click **Publish Discovery** to register devices with Home Assistant

### Home Assistant Setup

Ensure MQTT integration is configured in Home Assistant:

```yaml
# configuration.yaml
mqtt:
  broker: localhost
  port: 1883
  discovery: true
  discovery_prefix: homeassistant
```

Or use the Home Assistant UI: **Settings → Devices & Services → Add Integration → MQTT**

## Discovered Entities

ArgusAI creates these entities for each camera in Home Assistant:

### Sensors

| Entity Pattern | Description |
|----------------|-------------|
| `sensor.liveobject_{camera}_event` | Latest event AI description |
| `sensor.liveobject_{camera}_status` | Camera status (online/offline/unavailable) |
| `sensor.liveobject_{camera}_last_event` | Timestamp of last event |
| `sensor.liveobject_{camera}_events_today` | Daily event count (resets at midnight UTC) |
| `sensor.liveobject_{camera}_events_week` | Weekly event count (resets Monday 00:00 UTC) |

### Binary Sensors

| Entity Pattern | Description |
|----------------|-------------|
| `binary_sensor.liveobject_{camera}_activity` | Motion/activity detection (ON for 5 minutes after event) |

### Device Grouping

All sensors for a camera are grouped under a single device in Home Assistant, making it easy to view all related entities together.

## Event Attributes

Each event sensor includes rich attributes you can use in automations:

| Attribute | Type | Description |
|-----------|------|-------------|
| `camera_name` | string | Human-readable camera name |
| `smart_detection_type` | string | Detection type: `person`, `vehicle`, `package`, `animal`, `ring` |
| `is_doorbell_ring` | boolean | True if this is a doorbell ring event |
| `confidence` | integer | Detection confidence (0-100) |
| `ai_confidence` | float | AI analysis confidence |
| `thumbnail_url` | string | URL to event thumbnail image |
| `objects_detected` | array | List of detected objects |
| `timestamp` | string | ISO 8601 timestamp |
| `provider_used` | string | AI provider: `openai`, `grok`, `claude`, `gemini` |
| `source_type` | string | Camera source: `protect`, `rtsp`, `usb` |
| `delivery_carrier` | string | Package carrier if detected: `fedex`, `ups`, `usps`, `amazon` |

## Automation Examples

### Basic Motion Alert

Send a notification whenever any event is detected:

```yaml
automation:
  - alias: "ArgusAI - Motion Alert"
    description: "Send notification when ArgusAI detects an event"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_front_door_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable', ''] }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "{{ trigger.to_state.attributes.camera_name }}"
          message: "{{ trigger.to_state.state }}"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
            clickAction: "/lovelace/cameras"
```

### Person Detection Alert

Alert only when a person is detected:

```yaml
automation:
  - alias: "ArgusAI - Person Detected"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_front_door_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.smart_detection_type == 'person' }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Person at Front Door"
          message: "{{ trigger.to_state.state }}"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
            tag: "person-detection"
```

### Vehicle Detection Alert

```yaml
automation:
  - alias: "ArgusAI - Vehicle Detected"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_driveway_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.smart_detection_type == 'vehicle' }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Vehicle in Driveway"
          message: "{{ trigger.to_state.state }}"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
```

### Package Delivery Alert

```yaml
automation:
  - alias: "ArgusAI - Package Delivered"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_front_porch_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.smart_detection_type == 'package' }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Package Detected"
          message: "{{ trigger.to_state.state }}"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
            actions:
              - action: "VIEW_EVENT"
                title: "View Details"
```

### Doorbell Ring Alert

```yaml
automation:
  - alias: "ArgusAI - Doorbell Ring"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_doorbell_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.is_doorbell_ring == true }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Doorbell"
          message: "Someone is at the door"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
            priority: high
            ttl: 0
      - service: media_player.play_media
        target:
          entity_id: media_player.living_room_speaker
        data:
          media_content_id: "media-source://media_source/local/doorbell.mp3"
          media_content_type: "audio/mp3"
```

### Multi-Camera Alert

Monitor all cameras with a single automation:

```yaml
automation:
  - alias: "ArgusAI - All Camera Alerts"
    trigger:
      - platform: state
        entity_id:
          - sensor.liveobject_front_door_event
          - sensor.liveobject_backyard_event
          - sensor.liveobject_garage_event
          - sensor.liveobject_driveway_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable', ''] }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "{{ trigger.to_state.attributes.camera_name }}"
          message: "{{ trigger.to_state.state }}"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
            tag: "argusai-{{ trigger.entity_id }}"
```

### Night-Only Alerts

Alert only during nighttime hours:

```yaml
automation:
  - alias: "ArgusAI - Night Motion Alert"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_backyard_event
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable', ''] }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Night Motion - Backyard"
          message: "{{ trigger.to_state.state }}"
          data:
            priority: high
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
```

### Away Mode Alerts

Alert only when no one is home:

```yaml
automation:
  - alias: "ArgusAI - Away Mode Alert"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_front_door_event
    condition:
      - condition: state
        entity_id: group.family
        state: "not_home"
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable', ''] }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Motion While Away"
          message: "{{ trigger.to_state.attributes.camera_name }}: {{ trigger.to_state.state }}"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
            priority: high
```

### High Confidence Alerts Only

Only alert when AI confidence is above threshold:

```yaml
automation:
  - alias: "ArgusAI - High Confidence Alert"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_front_door_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.confidence | int > 80 }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "{{ trigger.to_state.attributes.camera_name }} ({{ trigger.to_state.attributes.confidence }}%)"
          message: "{{ trigger.to_state.state }}"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
```

### Log Events to Logbook

```yaml
automation:
  - alias: "ArgusAI - Log Events"
    trigger:
      - platform: state
        entity_id:
          - sensor.liveobject_front_door_event
          - sensor.liveobject_backyard_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable', ''] }}"
    action:
      - service: logbook.log
        data:
          name: "ArgusAI"
          message: "{{ trigger.to_state.attributes.camera_name }}: {{ trigger.to_state.state }}"
          entity_id: "{{ trigger.entity_id }}"
```

### Daily Summary Notification

Send a summary of daily events:

```yaml
automation:
  - alias: "ArgusAI - Daily Summary"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Daily Security Summary"
          message: >
            Front Door: {{ states('sensor.liveobject_front_door_events_today') }} events
            Backyard: {{ states('sensor.liveobject_backyard_events_today') }} events
            Driveway: {{ states('sensor.liveobject_driveway_events_today') }} events
```

### Carrier-Specific Package Alert

Alert with carrier information when a package is delivered:

```yaml
automation:
  - alias: "ArgusAI - Package with Carrier"
    trigger:
      - platform: state
        entity_id: sensor.liveobject_front_porch_event
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.smart_detection_type == 'package' }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: >
            {% if trigger.to_state.attributes.delivery_carrier %}
              {{ trigger.to_state.attributes.delivery_carrier | upper }} Package
            {% else %}
              Package Delivered
            {% endif %}
          message: "{{ trigger.to_state.state }}"
          data:
            image: "{{ trigger.to_state.attributes.thumbnail_url }}"
```

## MQTT Topics Reference

### Event Topics

```
{topic_prefix}/camera/{camera_id}/event     # Main event data
{topic_prefix}/camera/{camera_id}/status    # Camera status
{topic_prefix}/camera/{camera_id}/last_event # Last event timestamp
{topic_prefix}/camera/{camera_id}/counts    # Event counts
{topic_prefix}/camera/{camera_id}/activity  # Motion activity state
{topic_prefix}/status                       # ArgusAI connection status (birth/will)
```

### Event Payload Example

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "camera_id": "camera-uuid",
  "camera_name": "Front Door",
  "description": "A person in a blue jacket is approaching the front door, carrying a small package",
  "objects_detected": ["person", "package"],
  "confidence": 92,
  "ai_confidence": 94.5,
  "source_type": "protect",
  "smart_detection_type": "person",
  "is_doorbell_ring": false,
  "timestamp": "2025-12-27T10:30:00Z",
  "thumbnail_url": "http://192.168.1.100:8000/api/v1/events/550e8400-e29b-41d4-a716-446655440000/thumbnail",
  "provider_used": "openai",
  "analysis_mode": "multi_frame",
  "delivery_carrier": null,
  "correlation_group_id": null
}
```

## Troubleshooting

### Devices Not Appearing in Home Assistant

1. Verify MQTT discovery is enabled in Home Assistant:
   - **Settings → Devices & Services → MQTT → Configure → Enable Discovery**
2. Check MQTT broker connection in ArgusAI:
   - **Settings → Integrations → MQTT → Test Connection**
3. Manually publish discovery:
   - **Settings → Integrations → MQTT → Publish Discovery**
4. Restart Home Assistant after enabling MQTT discovery
5. Check discovery prefix matches (default: `homeassistant`)

### Events Not Publishing

1. Check MQTT connection status:
   ```bash
   curl http://localhost:8000/api/v1/integrations/mqtt/status
   ```
   Look for `connected: true`

2. Verify events are being generated:
   ```bash
   curl http://localhost:8000/api/v1/events?limit=5
   ```

3. Monitor MQTT traffic:
   ```bash
   mosquitto_sub -h your-broker -t "liveobject/#" -v
   ```

4. Check ArgusAI logs for MQTT errors:
   - **Settings → Logs** or `grep -i mqtt backend/logs/*.log`

### Notifications Not Showing Images

1. Ensure ArgusAI is accessible from your phone:
   - Local network: Use local IP address
   - Remote: Configure Cloudflare Tunnel or port forwarding

2. Check thumbnail URL in event attributes:
   ```yaml
   {{ trigger.to_state.attributes.thumbnail_url }}
   ```

3. For remote access, update `API_BASE_URL` in ArgusAI to use your external URL

### Connection Drops Frequently

1. Check MQTT broker logs for connection issues
2. Verify network stability between ArgusAI and broker
3. Check broker connection limits
4. ArgusAI auto-reconnects with exponential backoff (1s → 60s max)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/integrations/mqtt/config` | GET | Get current MQTT configuration |
| `/api/v1/integrations/mqtt/config` | PUT | Update MQTT configuration |
| `/api/v1/integrations/mqtt/status` | GET | Get connection status and stats |
| `/api/v1/integrations/mqtt/test` | POST | Test connection without saving |
| `/api/v1/integrations/mqtt/publish-discovery` | POST | Manually publish HA discovery |
