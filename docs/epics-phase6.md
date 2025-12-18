# Phase 6 Epics: Polish, Performance & Future Capabilities

**PRD Reference:** docs/backlog.md (remaining open items)
**Architecture Reference:** docs/architecture/ (Phase 6 Additions)
**Date:** 2025-12-16
**Status:** ✅ COMPLETE (2025-12-17)

---

## Overview

Phase 6 consolidates remaining backlog items into focused epics addressing:
- Performance optimizations for scale
- Accessibility completion
- Camera setup UX improvements
- Future audio analysis capabilities
- Data export enhancements

### Phase 6 Summary

| Epic | Stories | Status |
|------|---------|--------|
| P6-1: Camera Setup & Performance | 4 | ✅ Complete |
| P6-2: Accessibility Completion | 2 | ✅ Complete |
| P6-3: Audio Analysis Foundation | 3 | ✅ Complete |
| P6-4: Data Export Enhancements | 2 | ✅ Complete |
| **Total** | **11** | **✅ Complete** |

---

## Epic P6-1: Camera Setup & Performance

**Priority:** Medium
**Goal:** Improve camera setup UX and optimize for larger deployments

### Story P6-1.1: Implement Pre-Save Connection Test Endpoint
**Description:** Create API endpoint to test RTSP/USB connection before saving camera to database
**FRs:** Test connection without persistence
**Backlog:** FF-011
**Acceptance Criteria:**
- POST `/api/v1/cameras/test` endpoint created (accepts camera config in body)
- Validates RTSP URL format and credentials
- Tests actual connection to camera
- Returns stream info (resolution, FPS, codec) on success
- Returns diagnostic error message on failure
- Returns preview thumbnail on success
- No database record created during test

### Story P6-1.2: Add React.memo to CameraPreview Component
**Description:** Optimize CameraPreview component with React.memo to prevent unnecessary re-renders
**FRs:** Performance optimization
**Backlog:** IMP-005 (partial)
**Acceptance Criteria:**
- CameraPreview wrapped with React.memo
- Custom comparison function for props
- Re-renders only when camera data or preview changes
- No visual regression

### Story P6-1.3: Implement Virtual Scrolling for Camera List
**Description:** Add virtualization to camera list for handling 20+ cameras efficiently
**FRs:** Performance optimization
**Backlog:** IMP-005 (partial)
**Acceptance Criteria:**
- @tanstack/react-virtual or similar library integrated
- Only visible camera cards rendered to DOM
- Smooth scrolling performance maintained
- Works with existing camera filtering

### Story P6-1.4: Add Camera Data Caching with React Query
**Description:** Implement stale-while-revalidate caching for camera list API calls
**FRs:** Performance optimization
**Backlog:** IMP-005 (partial)
**Acceptance Criteria:**
- TanStack Query (React Query) configured for camera endpoints
- Stale time set appropriately (e.g., 30 seconds)
- Background refetch on window focus
- Reduced API calls during navigation

---

## Epic P6-2: Accessibility Completion

**Priority:** Low
**Goal:** Complete remaining accessibility enhancements for WCAG compliance

### Story P6-2.1: Add Skip to Content Link
**Description:** Implement skip link for keyboard users to bypass navigation
**FRs:** WCAG 2.4.1 Bypass Blocks
**Backlog:** IMP-004 (remaining)
**Acceptance Criteria:**
- Skip link appears on Tab at page top
- Visually hidden until focused
- Links to main content area
- Works on all pages
- Styled to match design system when visible

### Story P6-2.2: Audit and Fix Remaining ARIA Issues
**Description:** Complete accessibility audit and fix any remaining ARIA label gaps
**FRs:** WCAG compliance
**Backlog:** IMP-004 (remaining)
**Acceptance Criteria:**
- axe-core or similar audit tool run
- All critical/serious issues resolved
- Dynamic content announcements work
- Form error messages accessible
- Color contrast meets WCAG AA

---

## Epic P6-3: Audio Analysis Foundation

**Priority:** Low
**Goal:** Lay groundwork for future audio-based event detection

### Story P6-3.1: Add Audio Stream Extraction from RTSP
**Description:** Extend RTSP capture to extract audio stream alongside video
**FRs:** Audio capture
**Backlog:** FF-015
**Acceptance Criteria:**
- Audio stream detected and extracted from RTSP
- Supports common codecs (AAC, G.711, Opus)
- Audio buffer maintained separate from video
- Can be enabled/disabled per camera
- No impact on video capture performance when disabled

### Story P6-3.2: Implement Audio Event Detection Pipeline
**Description:** Create service for detecting audio events (glass break, etc.)
**FRs:** Audio analysis
**Backlog:** FF-015
**Acceptance Criteria:**
- Audio classification model integration point
- Supported event types: glass break, gunshot, scream, doorbell
- Confidence threshold configurable
- Events created with audio_event_type field
- Can trigger alerts like visual events

### Story P6-3.3: Add Audio Settings to Camera Configuration
**Description:** UI for enabling audio capture and configuring audio event detection
**FRs:** Audio configuration
**Backlog:** FF-015
**Acceptance Criteria:**
- Toggle to enable/disable audio capture per camera
- Audio event type selection (which sounds to detect)
- Sensitivity/confidence threshold slider
- Audio indicator in camera status

---

## Epic P6-4: Data Export Enhancements

**Priority:** Low
**Goal:** Provide comprehensive data export for external analysis

### Story P6-4.1: Implement Motion Events CSV Export
**Description:** Add CSV export endpoint for raw motion event data
**FRs:** Data export
**Backlog:** FF-017
**Acceptance Criteria:**
- GET `/api/v1/motion-events/export?format=csv` endpoint created
- Columns: timestamp, camera_id, camera_name, confidence, algorithm, x, y, width, height, zone_id
- Date range filtering (start_date, end_date)
- Camera filtering (camera_id)
- Streaming response for large datasets
- Filename includes date range

### Story P6-4.2: Add Motion Events Export UI
**Description:** Create UI for downloading motion events export
**FRs:** Data export
**Backlog:** FF-017
**Acceptance Criteria:**
- Export button on Motion Events page (if exists) or Settings
- Date range picker for filtering
- Camera selector for filtering
- Download triggers file save
- Loading state during export generation

---

## Summary

| Epic | Stories | Priority | Key Deliverable |
|------|---------|----------|-----------------|
| P6-1 | 4 | Medium | Camera setup UX & performance |
| P6-2 | 2 | Low | Accessibility completion |
| P6-3 | 3 | Low | Audio analysis foundation |
| P6-4 | 2 | Low | Motion events export |

**Total:** 4 epics, 11 stories

---

## Dependencies

- **P6-1.1** (Pre-save test): No dependencies, standalone feature
- **P6-1.2-1.4** (Performance): Can be done independently
- **P6-2** (Accessibility): No dependencies
- **P6-3** (Audio): Requires ffmpeg with audio codec support
- **P6-4** (Export): Requires motion_events table with bounding box data

---

## Notes

- Phase 6 focuses on polish and future-proofing rather than core features
- Audio analysis (P6-3) is foundational - full AI audio classification deferred
- Performance optimizations (P6-1) only needed if camera count exceeds ~20
- All items carried forward from project backlog
