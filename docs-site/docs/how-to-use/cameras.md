---
sidebar_position: 4
---

# Cameras

The Cameras page lets you manage all your video sources, from UniFi Protect cameras to RTSP streams and USB webcams.

## Camera Overview

### Camera List

The main view shows all configured cameras:

| Column | Description |
|--------|-------------|
| **Preview** | Live thumbnail (when available) |
| **Name** | Camera friendly name |
| **Type** | Source type (Protect/RTSP/USB) |
| **Status** | Online, offline, or error state |
| **Events** | Count of recent events |
| **Actions** | Quick action buttons |

### Status Indicators

| Status | Meaning |
|--------|---------|
| **Online** | Camera is connected and streaming |
| **Offline** | Camera is not responding |
| **Error** | Connection or configuration issue |
| **Disabled** | Camera is intentionally turned off |
| **Processing** | Currently capturing or analyzing |

## Adding Cameras

### UniFi Protect Cameras

Protect cameras are discovered automatically from your controller:

1. Go to **Settings > Protect Controllers**
2. Add your controller (see [UniFi Protect Integration](/docs/features/unifi-protect))
3. Return to **Cameras** page
4. Protect cameras appear with "Protect" badge
5. Toggle individual cameras on/off for AI analysis

### RTSP Cameras

For generic IP cameras with RTSP streams:

1. Go to **Cameras**
2. Click **Add Camera**
3. Select **RTSP** as source type
4. Fill in the details:

| Field | Example | Required |
|-------|---------|----------|
| **Name** | Front Porch | Yes |
| **RTSP URL** | rtsp://192.168.1.100:554/stream1 | Yes |
| **Username** | admin | If required |
| **Password** | ****** | If required |

4. Click **Test Connection**
5. If successful, click **Save**

#### Finding Your RTSP URL

Common RTSP URL patterns:

| Brand | URL Pattern |
|-------|-------------|
| Hikvision | `rtsp://user:pass@IP:554/Streaming/Channels/101` |
| Dahua | `rtsp://user:pass@IP:554/cam/realmonitor?channel=1&subtype=0` |
| Reolink | `rtsp://user:pass@IP:554/h264Preview_01_main` |
| Amcrest | `rtsp://user:pass@IP:554/cam/realmonitor?channel=1&subtype=0` |
| Generic | `rtsp://user:pass@IP:554/stream` |

Check your camera's documentation for the exact URL format.

### USB Webcams

For directly connected webcams:

1. Click **Add Camera**
2. Select **USB** as source type
3. Choose the device from the dropdown
4. Enter a friendly name
5. Click **Save**

:::note
USB cameras require the backend to run on the same machine as the camera is connected to.
:::

## Camera Configuration

### Editing Camera Settings

1. Click on a camera name or the **Edit** button
2. Modify settings as needed
3. Click **Save**

### Common Settings

| Setting | Description |
|---------|-------------|
| **Name** | Friendly display name |
| **Enabled** | Whether to process events from this camera |
| **Motion Sensitivity** | Threshold for motion detection (RTSP/USB) |
| **Frame Rate** | Capture rate for motion detection |

### Protect-Specific Settings

For UniFi Protect cameras:

| Setting | Description |
|---------|-------------|
| **Event Filters** | Which detection types to process |
| **Smart Detection** | Person, Vehicle, Package, Animal, Ring |
| **Zone Filters** | Limit to specific motion zones |

## Camera Actions

### Test Connection

Verify camera connectivity:

1. Click the **Test** button
2. Wait for the connection test
3. Success shows green checkmark
4. Failure shows error message with details

### View Live

Open a live preview window:

1. Click the **Live** button
2. Full-screen preview opens
3. Stream updates in real-time
4. Click anywhere to close

### View Events

See all events from a specific camera:

1. Click the **Events** button
2. Navigates to Events page with camera filter applied
3. Shows only events from selected camera

### Start/Stop Capture

Control motion detection (RTSP/USB only):

1. Click **Start** to begin motion detection
2. Click **Stop** to pause detection
3. Status updates immediately
4. Events stop/resume accordingly

### Delete Camera

Remove a camera from the system:

1. Click the **Delete** button
2. Confirm in the dialog
3. Camera and its settings are removed
4. Past events remain in the database

:::caution
Protect cameras cannot be deleted individually. They are managed through the controller.
:::

## Troubleshooting

### Camera Won't Connect

**RTSP cameras:**
- Verify the URL is correct
- Check username/password
- Ensure camera is on the same network
- Test URL in VLC media player
- Check firewall rules

**USB cameras:**
- Verify the device is connected
- Check device permissions
- Restart the backend service
- Try a different USB port

### No Events Appearing

- Check camera is **Enabled**
- Verify motion sensitivity is appropriate
- For Protect: ensure event filters include desired types
- Check camera is actually detecting motion
- Review backend logs for errors

### Poor Video Quality

- Use main stream instead of substream in RTSP URL
- Check network bandwidth
- Reduce number of concurrent cameras
- Adjust bitrate on the camera itself

### High CPU Usage

- Lower frame rate for motion detection
- Use hardware-accelerated codecs if available
- Reduce number of active cameras
- Consider substream for detection, main stream for events

## Best Practices

### Camera Naming

Use clear, location-based names:
- Good: "Front Door", "Driveway", "Backyard"
- Avoid: "Camera 1", "IP Camera", "Test"

### Multiple Cameras

When adding many cameras:
- Add and test one at a time
- Use consistent naming convention
- Group related cameras logically
- Consider network bandwidth limits

### Protect vs RTSP

If you have UniFi Protect:
- Use Protect integration for those cameras
- Only use RTSP for non-Protect cameras
- Protect provides better event detection
- RTSP requires more local processing
