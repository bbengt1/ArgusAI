---
sidebar_position: 1
---

# How to Use ArgusAI

This guide walks you through using ArgusAI to monitor your home security cameras with AI-powered event detection.

## Overview

ArgusAI provides a web-based interface to:

- **Monitor cameras** in real-time with live previews
- **View events** with AI-generated descriptions
- **Track entities** (people, vehicles) across multiple events
- **Receive notifications** when specific events occur
- **Review daily summaries** of activity

## Getting Around

### Navigation

The main navigation menu provides access to all features:

| Page | Description |
|------|-------------|
| **Dashboard** | System overview, stats, and quick access |
| **Events** | Timeline of all detected events |
| **Entities** | Recognized people and vehicles |
| **Cameras** | Camera management and live preview |
| **Summaries** | AI-generated activity digests |
| **Alert Rules** | Notification configuration |
| **Settings** | System configuration |

### Quick Actions

From any page, you can:

- Use the **search** function to find specific events
- Check **system status** in the header
- Access **notifications** from the bell icon
- Switch between **light/dark mode** in settings

## First Steps

After installation, follow these steps to get started:

### 1. Configure AI Providers

ArgusAI needs at least one AI provider to generate event descriptions.

1. Navigate to **Settings > AI Models**
2. Enter your API key for at least one provider
3. Click **Test** to verify the connection
4. Drag providers to set priority order

### 2. Add Cameras

Choose your camera integration method:

**UniFi Protect (Recommended for Ubiquiti users)**
1. Go to **Settings > Protect Controllers**
2. Add your controller credentials
3. Enable desired cameras for AI analysis

**RTSP Cameras**
1. Go to **Cameras**
2. Click **Add Camera**
3. Enter the RTSP stream URL

**USB Webcams**
1. Go to **Cameras**
2. Click **Add Camera**
3. Select USB as source type

### 3. Enable Notifications (Optional)

1. Go to **Settings > Notifications**
2. Click **Enable Push Notifications**
3. Grant browser permission when prompted
4. Create alert rules to filter notifications

### 4. Start Monitoring

Once cameras are configured:

- Events appear on the **Events** page
- Live previews show on the **Dashboard**
- AI descriptions are generated automatically

## Understanding Events

Events are the core of ArgusAI. Each event represents a detected activity:

### Event Information

- **Thumbnail**: Snapshot from the camera
- **Description**: AI-generated text describing what happened
- **Detection Type**: person, vehicle, package, animal, or ring
- **Confidence Score**: How certain the AI is (0-100%)
- **Timestamp**: When the event occurred
- **Camera**: Which camera captured it

### Event Actions

Click on any event to:

- View full-size images
- See additional frames (multi-frame analysis)
- Re-analyze with updated AI settings
- Link to or unlink from entities
- Provide feedback on description accuracy

## Getting Help

- **Troubleshooting**: See the [Troubleshooting](/docs/troubleshooting) guide
- **Configuration**: Check [Configuration](/docs/getting-started/configuration) options
- **Features**: Learn about [AI Analysis](/docs/features/ai-analysis) and more

## Next Steps

Explore the detailed guides for each section:

- [Dashboard](/docs/how-to-use/dashboard) - System overview and monitoring
- [Events](/docs/how-to-use/events) - Browsing and managing events
- [Cameras](/docs/how-to-use/cameras) - Camera setup and management
- [Entities](/docs/how-to-use/entities) - Tracking recognized subjects
- [Alert Rules](/docs/how-to-use/alert-rules) - Configuring notifications
- [Settings](/docs/how-to-use/settings) - System configuration
- [Summaries](/docs/how-to-use/summaries) - Activity reports
