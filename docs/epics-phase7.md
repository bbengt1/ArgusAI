# Phase 7 Epics: HomeKit Integration & Enhancements

**PRD Reference:** docs/backlog.md
**Architecture Reference:** docs/architecture/ (Phase 7 Additions)
**Date:** 2025-12-17
**Status:** In Progress

---

## Overview

Phase 7 focuses on perfecting the HomeKit integration, adding package delivery alerts, camera previews in HomeKit, and laying groundwork for entity-based alerts.

**Goals:**
- Troubleshoot and fix HomeKit connectivity issues
- Add package delivery carrier detection (FedEx, UPS, USPS, Amazon, DHL)
- Enable camera live preview/streaming in HomeKit
- Stub out entities page with alert configuration

---

## Epic P7-1: HomeKit Troubleshooting & Fixes

**Priority:** High
**Goal:** Diagnose and fix issues preventing HomeKit from working correctly in Apple Home app

### Story P7-1.1: Add HomeKit Diagnostic Logging
**Description:** Add comprehensive logging to diagnose HomeKit connection, pairing, and event delivery issues
**FRs:** Troubleshooting support
**Acceptance Criteria:**
- Add debug logging for HAP server lifecycle (start, stop, errors)
- Log all pairing attempts with success/failure status
- Log accessory characteristic updates (motion triggered, reset)
- Log network binding (IP, port) information
- Add `/api/v1/homekit/diagnostics` endpoint returning recent logs
- Display diagnostic info in Settings UI

### Story P7-1.2: Fix HomeKit Bridge Discovery Issues
**Description:** Investigate and fix mDNS/Bonjour advertisement issues preventing Home app from discovering ArgusAI bridge
**FRs:** HomeKit discovery
**Acceptance Criteria:**
- Verify HAP-python mDNS advertisement is working
- Test with avahi-browse/dns-sd to confirm service visibility
- Add network interface binding configuration
- Support binding to specific IP address (not just 0.0.0.0)
- Document firewall requirements (UDP 5353 for mDNS)
- Add connectivity test button in UI

### Story P7-1.3: Fix HomeKit Event Delivery
**Description:** Ensure motion events are reliably delivered to paired HomeKit devices
**FRs:** Event reliability
**Acceptance Criteria:**
- Verify characteristic updates are propagated to clients
- Add event delivery confirmation logging
- Test with multiple paired devices
- Ensure auto-reset timers work correctly
- Add manual test button to trigger motion in UI

### Story P7-1.4: Add HomeKit Connection Status Monitoring
**Description:** Display real-time HomeKit connection health in the UI
**FRs:** Status monitoring
**Acceptance Criteria:**
- Show mDNS advertisement status (advertising/not advertising)
- Show connected clients count
- Show last event delivery timestamp per sensor
- Show any errors or warnings
- Auto-refresh status every 5 seconds when panel open

---

## Epic P7-2: Package Delivery Alerts

**Priority:** Medium
**Goal:** Detect and alert when packages are delivered by major carriers

### Story P7-2.1: Add Carrier Detection to AI Analysis
**Description:** Extend AI description prompt to identify delivery carriers from uniforms/trucks
**FRs:** Carrier identification
**Acceptance Criteria:**
- Update AI prompt to identify: FedEx, UPS, USPS, Amazon, DHL
- Add `delivery_carrier` field to event schema
- Extract carrier from AI description using pattern matching
- Store carrier in event record when detected
- Return carrier in event API responses

### Story P7-2.2: Create Package Delivery Alert Rule Type
**Description:** Add new alert rule type for package delivery notifications
**FRs:** Delivery alerts
**Acceptance Criteria:**
- Add "Package Delivery" to alert rule types
- Support filtering by carrier (any, specific carrier, multiple carriers)
- Trigger when package detected AND carrier identified
- Include carrier name in alert message
- Support all notification channels (push, webhook, MQTT)

### Story P7-2.3: Add Package Delivery to HomeKit
**Description:** Trigger HomeKit package sensor when delivery is detected with carrier info
**FRs:** HomeKit package alerts
**Acceptance Criteria:**
- Trigger existing package sensor on delivery detection
- Add carrier info to HomeKit accessory name/metadata if possible
- Create separate sensors per carrier (optional config)
- Log carrier detection for debugging

### Story P7-2.4: Create Package Delivery Dashboard Widget
**Description:** Add widget showing recent package deliveries
**FRs:** Delivery tracking UI
**Acceptance Criteria:**
- Show last 5 package deliveries on dashboard
- Display: timestamp, camera, carrier, thumbnail
- Link to full event detail
- Filter events page by "Package Delivery"

---

## Epic P7-3: HomeKit Camera Streaming

**Priority:** Medium
**Goal:** Enable live camera preview/streaming directly in Apple Home app

### Story P7-3.1: Verify RTSP-to-SRTP Streaming Works
**Description:** Test and fix the existing camera streaming implementation
**FRs:** Camera streaming
**Acceptance Criteria:**
- Test camera preview in Home app
- Verify ffmpeg transcoding pipeline
- Fix any codec/resolution compatibility issues
- Support multiple concurrent streams (up to 2)
- Add stream quality configuration (low/medium/high)

### Story P7-3.2: Add Camera Snapshot Support
**Description:** Implement snapshot capture for HomeKit camera tiles
**FRs:** Camera snapshots
**Acceptance Criteria:**
- Implement get_snapshot() method in camera accessory
- Return JPEG snapshot from camera
- Cache snapshot for 5 seconds to reduce load
- Handle camera offline gracefully (return placeholder)

### Story P7-3.3: Add Camera Streaming Diagnostics
**Description:** Add monitoring and troubleshooting for camera streaming
**FRs:** Stream diagnostics
**Acceptance Criteria:**
- Log stream start/stop events
- Show active streams in HomeKit status panel
- Display ffmpeg command being used (for debugging)
- Add stream test button in camera settings

---

## Epic P7-4: Entities Page & Alert Stub

**Priority:** Low
**Goal:** Create foundation for entity-based alerting (known people, vehicles, etc.)

### Story P7-4.1: Design Entities Data Model
**Description:** Define schema for tracking recognized entities (people, vehicles)
**FRs:** Entity tracking
**Acceptance Criteria:**
- Create Entity model: id, type (person/vehicle), name, thumbnail, first_seen, last_seen, occurrence_count
- Create EntitySighting model: entity_id, event_id, confidence, timestamp
- Add migration for new tables
- Define API endpoints structure

### Story P7-4.2: Create Entities List Page
**Description:** Build UI to view and manage recognized entities
**FRs:** Entity management
**Acceptance Criteria:**
- Display grid of entity cards with thumbnail
- Show entity name (editable), type, last seen, occurrence count
- Support search/filter by name, type
- Placeholder for "Add Alert" button (not functional yet)
- Empty state when no entities exist

### Story P7-4.3: Stub Entity Alert Configuration UI
**Description:** Create non-functional UI for configuring entity-based alerts
**FRs:** Alert configuration preview
**Acceptance Criteria:**
- Add "Create Alert" modal to entity card
- Show options: notify when seen, notify when NOT seen for X hours
- Show time range configuration (all day, schedule)
- Display "Coming Soon" message when save attempted
- Link to alert rules page

---

## Dependencies

- **HAP-python**: Required for HomeKit (already installed)
- **ffmpeg**: Required for camera streaming (optional feature)
- **qrcode**: Required for QR code pairing (already installed)

---

## Technical Notes

### HomeKit Troubleshooting Checklist

1. **mDNS/Bonjour**
   - Port 5353 UDP must be open
   - avahi-daemon or mDNSResponder must be running
   - Test with: `avahi-browse -a` or `dns-sd -B _hap._tcp`

2. **HAP Server**
   - Port 51826 (default) must be accessible
   - Check binding address (0.0.0.0 vs specific IP)
   - Verify accessory.state file permissions

3. **Pairing**
   - Reset pairing if stuck in bad state
   - Ensure setup code is valid (XXX-XX-XXX format)
   - Check iOS Home app logs via Console app

4. **Event Delivery**
   - Characteristic changes must propagate to clients
   - HAP-python uses asyncio - ensure event loop is running
   - Check for race conditions in timer management

### Package Carrier Detection

AI prompt enhancement:
```
If you see a delivery person or truck, identify the carrier:
- FedEx (purple/orange colors, FedEx logo)
- UPS (brown uniform, brown truck)
- USPS (blue uniform, postal logo, mail truck)
- Amazon (blue vest, Amazon logo, Amazon van)
- DHL (yellow/red colors, DHL logo)
Include the carrier name in your description.
```

### Entities Data Model

```python
class Entity(Base):
    id = Column(UUID, primary_key=True)
    type = Column(String)  # 'person', 'vehicle'
    name = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    embedding = Column(LargeBinary, nullable=True)  # For future face/vehicle recognition
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    occurrence_count = Column(Integer, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

---

## GitHub Issues to Create

| Story | Title | Labels |
|-------|-------|--------|
| P7-1.1 | Add HomeKit Diagnostic Logging | homekit, troubleshooting |
| P7-1.2 | Fix HomeKit Bridge Discovery Issues | homekit, bug |
| P7-1.3 | Fix HomeKit Event Delivery | homekit, bug |
| P7-1.4 | Add HomeKit Connection Status Monitoring | homekit, frontend |
| P7-2.1 | Add Carrier Detection to AI Analysis | ai, feature |
| P7-2.2 | Create Package Delivery Alert Rule Type | alerts, feature |
| P7-2.3 | Add Package Delivery to HomeKit | homekit, feature |
| P7-2.4 | Create Package Delivery Dashboard Widget | frontend, feature |
| P7-3.1 | Verify RTSP-to-SRTP Streaming Works | homekit, camera |
| P7-3.2 | Add Camera Snapshot Support | homekit, camera |
| P7-3.3 | Add Camera Streaming Diagnostics | homekit, troubleshooting |
| P7-4.1 | Design Entities Data Model | entities, backend |
| P7-4.2 | Create Entities List Page | entities, frontend |
| P7-4.3 | Stub Entity Alert Configuration UI | entities, frontend |

---

## Success Criteria

Phase 7 is complete when:
1. HomeKit integration works reliably (discovery, pairing, event delivery)
2. Package deliveries are detected with carrier identification
3. Camera streaming works in Apple Home app
4. Entities page exists with stub alert configuration
