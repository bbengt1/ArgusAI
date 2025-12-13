# Webhook Integration Guide

Connect ArgusAI to external systems using webhooks. This guide covers webhook configuration, payload formats, and integration examples.

---

## Overview

ArgusAI can send HTTP POST requests to external URLs when alert rules trigger. Use webhooks to:

- Send alerts to Slack, Discord, or Teams
- Trigger Home Assistant automations
- Log events to external systems
- Integrate with custom applications

---

## Configuring Webhooks

### Via Alert Rules

1. Navigate to **Rules** > **Create Rule** or edit existing rule
2. In the **Actions** section, enable **Webhook**
3. Enter the webhook URL
4. Optionally add custom headers (e.g., Authorization)
5. Save the rule

### Webhook Settings

| Setting | Description |
|---------|-------------|
| **URL** | HTTPS endpoint to receive POST requests |
| **Headers** | Custom HTTP headers (JSON object) |
| **Retry** | Automatic retry on failure (3 attempts) |
| **Timeout** | Request timeout (10 seconds default) |

---

## Webhook Payload

When an alert triggers, ArgusAI sends a JSON payload:

```json
{
  "event_type": "alert_triggered",
  "timestamp": "2025-01-15T10:30:00Z",
  "rule": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Person at Front Door"
  },
  "event": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "camera_id": "550e8400-e29b-41d4-a716-446655440002",
    "camera_name": "Front Door",
    "description": "A person in a blue jacket approached the front door and rang the doorbell",
    "enriched_description": "John arrived at the front door",
    "timestamp": "2025-01-15T10:29:55Z",
    "source_type": "protect",
    "smart_detection_type": "person",
    "thumbnail_url": "http://localhost:8000/api/v1/events/550e8400-e29b-41d4-a716-446655440001/thumbnail",
    "confidence_score": 0.92,
    "anomaly_score": 15,
    "recognition_status": "known"
  },
  "matched_entities": [
    {
      "id": "entity-uuid",
      "name": "John",
      "entity_type": "person",
      "is_vip": true
    }
  ]
}
```

### Payload Fields

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | string | Always `alert_triggered` |
| `timestamp` | string | ISO 8601 timestamp of alert |
| `rule.id` | string | UUID of the triggered rule |
| `rule.name` | string | Human-readable rule name |
| `event.id` | string | UUID of the triggering event |
| `event.camera_id` | string | Camera UUID |
| `event.camera_name` | string | Camera display name |
| `event.description` | string | AI-generated description |
| `event.enriched_description` | string | Description with entity names (if applicable) |
| `event.timestamp` | string | Event occurrence time |
| `event.source_type` | string | `rtsp`, `usb`, or `protect` |
| `event.smart_detection_type` | string | `person`, `vehicle`, `package`, `animal`, `ring` |
| `event.thumbnail_url` | string | URL to fetch event thumbnail |
| `event.confidence_score` | float | AI confidence (0-1) |
| `event.anomaly_score` | integer | Anomaly score (0-100) |
| `event.recognition_status` | string | `known`, `stranger`, `unknown`, or null |
| `matched_entities` | array | Recognized entities in event |

---

## Integration Examples

### Slack

**Webhook URL:** Create an [Incoming Webhook](https://api.slack.com/messaging/webhooks) in Slack.

**ArgusAI sends standard JSON.** Use Slack Workflow Builder or a middleware to transform:

```python
# Example middleware (Flask)
from flask import Flask, request
import requests

app = Flask(__name__)
SLACK_WEBHOOK = "https://hooks.slack.com/services/T00/B00/xxx"

@app.route("/argusai-webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    event = data["event"]

    slack_message = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{data['rule']['name']}*\n{event['description']}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Camera: {event['camera_name']}"},
                    {"type": "mrkdwn", "text": f"Time: {event['timestamp']}"}
                ]
            }
        ]
    }

    requests.post(SLACK_WEBHOOK, json=slack_message)
    return "OK", 200
```

### Discord

**Webhook URL:** Create a webhook in Discord channel settings.

Discord accepts a similar format:

```python
# Transform for Discord
discord_message = {
    "embeds": [{
        "title": data["rule"]["name"],
        "description": event["description"],
        "color": 15158332,  # Red for alerts
        "fields": [
            {"name": "Camera", "value": event["camera_name"], "inline": True},
            {"name": "Detection", "value": event["smart_detection_type"], "inline": True}
        ],
        "thumbnail": {"url": event["thumbnail_url"]},
        "timestamp": event["timestamp"]
    }]
}
```

### Home Assistant

Use Home Assistant's [webhook automation trigger](https://www.home-assistant.io/docs/automation/trigger/#webhook-trigger):

**1. Create webhook automation in Home Assistant:**

```yaml
# configuration.yaml or automations.yaml
automation:
  - alias: "ArgusAI Alert Handler"
    trigger:
      - platform: webhook
        webhook_id: argusai_alerts
        allowed_methods:
          - POST
    action:
      - service: notify.mobile_app_phone
        data:
          title: "{{ trigger.json.rule.name }}"
          message: "{{ trigger.json.event.description }}"
          data:
            image: "{{ trigger.json.event.thumbnail_url }}"
```

**2. Configure ArgusAI webhook URL:**
```
http://homeassistant.local:8123/api/webhook/argusai_alerts
```

### Node-RED

**1. Add HTTP In node** with POST method at `/argusai-webhook`

**2. Process payload:**

```javascript
// Function node
const payload = msg.payload;
const event = payload.event;

msg.notification = {
    title: payload.rule.name,
    message: event.description,
    camera: event.camera_name,
    thumbnail: event.thumbnail_url
};

return msg;
```

**3. Send to desired output** (Telegram, email, etc.)

### IFTTT

Use IFTTT Webhooks service:

**1. Create IFTTT Applet:**
- Trigger: Webhooks > Receive web request
- Event name: `argusai_alert`

**2. Use middleware to transform:**

```python
IFTTT_KEY = "your-ifttt-key"
IFTTT_EVENT = "argusai_alert"

@app.route("/argusai-webhook", methods=["POST"])
def handle_webhook():
    data = request.json

    # IFTTT accepts value1, value2, value3
    ifttt_payload = {
        "value1": data["rule"]["name"],
        "value2": data["event"]["description"],
        "value3": data["event"]["camera_name"]
    }

    requests.post(
        f"https://maker.ifttt.com/trigger/{IFTTT_EVENT}/with/key/{IFTTT_KEY}",
        json=ifttt_payload
    )
    return "OK", 200
```

### Pushover

```python
import requests

PUSHOVER_TOKEN = "your-app-token"
PUSHOVER_USER = "your-user-key"

@app.route("/argusai-webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    event = data["event"]

    # Download thumbnail
    thumbnail = requests.get(event["thumbnail_url"]).content

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "title": data["rule"]["name"],
            "message": event["description"],
            "url": f"http://localhost:3000/events/{event['id']}",
            "url_title": "View Event"
        },
        files={"attachment": ("thumbnail.jpg", thumbnail, "image/jpeg")}
    )
    return "OK", 200
```

### Telegram

```python
import requests

BOT_TOKEN = "your-bot-token"
CHAT_ID = "your-chat-id"

@app.route("/argusai-webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    event = data["event"]

    # Send message with photo
    message = f"*{data['rule']['name']}*\n\n{event['description']}\n\nCamera: {event['camera_name']}"

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "photo": event["thumbnail_url"],
            "caption": message,
            "parse_mode": "Markdown"
        }
    )
    return "OK", 200
```

---

## Security Best Practices

### Use HTTPS

Always use HTTPS URLs for webhook endpoints to encrypt data in transit.

### Verify Webhook Source

ArgusAI includes a signature header for verification:

```
X-ArgusAI-Signature: sha256=abc123...
```

Verify in your endpoint:

```python
import hmac
import hashlib

WEBHOOK_SECRET = "your-secret"  # Configure in ArgusAI settings

def verify_signature(payload, signature):
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.route("/webhook", methods=["POST"])
def handle():
    signature = request.headers.get("X-ArgusAI-Signature")
    if not verify_signature(request.data, signature):
        return "Invalid signature", 401
    # Process webhook...
```

### Custom Headers

Add authentication headers in ArgusAI:

```json
{
  "Authorization": "Bearer your-token",
  "X-Custom-Header": "value"
}
```

### IP Allowlisting

Restrict your webhook endpoint to accept requests only from your ArgusAI server's IP address.

---

## Retry Behavior

Failed webhooks are retried automatically:

| Attempt | Delay |
|---------|-------|
| 1st retry | 1 minute |
| 2nd retry | 5 minutes |
| 3rd retry | 15 minutes |

After 3 failures, the webhook is marked as failed for that event.

### Response Requirements

Your endpoint should:
- Return `2xx` status for success
- Respond within 10 seconds
- Be idempotent (handle duplicate deliveries)

---

## Testing Webhooks

### Test Endpoint

Use webhook.site or requestbin.com to test:

1. Get a test URL from webhook.site
2. Configure it as your webhook URL
3. Trigger an alert rule
4. Inspect the received payload

### Local Testing

Use ngrok to expose local endpoints:

```bash
# Start ngrok
ngrok http 5000

# Use the ngrok URL in ArgusAI
# https://abc123.ngrok.io/webhook
```

### Manual Trigger

Use the alert rule test endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/alert-rules/{rule_id}/test
```

---

## Troubleshooting

### Webhook Not Firing

1. Check rule is enabled
2. Verify rule conditions match the event
3. Check webhook URL is correct
4. Review backend logs for errors

### Timeout Errors

- Ensure endpoint responds within 10 seconds
- Process asynchronously if needed
- Return 200 immediately, process in background

### Invalid Payload

- Check Content-Type is `application/json`
- Verify JSON parsing in your endpoint
- Log raw request body for debugging

---

## Related Resources

- [Alert Rules](user-guide.md#alert-rules) - Creating alert rules
- [API Reference](api-reference.md#alert-rules) - Alert rules API
- [Home Assistant Integration](user-guide.md#home-assistant-via-mqtt) - MQTT alternative

---

*Last updated: December 2025*
