# ArgusAI User Guide

**AI-Powered Security Event Detection for Your Home**

This guide covers everything you need to know to set up, configure, and use ArgusAI effectively.

---

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [System Requirements](#system-requirements)
  - [Installation](#installation)
  - [First-Run Setup](#first-run-setup)
- [Dashboard Overview](#dashboard-overview)
- [Camera Setup](#camera-setup)
  - [UniFi Protect Cameras](#unifi-protect-cameras)
  - [RTSP IP Cameras](#rtsp-ip-cameras)
  - [USB Webcams](#usb-webcams)
- [AI Configuration](#ai-configuration)
  - [Provider Setup](#provider-setup)
  - [Choosing the Right Provider](#choosing-the-right-provider)
  - [Analysis Modes](#analysis-modes)
- [Events and Timeline](#events-and-timeline)
  - [Viewing Events](#viewing-events)
  - [Searching and Filtering](#searching-and-filtering)
  - [Event Details](#event-details)
  - [User Feedback](#user-feedback)
- [Alert Rules](#alert-rules)
  - [Creating Rules](#creating-rules)
  - [Webhook Integration](#webhook-integration)
- [Push Notifications](#push-notifications)
  - [Enabling Push](#enabling-push)
  - [Notification Preferences](#notification-preferences)
- [Smart Home Integration](#smart-home-integration)
  - [Home Assistant via MQTT](#home-assistant-via-mqtt)
  - [HomeKit Integration](#homekit-integration)
  - [Voice Queries](#voice-queries)
- [Activity Summaries](#activity-summaries)
  - [Daily Digests](#daily-digests)
  - [On-Demand Summaries](#on-demand-summaries)
- [Entity Management](#entity-management)
  - [Recognized People and Vehicles](#recognized-people-and-vehicles)
  - [VIP Alerts and Blocklist](#vip-alerts-and-blocklist)
  - [Entity-Based Alert Rules](#entity-based-alert-rules)
  - [Similar Events](#similar-events)
- [Anomaly Detection](#anomaly-detection)
  - [Baseline Learning](#baseline-learning)
  - [Viewing Anomaly Scores](#viewing-anomaly-scores)
  - [Anomaly Alerts](#anomaly-alerts)
- [Cost Monitoring](#cost-monitoring)
  - [Viewing AI Costs](#viewing-ai-costs)
  - [Setting Cost Limits](#setting-cost-limits)
- [Settings Reference](#settings-reference)
- [Troubleshooting](#troubleshooting)

---

## Introduction

ArgusAI transforms your security cameras into an intelligent monitoring system. Instead of reviewing hours of footage, you receive natural language descriptions of what's happening: "A delivery person left a package at the front door" or "Two people walking dogs passed by the driveway."

**Key capabilities:**

- Connect UniFi Protect, RTSP IP cameras, or USB webcams
- AI-powered event descriptions using multiple providers
- Smart filtering by person, vehicle, package, or animal
- Real-time push notifications with thumbnails
- Home Assistant and HomeKit integration
- Daily activity summaries and pattern detection

---

## Getting Started

### System Requirements

**Hardware:**
- Computer or server to run the backend (Raspberry Pi 4+, NAS, or desktop)
- Network access to your cameras

**Software:**
- Python 3.11 or higher
- Node.js 18 or higher
- Web browser (Chrome, Firefox, Safari, Edge)

**Optional:**
- UniFi Protect controller (UDM, Cloud Key, or NVR)
- AI API key from OpenAI, Anthropic, Google, or xAI

### Installation

The easiest method is the automated installation script:

```bash
# Download and run the installer
chmod +x install.sh
./install.sh
```

The installer:
1. Checks system dependencies
2. Creates Python virtual environment
3. Installs backend and frontend packages
4. Generates encryption keys
5. Initializes the database

After installation completes, start the servers:

```bash
# Terminal 1: Start backend
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### First-Run Setup

1. Open your browser to `http://localhost:3000/setup`
2. Follow the setup wizard to configure:
   - AI provider credentials
   - Your first camera connection
   - Basic preferences

---

## Dashboard Overview

The dashboard (`http://localhost:3000`) shows:

```
+------------------+----------------------------------+
|                  |                                  |
|  Camera Grid     |  Event Timeline                  |
|  (Live Preview)  |  (Recent Activity)               |
|                  |                                  |
+------------------+----------------------------------+
|                                                     |
|  Quick Stats: Events Today | Active Cameras | Alerts|
|                                                     |
+-----------------------------------------------------+
```

**Navigation:**
- **Dashboard** - Live cameras and recent events
- **Events** - Full event timeline with search
- **Cameras** - Camera management and status
- **Rules** - Alert rule configuration
- **Summaries** - Activity summaries and digests
- **Entities** - Recognized people and vehicles
- **Settings** - System configuration

---

## Camera Setup

### UniFi Protect Cameras

UniFi Protect provides the best integration with real-time smart detection events.

**Adding a Protect Controller:**

1. Navigate to **Settings** > **UniFi Protect**
2. Click **Add Controller**
3. Enter connection details:
   - **Name**: Descriptive label (e.g., "Home UDM Pro")
   - **Host**: IP address or hostname of your controller
   - **Port**: Usually 443 (default)
   - **Username**: Local Protect account (not UniFi SSO)
   - **Password**: Account password
   - **Verify SSL**: Disable for self-signed certificates
4. Click **Test Connection**
5. If successful, click **Save**

**Enabling Cameras:**

1. After adding a controller, click **Discover Cameras**
2. You'll see all cameras connected to that controller
3. Toggle **Enable AI** for cameras you want to monitor
4. Click **Filters** to select detection types:
   - **Person** - Human detection
   - **Vehicle** - Cars, trucks, motorcycles
   - **Package** - Delivery detection
   - **Animal** - Pets and wildlife
   - **All Motion** - Any movement (can be noisy)

**Important:** Create a dedicated local account on your Protect controller for ArgusAI. UniFi SSO/Cloud accounts are not supported.

### RTSP IP Cameras

RTSP cameras work with most IP camera brands (Hikvision, Dahua, Reolink, Amcrest, etc.).

**Adding an RTSP Camera:**

1. Navigate to **Cameras** > **Add Camera**
2. Select **RTSP Camera**
3. Enter the RTSP URL:
   ```
   rtsp://username:password@192.168.1.50:554/stream1
   ```
4. Configure options:
   - **Name**: Descriptive label
   - **Motion Detection**: Enable to detect movement
   - **Sensitivity**: Adjust for your environment
5. Click **Test Connection**
6. If preview appears, click **Save**

**Finding your RTSP URL:**
- Check your camera's documentation
- Common patterns:
  - Hikvision: `rtsp://user:pass@ip:554/Streaming/Channels/101`
  - Dahua: `rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0`
  - Reolink: `rtsp://user:pass@ip:554/h264Preview_01_main`

### USB Webcams

USB cameras are useful for testing or basic monitoring.

**Adding a USB Camera:**

1. Navigate to **Cameras** > **Add Camera**
2. Select **USB Camera**
3. Choose the device index:
   - **0** - Primary/built-in camera
   - **1** - Secondary USB camera
   - **2, 3...** - Additional cameras
4. Enter a descriptive name
5. Click **Test Connection**
6. If preview appears, click **Save**

---

## AI Configuration

### Provider Setup

ArgusAI supports multiple AI providers with automatic fallback:

| Provider | Model | Best For |
|----------|-------|----------|
| OpenAI | GPT-4o mini | Best balance of cost and quality |
| xAI | Grok 2 Vision | Fast responses, good accuracy |
| Anthropic | Claude 3 Haiku | Reliable, consistent descriptions |
| Google | Gemini Flash | Free tier available |

**Configuring a Provider:**

1. Navigate to **Settings** > **AI Providers**
2. Click on the provider you want to configure
3. Enter your API key
4. Click **Test** to verify the key works
5. Click **Save**

**Getting API Keys:**
- OpenAI: [platform.openai.com](https://platform.openai.com)
- xAI: [console.x.ai](https://console.x.ai)
- Anthropic: [console.anthropic.com](https://console.anthropic.com)
- Google: [aistudio.google.com](https://aistudio.google.com)

### Choosing the Right Provider

**For most users:** Start with OpenAI GPT-4o mini. It provides excellent descriptions at low cost (~$0.001 per event).

**Fallback order:** Configure multiple providers. If your primary fails (rate limit, outage), ArgusAI automatically tries the next one:
```
OpenAI → xAI Grok → Claude → Gemini
```

Drag and drop providers in Settings to customize the fallback order.

### Analysis Modes

For UniFi Protect cameras, choose how events are analyzed:

| Mode | Description | Quality | Cost |
|------|-------------|---------|------|
| Single Frame | Snapshot at event time | Good | Lowest |
| Multi-Frame | 3-5 key frames from video | Better | Medium |
| Video Native | Full video clip to AI | Best | Highest |

Change analysis mode per-camera in **Cameras** > click camera > **Analysis Mode**.

---

## Events and Timeline

### Viewing Events

The **Events** page shows all detected activity in chronological order.

Each event card displays:
- Thumbnail image
- AI-generated description
- Timestamp
- Camera name
- Detection type badges (Person, Vehicle, etc.)
- Source badge (Protect, RTSP, USB)

### Searching and Filtering

**Search bar:** Type natural language queries:
- "person at front door"
- "vehicle in driveway"
- "package delivery"

**Filters:**
- **Camera**: Show events from specific cameras
- **Date Range**: Select time period
- **Detection Type**: Person, Vehicle, Package, Animal
- **Source**: Protect, RTSP, USB
- **Analysis Mode**: Single, Multi-frame, Video

### Event Details

Click any event card to see:
- Full-size image or key frames gallery
- Complete AI description
- Confidence score (high/medium/low)
- Related events from other cameras
- Similar past events

### User Feedback

Help improve AI accuracy by providing feedback:

1. On any event card, find the feedback buttons
2. Click **thumbs up** if the description is accurate
3. Click **thumbs down** if incorrect
4. Optionally add a correction note

Your feedback helps ArgusAI generate better descriptions over time.

---

## Alert Rules

### Creating Rules

Alert rules trigger notifications when specific conditions are met.

**Creating a Rule:**

1. Navigate to **Rules** > **Create Rule**
2. Configure conditions:
   - **Name**: Descriptive rule name
   - **Cameras**: Which cameras to monitor (or all)
   - **Detection Types**: Person, Vehicle, Package, etc.
   - **Keywords**: Match words in AI descriptions
   - **Schedule**: Active times (optional)
3. Configure actions:
   - In-app notification
   - Push notification
   - Webhook call
4. Click **Save**

**Example Rules:**
- "Package at Front Door" - Trigger when package detected at front camera
- "Person at Night" - Trigger for any person 10 PM - 6 AM
- "Vehicle in Driveway" - Alert when vehicle enters driveway

### Webhook Integration

Send alerts to external systems:

1. In the rule editor, enable **Webhook**
2. Enter the webhook URL
3. Choose payload format (JSON)
4. Optionally add custom headers

**Webhook payload example:**
```json
{
  "event_id": "abc123",
  "camera": "Front Door",
  "description": "A person in a blue jacket approached the door",
  "timestamp": "2024-01-15T14:30:00Z",
  "thumbnail_url": "http://localhost:8000/api/v1/events/abc123/thumbnail"
}
```

---

## Push Notifications

### Enabling Push

Receive instant notifications on your phone or desktop:

1. Navigate to **Settings** > **Notifications**
2. Click **Enable Push Notifications**
3. Allow notifications when prompted by your browser
4. You're now subscribed!

**PWA Installation:**
For the best mobile experience, install ArgusAI as a Progressive Web App:
1. Open ArgusAI in Chrome/Safari
2. Click the install prompt or menu > "Add to Home Screen"
3. ArgusAI appears as an app with offline support

### Notification Preferences

Customize what triggers notifications:

- **All Events**: Every detection
- **Alerts Only**: Only when rules trigger
- **High Priority**: Person/Package detection only
- **Quiet Hours**: Suppress notifications during set times

---

## Smart Home Integration

### Home Assistant via MQTT

Connect ArgusAI to Home Assistant for automations.

**Setup:**

1. Navigate to **Settings** > **Integrations** > **MQTT**
2. Enter your MQTT broker details:
   - **Host**: MQTT broker IP (e.g., Home Assistant IP)
   - **Port**: Usually 1883
   - **Username/Password**: If required
3. Click **Test Connection**
4. Enable **Home Assistant Auto-Discovery**
5. Click **Save**

**What's created in Home Assistant:**
- Binary sensors for each camera (motion detected)
- Sensors showing last event description
- Camera status entities

**Example Automation:**
```yaml
automation:
  - alias: "Announce Front Door Activity"
    trigger:
      - platform: state
        entity_id: sensor.argusai_front_door_last_event
    action:
      - service: tts.speak
        data:
          message: "{{ states('sensor.argusai_front_door_last_event') }}"
```

### HomeKit Integration

Access cameras as motion sensors in Apple Home.

**Setup:**

1. Navigate to **Settings** > **Integrations** > **HomeKit**
2. Click **Enable HomeKit**
3. Note the pairing code displayed
4. On your iPhone/iPad:
   - Open Home app
   - Tap **+** > **Add Accessory**
   - Select **ArgusAI Bridge**
   - Enter the pairing code

**Features:**
- Each camera appears as a motion sensor
- Motion triggers when events are detected
- Use in HomeKit automations and scenes

### Voice Queries

Ask about activity using natural language:

**API Endpoint:** `POST /api/v1/voice/query`

**Example queries:**
- "What's happening at the front door?"
- "Any activity this morning?"
- "Was there anyone in the backyard today?"

**Response:**
```
"I found 3 events at the front door today. I saw 2 persons and 1 package."
```

This API is designed for voice assistant integration (custom Alexa skills, Google Actions, Siri Shortcuts).

---

## Activity Summaries

### Daily Digests

Receive a summary of the day's activity:

1. Navigate to **Settings** > **Summaries**
2. Enable **Daily Digest**
3. Set your preferred delivery time
4. Choose delivery method:
   - In-app notification
   - Push notification
   - Email (if configured)

**Digest contents:**
- Total events by camera
- Notable detections
- Activity patterns
- Unusual events highlighted

### On-Demand Summaries

Generate summaries anytime:

1. Navigate to **Summaries**
2. Select time range (Today, Yesterday, Last 7 days, Custom)
3. Select cameras to include
4. Click **Generate Summary**

The AI creates a narrative summary of activity during that period.

---

## Entity Management

### Recognized People and Vehicles

ArgusAI learns to recognize recurring visitors using privacy-first face and vehicle embeddings:

1. Navigate to **Entities**
2. View detected entities grouped by type (Person, Vehicle)
3. Click an entity to see:
   - All events featuring this entity
   - First and last seen dates
   - Frequency statistics
   - Recognition status badge

**Recognition Status:**
- **Known** - Named entity (you've assigned a name)
- **Stranger** - Seen before but not named
- **Unknown** - First-time visitor

**Naming Entities:**
1. Click an unknown entity
2. Enter a name (e.g., "Mail Carrier", "John Smith")
3. Future events will show personalized descriptions:
   - Before: "A person approached the front door"
   - After: "John arrived at the front door"

### VIP Alerts and Blocklist

Control notifications for specific people and vehicles:

**VIP Entities:**

Mark important entities as VIP to receive priority notifications:

1. Navigate to **Entities**
2. Click on an entity
3. Toggle **VIP** on
4. VIP notifications appear with a ⭐ indicator and distinct styling

**Use cases:**
- Family members returning home
- Expected delivery drivers
- Important visitors

**Blocklist:**

Suppress notifications for entities you don't need alerts about:

1. Navigate to **Entities**
2. Click on an entity
3. Toggle **Blocked** on
4. Events are still recorded, but no notifications are sent

**Use cases:**
- Household members (you don't need alerts for yourself)
- Regular mail carriers
- Neighbors who frequently pass by

**Viewing VIP and Blocked Lists:**
- **Settings** > **Entities** > **VIP List** - All VIP entities
- **Settings** > **Entities** > **Blocked List** - All blocked entities

### Entity-Based Alert Rules

Create alert rules that trigger for specific named entities:

1. Navigate to **Rules** > **Create Rule**
2. In the conditions section, find **Entity Matching**
3. Choose matching method:
   - **Specific Entities**: Select from your named entities
   - **Name Patterns**: Use wildcards (e.g., "John*" matches John, Johnny)
4. Configure other conditions and actions
5. Click **Save**

**Example Rules:**
- "Alert when John arrives" - Trigger only for entity named John
- "Alert for delivery*" - Match "Delivery Driver", "Delivery Person", etc.
- "Alert for unknown person at night" - Combine stranger status with time schedule

### Similar Events

Find related past events:

1. Open any event detail page
2. Scroll to **Similar Events**
3. View events with similar visual characteristics

This helps track recurring visitors or identify patterns.

---

## Anomaly Detection

ArgusAI learns your property's normal activity patterns and alerts you to unusual behavior.

### Baseline Learning

The system automatically builds a baseline of normal activity:

1. **Data Collection**: ArgusAI analyzes events over time to understand:
   - Typical activity hours per camera
   - Normal event frequency
   - Common detection types
   - Day-of-week patterns

2. **Learning Period**: The baseline improves over approximately 7 days of activity

3. **Viewing Baseline Data**:
   - Navigate to **Settings** > **Anomaly Detection**
   - View learned patterns per camera
   - See activity heatmaps by hour and day

**What the baseline tracks:**
- Event frequency per hour
- Detection type distribution
- Activity timing patterns
- Typical event characteristics

### Viewing Anomaly Scores

Each event receives an anomaly score indicating how unusual it is:

**Score Levels:**
| Score | Label | Meaning |
|-------|-------|---------|
| 0-30 | Normal | Typical activity for this time/camera |
| 31-60 | Slightly Unusual | Somewhat outside normal patterns |
| 61-80 | Unusual | Notably different from baseline |
| 81-100 | Highly Anomalous | Very rare or unexpected activity |

**Viewing Scores:**
1. Open any event card
2. Look for the **Anomaly Score** indicator
3. Click for details on why it was flagged

**Filtering by Anomaly:**
1. On the Events page, use the **Anomaly** filter
2. Select threshold (e.g., "Show Unusual and above")
3. View only events that deviate from normal patterns

### Anomaly Alerts

Create alerts for unusual activity:

1. Navigate to **Rules** > **Create Rule**
2. Enable **Anomaly Detection** condition
3. Set the threshold:
   - **Unusual** (61+) - Moderate sensitivity
   - **Highly Anomalous** (81+) - High confidence only
4. Configure notification preferences
5. Click **Save**

**Example Use Cases:**
- Alert for any activity between 2-5 AM (unusual hours)
- Alert for front door activity when typically quiet
- Detect unusual vehicle presence in driveway

---

## Cost Monitoring

Track and control your AI provider spending.

### Viewing AI Costs

Monitor costs across all providers:

1. Navigate to **Settings** > **AI Providers** > **Cost Dashboard**
2. View:
   - **Today's Cost**: Current day spending
   - **Month-to-Date**: Cumulative monthly cost
   - **Per-Provider Breakdown**: Cost by OpenAI, xAI, Claude, Gemini
   - **Per-Camera Breakdown**: Which cameras use the most AI
   - **Cost Trend**: Graph of daily spending

**Cost Factors:**
- **Analysis Mode**: Video native costs more than single frame
- **Provider**: Pricing varies by provider
- **Event Volume**: More events = higher costs
- **Image Size**: Larger thumbnails use more tokens

### Setting Cost Limits

Prevent unexpected bills with spending caps:

**Daily Limit:**
1. Navigate to **Settings** > **AI Providers** > **Cost Limits**
2. Enable **Daily Limit**
3. Set maximum daily spend (e.g., $1.00)
4. Choose action when limit reached:
   - **Pause AI**: Stop analysis until tomorrow
   - **Fallback Only**: Use free tier providers only
   - **Alert Only**: Notify but continue

**Monthly Limit:**
1. Enable **Monthly Limit**
2. Set maximum monthly spend (e.g., $20.00)
3. Choose action when limit reached

**Cost Alerts:**
- Get notified at 50%, 75%, and 90% of your limits
- Receive daily cost summaries via push notification

**Typical Costs:**
| Analysis Mode | Approx. Cost per Event |
|---------------|------------------------|
| Single Frame | $0.001 - $0.002 |
| Multi-Frame (5 frames) | $0.003 - $0.005 |
| Video Native | $0.01 - $0.03 |

---

## Settings Reference

| Setting | Location | Description |
|---------|----------|-------------|
| AI Providers | Settings > AI Providers | Configure API keys and fallback order |
| Provider Order | Settings > AI Providers | Drag to reorder fallback chain |
| Cost Limits | Settings > AI Providers > Cost Limits | Daily/monthly spending caps |
| Cost Dashboard | Settings > AI Providers > Cost Dashboard | View spending breakdown |
| Data Retention | Settings > Storage | How long to keep events (7-365 days) |
| Motion Sensitivity | Cameras > [Camera] | Adjust detection threshold |
| Analysis Mode | Cameras > [Camera] | Single frame, multi-frame, or video |
| Push Notifications | Settings > Notifications | Enable/disable push |
| Quiet Hours | Settings > Notifications | Suppress notifications during set times |
| MQTT Broker | Settings > Integrations > MQTT | Home Assistant connection |
| HomeKit | Settings > Integrations > HomeKit | Apple Home pairing |
| Face Recognition | Settings > Privacy | Enable/disable face embeddings |
| Vehicle Recognition | Settings > Privacy | Enable/disable vehicle embeddings |
| VIP Entities | Entities > [Entity] | Mark entities for priority alerts |
| Blocked Entities | Entities > [Entity] | Suppress notifications for entity |
| Anomaly Detection | Settings > Anomaly Detection | View baseline and configure alerts |
| Anomaly Threshold | Rules > [Rule] | Set anomaly score threshold for alerts |
| Entity Matching | Rules > [Rule] | Match alerts to specific named entities |

---

## Troubleshooting

### Common Issues

**No events appearing:**
1. Verify camera is enabled for AI analysis
2. Check AI provider is configured with valid key
3. Review event type filters on the camera

**AI descriptions missing:**
1. Test your AI provider in Settings > AI Providers
2. Check API key hasn't exceeded quota
3. Ensure events have thumbnails

**Push notifications not working:**
1. Check browser notification permissions
2. Verify HTTPS is enabled (required for push)
3. Try re-subscribing in Settings > Notifications

**UniFi Protect connection failed:**
See the [UniFi Protect Troubleshooting Guide](troubleshooting-protect.md) for detailed solutions.

### Getting Help

1. Check the [Troubleshooting Guide](troubleshooting-protect.md)
2. Review backend logs for errors
3. Open an issue on GitHub with:
   - Steps to reproduce
   - Error messages
   - System configuration

---

## Quick Reference

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `?` | Show shortcuts help |
| `d` | Go to Dashboard |
| `e` | Go to Events |
| `c` | Go to Cameras |
| `s` | Go to Settings |
| `/` | Focus search |
| `Esc` | Close dialogs |

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/events` | List events |
| `GET /api/v1/cameras` | List cameras |
| `POST /api/v1/voice/query` | Voice query |
| `GET /api/v1/summaries/daily` | Get daily digest |
| `GET /docs` | API documentation |

---

*Last updated: December 2025*
