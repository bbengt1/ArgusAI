# ArgusAI API Quick Reference

One-page endpoint summary with curl examples.

**Base URL:** `http://localhost:8000/api/v1`

---

## Cameras

```bash
# List all cameras
curl http://localhost:8000/api/v1/cameras

# Create RTSP camera
curl -X POST http://localhost:8000/api/v1/cameras \
  -H "Content-Type: application/json" \
  -d '{"name": "Front Door", "source_type": "rtsp", "rtsp_url": "rtsp://192.168.1.50:554/stream1"}'

# Get camera preview (base64 JPEG)
curl http://localhost:8000/api/v1/cameras/{id}/preview

# Trigger manual AI analysis
curl -X POST http://localhost:8000/api/v1/cameras/{id}/analyze
```

---

## Events

```bash
# List recent events
curl "http://localhost:8000/api/v1/events?limit=20"

# Search events
curl "http://localhost:8000/api/v1/events?search_query=person+front+door"

# Filter by detection type
curl "http://localhost:8000/api/v1/events?smart_detection_type=person"

# Filter by source
curl "http://localhost:8000/api/v1/events?source_type=protect"

# Filter by date range
curl "http://localhost:8000/api/v1/events?start_time=2025-01-14T00:00:00Z&end_time=2025-01-15T00:00:00Z"

# Filter by anomaly severity
curl "http://localhost:8000/api/v1/events?anomaly_severity=high"

# Get single event with related events
curl http://localhost:8000/api/v1/events/{id}

# Export as CSV
curl "http://localhost:8000/api/v1/events/export?format=csv" > events.csv

# Re-analyze event
curl -X POST http://localhost:8000/api/v1/events/{id}/reanalyze \
  -H "Content-Type: application/json" \
  -d '{"analysis_mode": "video_native"}'

# Submit feedback
curl -X POST http://localhost:8000/api/v1/events/{id}/feedback \
  -H "Content-Type: application/json" \
  -d '{"rating": "helpful"}'
```

---

## UniFi Protect

```bash
# Test connection (before saving)
curl -X POST http://localhost:8000/api/v1/protect/controllers/test \
  -H "Content-Type: application/json" \
  -d '{"host": "192.168.1.1", "username": "argusai", "password": "secret"}'

# Add controller
curl -X POST http://localhost:8000/api/v1/protect/controllers \
  -H "Content-Type: application/json" \
  -d '{"name": "Home UDM", "host": "192.168.1.1", "username": "argusai", "password": "secret"}'

# Discover cameras
curl http://localhost:8000/api/v1/protect/controllers/{id}/cameras

# Enable camera for AI
curl -X POST http://localhost:8000/api/v1/protect/controllers/{id}/cameras/{cam_id}/enable

# Set detection filters
curl -X PUT http://localhost:8000/api/v1/protect/controllers/{id}/cameras/{cam_id}/filters \
  -H "Content-Type: application/json" \
  -d '{"smart_detection_types": ["person", "package"]}'
```

---

## Entities (Person/Vehicle Recognition)

```bash
# List all entities
curl http://localhost:8000/api/v1/context/entities

# List named entities only
curl "http://localhost:8000/api/v1/context/entities?named_only=true"

# List VIP entities
curl http://localhost:8000/api/v1/context/entities/vip

# List blocked entities
curl http://localhost:8000/api/v1/context/entities/blocked

# Update entity (name, VIP, blocked)
curl -X PUT http://localhost:8000/api/v1/context/entities/{id} \
  -H "Content-Type: application/json" \
  -d '{"name": "John Smith", "is_vip": true, "is_blocked": false}'

# Find similar events
curl http://localhost:8000/api/v1/context/similar/{event_id}
```

---

## Anomaly Detection

```bash
# Get anomaly score for event
curl -X POST http://localhost:8000/api/v1/context/anomaly/score \
  -H "Content-Type: application/json" \
  -d '{"event_id": "uuid"}'

# Get camera baseline
curl http://localhost:8000/api/v1/context/anomaly/baseline/{camera_id}

# Get activity patterns
curl http://localhost:8000/api/v1/context/patterns/{camera_id}
```

---

## Alert Rules

```bash
# List rules
curl http://localhost:8000/api/v1/alert-rules

# Create rule
curl -X POST http://localhost:8000/api/v1/alert-rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Person at Night",
    "is_enabled": true,
    "conditions": {
      "detection_types": ["person"],
      "time_range": {"start": "22:00", "end": "06:00"}
    },
    "actions": {"push_notification": true}
  }'

# Create entity-based rule
curl -X POST http://localhost:8000/api/v1/alert-rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alert for John",
    "conditions": {"entity_names": ["John*"]},
    "actions": {"push_notification": true}
  }'

# Test rule
curl -X POST http://localhost:8000/api/v1/alert-rules/{id}/test
```

---

## Voice Queries

```bash
# Ask about events
curl -X POST http://localhost:8000/api/v1/voice/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What happened at the front door today?"}'

# Query specific camera
curl -X POST http://localhost:8000/api/v1/voice/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Any activity this morning?", "camera_id": "uuid"}'
```

---

## Activity Summaries

```bash
# Generate summary for last 24 hours
curl -X POST http://localhost:8000/api/v1/summaries/generate \
  -H "Content-Type: application/json" \
  -d '{"hours_back": 24}'

# Get today's daily digest
curl http://localhost:8000/api/v1/summaries/daily

# Get recent summaries
curl http://localhost:8000/api/v1/summaries/recent
```

---

## Push Notifications

```bash
# Subscribe (from browser - use Push API)
curl -X POST http://localhost:8000/api/v1/push/subscribe \
  -H "Content-Type: application/json" \
  -d '{"subscription": {...}, "device_name": "My Phone"}'

# Test push notification
curl -X POST http://localhost:8000/api/v1/push/test

# List subscriptions
curl http://localhost:8000/api/v1/push/subscriptions
```

---

## Integrations

### MQTT (Home Assistant)

```bash
# Get MQTT config
curl http://localhost:8000/api/v1/integrations/mqtt/config

# Update MQTT config
curl -X PUT http://localhost:8000/api/v1/integrations/mqtt/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "host": "192.168.1.100", "port": 1883}'

# Test MQTT connection
curl -X POST http://localhost:8000/api/v1/integrations/mqtt/test \
  -H "Content-Type: application/json" \
  -d '{"host": "192.168.1.100", "port": 1883}'

# Publish Home Assistant discovery
curl -X POST http://localhost:8000/api/v1/integrations/mqtt/publish-discovery
```

### HomeKit

```bash
# Get HomeKit status
curl http://localhost:8000/api/v1/integrations/homekit/status

# Get pairing code
curl http://localhost:8000/api/v1/integrations/homekit/pairing-code

# Enable HomeKit
curl -X PUT http://localhost:8000/api/v1/integrations/homekit/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

---

## AI Providers

```bash
# Get usage statistics
curl http://localhost:8000/api/v1/ai/usage

# Get provider capabilities
curl http://localhost:8000/api/v1/ai/capabilities
```

---

## Feedback Statistics

```bash
# Get feedback stats
curl http://localhost:8000/api/v1/feedback/stats

# Get prompt improvement insights
curl http://localhost:8000/api/v1/feedback/prompt-insights
```

---

## System

```bash
# Health check
curl http://localhost:8000/api/v1/system/health

# Get settings
curl http://localhost:8000/api/v1/system/settings

# Update settings
curl -X PUT http://localhost:8000/api/v1/system/settings \
  -H "Content-Type: application/json" \
  -d '{"retention_days": 30, "daily_cost_limit": 5.00}'

# Get storage info
curl http://localhost:8000/api/v1/system/storage

# Create backup
curl -X POST http://localhost:8000/api/v1/system/backup
```

---

## Common Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `limit` | Max results | `?limit=50` |
| `offset` | Pagination offset | `?offset=20` |
| `camera_id` | Filter by camera | `?camera_id=uuid` |
| `start_time` | Start of range | `?start_time=2025-01-14T00:00:00Z` |
| `end_time` | End of range | `?end_time=2025-01-15T00:00:00Z` |
| `source_type` | Camera source | `?source_type=protect` |
| `smart_detection_type` | Detection filter | `?smart_detection_type=person` |
| `search_query` | Full-text search | `?search_query=delivery` |

---

## Response Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `204` | Deleted |
| `400` | Bad request |
| `404` | Not found |
| `422` | Validation error |
| `429` | Rate limited |
| `500` | Server error |

---

*Full documentation: [API Reference](api-reference.md)*
