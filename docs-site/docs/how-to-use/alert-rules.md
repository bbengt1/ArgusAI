---
sidebar_position: 6
---

# Alert Rules

Alert Rules let you configure notifications for specific types of events, cameras, and schedules. Instead of being notified for every event, create rules to filter for what matters most.

## Understanding Rules

### How Rules Work

1. An event is detected by a camera
2. ArgusAI evaluates the event against all enabled rules
3. If any rule matches, the configured actions trigger
4. Actions can include push notifications, webhooks, etc.

### Rule Components

| Component | Purpose |
|-----------|---------|
| **Name** | Identifies the rule |
| **Conditions** | What must match for the rule to trigger |
| **Actions** | What happens when the rule triggers |
| **Schedule** | When the rule is active |
| **Enabled** | Toggle the rule on/off |

## Creating Rules

### Basic Rule Setup

1. Navigate to **Alert Rules** or **Settings > Alert Rules**
2. Click **Add Rule**
3. Enter a **Name** (e.g., "Package Deliveries")
4. Configure conditions, actions, and schedule
5. Click **Save**

### Condition Configuration

#### Object Types

Select which detection types trigger the rule:

| Type | Detects |
|------|---------|
| **Person** | Human activity |
| **Vehicle** | Cars, trucks, motorcycles |
| **Package** | Delivery boxes |
| **Animal** | Pets and wildlife |
| **Ring** | Doorbell presses |

Select multiple types if needed. Leave empty to match all types.

#### Camera Selection

Choose which cameras apply to this rule:

- **All Cameras**: Rule applies to every camera
- **Specific Cameras**: Select individual cameras

For location-specific rules (e.g., "Driveway Vehicles"), select only relevant cameras.

#### Confidence Threshold

Set minimum AI confidence to trigger:

- **0-49%**: Low confidence (more false positives)
- **50-74%**: Moderate confidence
- **75-100%**: High confidence (fewer triggers)

Higher thresholds reduce false alerts but may miss valid events.

### Action Configuration

#### Push Notifications

Send browser push notifications:

| Setting | Description |
|---------|-------------|
| **Enable** | Toggle push for this rule |
| **Sound** | Play notification sound |
| **Vibration** | Vibrate on mobile devices |

Push notifications include:
- Event thumbnail
- AI description
- Camera name
- Quick action buttons

:::note
Push notifications require HTTPS. See [Configuration](/docs/getting-started/configuration) for SSL setup.
:::

#### Webhooks

Send event data to external URLs:

| Setting | Description |
|---------|-------------|
| **URL** | Endpoint to receive events |
| **Method** | HTTP method (usually POST) |
| **Headers** | Custom HTTP headers |
| **Retry** | Retry failed requests |

Webhook payload example:

```json
{
  "event_id": "abc123",
  "timestamp": "2025-12-25T10:30:00Z",
  "camera_name": "Front Door",
  "description": "Person approaching front door",
  "detection_type": "person",
  "thumbnail_url": "https://...",
  "confidence": 85
}
```

### Schedule Configuration

Control when the rule is active:

#### Time Range

Set daily active hours:

- **Start Time**: When rule activates (e.g., 10:00 PM)
- **End Time**: When rule deactivates (e.g., 6:00 AM)

For 24-hour rules, set start and end to the same time.

#### Days of Week

Select which days the rule applies:

- Check individual days
- Quick presets: Weekdays, Weekends, Every Day

#### Schedule Examples

| Rule | Schedule |
|------|----------|
| Work hours monitoring | Mon-Fri, 9 AM - 5 PM |
| Night watch | Every day, 10 PM - 6 AM |
| Weekend security | Sat-Sun, All day |

## Managing Rules

### Rule List

The main view shows all rules with:

| Column | Description |
|--------|-------------|
| **Name** | Rule identifier |
| **Conditions** | Summary of what triggers |
| **Actions** | Icons for enabled actions |
| **Schedule** | When active |
| **Status** | Enabled/Disabled toggle |

### Editing Rules

1. Click on a rule name
2. Modify any settings
3. Click **Save**

Changes take effect immediately.

### Enabling/Disabling

Toggle rules on/off without deleting:

- Click the **Enable** toggle
- Disabled rules are grayed out
- Re-enable anytime

### Duplicating Rules

Create a copy of an existing rule:

1. Click the **More** (three dots) menu
2. Select **Duplicate**
3. Edit the copy as needed
4. Save with a new name

### Deleting Rules

Remove a rule permanently:

1. Click the **More** menu
2. Select **Delete**
3. Confirm in the dialog

Deleted rules cannot be recovered.

## Rule Examples

### Package Detection

```
Name: Package Alerts
Object Types: Package
Cameras: Front Door, Porch
Schedule: Mon-Fri 9am-5pm
Actions: Push Notification
```

Get notified when packages arrive during work hours.

### After-Hours Person Detection

```
Name: Night Watch
Object Types: Person
Cameras: All
Schedule: Daily 10pm-6am
Confidence: 75%+
Actions: Push Notification, Webhook
```

Alert for any person detected at night.

### Vehicle in Driveway

```
Name: Driveway Vehicle
Object Types: Vehicle
Cameras: Driveway
Schedule: Always
Confidence: 50%+
Actions: Push Notification
```

Know when any vehicle enters your driveway.

### Doorbell Ring

```
Name: Doorbell
Object Types: Ring
Cameras: Front Door
Schedule: Always
Actions: Push Notification (with sound)
```

Never miss a doorbell press.

## Webhook Integrations

### Slack

1. Create a Slack incoming webhook
2. Add webhook URL to rule
3. Events post to your Slack channel

### Discord

1. Create a Discord webhook (Server Settings > Integrations)
2. Use webhook URL in rule
3. Add header: `Content-Type: application/json`

### Home Assistant

1. Use REST API endpoint
2. Configure with long-lived access token
3. Events trigger automations in HA

### IFTTT

1. Create a Webhooks applet
2. Use the IFTTT webhook URL
3. Configure what happens when triggered

## Tips

### Avoiding Alert Fatigue

- Start with high confidence thresholds
- Be specific about cameras
- Use schedules to limit when rules fire
- Create fewer, more targeted rules

### Testing Rules

1. Create a rule with your settings
2. Trigger an event in front of the camera
3. Verify notification/webhook received
4. Adjust settings as needed

### Rule Organization

- Use descriptive names
- Group related rules logically
- Document complex rules with notes
- Review and clean up periodically
