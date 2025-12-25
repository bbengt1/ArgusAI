---
sidebar_position: 2
---

# Dashboard

The Dashboard is your home base for monitoring your security system. It provides an at-a-glance view of system status, recent activity, and camera feeds.

## Dashboard Components

### Statistics Overview

The top of the dashboard displays key metrics:

| Stat | Description |
|------|-------------|
| **Total Events** | Number of events detected today |
| **Active Cameras** | Cameras currently online and recording |
| **Entities Tracked** | Recognized people and vehicles |
| **AI Usage** | API calls made today |

### Activity Summary

The **Activity Summary** card shows an AI-generated overview of recent activity:

- Natural language summary of the day's events
- Highlights notable patterns or unusual activity
- Updates periodically throughout the day

Click **View Full Summary** to see detailed daily reports.

### Package Deliveries

The **Package Deliveries** widget tracks:

- Recent package detections
- Delivery timestamps
- Associated camera and snapshot

This helps you quickly check if packages have arrived.

### Camera Grid

The **Live Cameras** section shows:

- Preview thumbnails from active cameras
- Camera name and status
- Last event timestamp
- Quick action buttons

#### Camera Status Indicators

| Color | Status |
|-------|--------|
| Green | Online and active |
| Yellow | Online but idle |
| Red | Offline or error |
| Gray | Disabled |

### Recent Activity

The **Recent Activity** section displays the latest events:

- Shows the 10 most recent events
- Includes thumbnail, description, and timestamp
- Click any event to view details
- Click **View All Events** for the full timeline

## Using the Dashboard

### Refreshing Data

Dashboard data updates automatically, but you can:

- Click the **Refresh** button for immediate update
- Pull down on mobile to refresh
- Data auto-refreshes every 30 seconds

### Camera Quick Actions

Hover over any camera card to access:

- **View Live**: Open full-size live preview
- **View Events**: See events from this camera
- **Settings**: Quick access to camera settings

### Real-Time Updates

The dashboard receives real-time updates via WebSocket:

- New events appear instantly
- Camera status changes immediately
- No page refresh required

### Mobile Experience

On mobile devices, the dashboard adapts:

- Cards stack vertically
- Camera grid becomes scrollable
- Tap cameras to expand
- Swipe between sections

## Customization

### Dashboard Preferences

Access **Settings > Dashboard** to customize:

- Number of cameras shown
- Events displayed in recent activity
- Auto-refresh interval
- Default time range for stats

### Widget Visibility

Show or hide dashboard widgets:

1. Click the **gear icon** on any widget
2. Toggle visibility options
3. Changes save automatically

## Tips

### Quick Navigation

- Click any stat card to drill down to details
- Camera names link to their event history
- Entity counts link to the Entities page

### Monitoring Best Practices

- Keep the dashboard open on a dedicated display
- Use dark mode for nighttime monitoring
- Enable sound alerts for important events
- Check the summary at end of day

### Performance

If the dashboard feels slow:

- Reduce number of camera previews
- Lower preview refresh rate
- Disable auto-refresh when not actively monitoring
