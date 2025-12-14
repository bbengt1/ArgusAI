# Epic Technical Specification: UX Polish & Accessibility

Date: 2025-12-14
Author: Brent
Epic ID: P5-5
Status: Draft

---

## Overview

Epic P5-5 improves ArgusAI's accessibility and user experience through ARIA label additions, keyboard navigation improvements, detection zone presets, multiple schedule time ranges, and README documentation updates. This epic addresses accumulated UX backlog items while ensuring the application meets WCAG 2.1 AA accessibility standards.

The implementation focuses on making ArgusAI usable by people with disabilities (screen reader users, keyboard-only users) while also adding convenience features requested by users (zone presets, flexible schedules).

**PRD Reference:** docs/PRD-phase5.md (FR31-FR36, NFR21-NFR23)
**Backlog Items:** IMP-004, FF-016, FF-018, TD-005

## Objectives and Scope

**In Scope:**
- ARIA labels on all interactive elements (buttons, inputs, icons)
- Keyboard navigation for core workflows (tab order, focus states)
- Focus trapping in modal dialogs
- Detection zone preset templates (Full Frame, Top Half, Bottom Half, Center, L-Shape)
- Multiple time ranges per day for detection schedules
- Database schema for schedule ranges and zone presets
- README update with frontend setup documentation

**Out of Scope:**
- Full WCAG audit and remediation (focus on core flows)
- Color contrast fixes (assumed already compliant with shadcn/ui)
- Internationalization/localization
- Mobile-specific accessibility (focus on desktop)

## System Architecture Alignment

**Architecture Reference:** docs/architecture/phase-5-additions.md

This epic aligns with:
- **Phase 5 Database Schema** - detection_schedule_ranges and zone_presets tables
- **Accessibility Patterns** - AccessibleButton component pattern
- **Zone Preset Application** - ZONE_PRESETS constant and applyPreset function

**Key Files:**
- Frontend components throughout (accessibility updates)
- `frontend/components/cameras/ZonePresets.tsx` - New component
- `backend/app/models/` - Schedule range and preset models
- `README.md` - Documentation updates

## Detailed Design

### Services and Modules

| Component | Responsibility | Location |
|-----------|----------------|----------|
| ZonePresets.tsx | Zone preset selection UI | frontend/components/cameras/ |
| ScheduleRangeEditor.tsx | Multiple time range UI | frontend/components/cameras/ |
| Accessibility updates | ARIA labels, focus management | Various components |
| README.md | Frontend setup docs | Root directory |

### Data Models and Contracts

**Detection Schedule Ranges (SQLAlchemy):**
```python
class DetectionScheduleRange(Base):
    __tablename__ = "detection_schedule_ranges"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id"))
    day_of_week: Mapped[int] = mapped_column()  # 0=Sunday, 6=Saturday
    start_time: Mapped[time] = mapped_column()
    end_time: Mapped[time] = mapped_column()
    enabled: Mapped[bool] = mapped_column(default=True)

    camera = relationship("Camera", back_populates="schedule_ranges")

    __table_args__ = (
        UniqueConstraint('camera_id', 'day_of_week', 'start_time'),
    )
```

**Zone Presets (SQLAlchemy):**
```python
class ZonePreset(Base):
    __tablename__ = "zone_presets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    points: Mapped[dict] = mapped_column(JSON)  # [[x,y], ...]
    is_system: Mapped[bool] = mapped_column(default=False)
```

**Zone Preset Constants (Frontend):**
```typescript
export const ZONE_PRESETS = {
  full_frame: {
    name: "Full Frame",
    description: "Entire camera view",
    points: [[0, 0], [1, 0], [1, 1], [0, 1]]
  },
  top_half: {
    name: "Top Half",
    description: "Upper portion of frame",
    points: [[0, 0], [1, 0], [1, 0.5], [0, 0.5]]
  },
  bottom_half: {
    name: "Bottom Half",
    description: "Lower portion of frame",
    points: [[0, 0.5], [1, 0.5], [1, 1], [0, 1]]
  },
  center: {
    name: "Center",
    description: "Center 50% of frame",
    points: [[0.25, 0.25], [0.75, 0.25], [0.75, 0.75], [0.25, 0.75]]
  },
  l_shape: {
    name: "L-Shape",
    description: "L-shaped zone covering bottom and left",
    points: [[0, 0], [0.5, 0], [0.5, 0.5], [1, 0.5], [1, 1], [0, 1]]
  }
} as const;
```

### APIs and Interfaces

**Schedule Ranges API (extension to existing camera endpoints):**

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | /api/v1/cameras/{id}/schedule-ranges | - | `ScheduleRange[]` |
| POST | /api/v1/cameras/{id}/schedule-ranges | ScheduleRange | ScheduleRange |
| DELETE | /api/v1/cameras/{id}/schedule-ranges/{range_id} | - | 204 |

**ScheduleRange Schema:**
```json
{
  "id": 1,
  "day_of_week": 1,
  "start_time": "08:00",
  "end_time": "18:00",
  "enabled": true
}
```

### Workflows and Sequencing

**Accessibility Audit Workflow:**
```
1. Identify all interactive elements:
   - Buttons (action buttons, icon buttons)
   - Form inputs (text, select, checkbox)
   - Links and navigation
   - Modal dialogs
   - Dropdowns and menus

2. For each element, verify:
   - Has aria-label or accessible text
   - Has visible focus indicator
   - Is reachable via Tab key
   - Responds to Enter/Space appropriately

3. For modal dialogs:
   - Focus trapped inside when open
   - Escape key closes dialog
   - Focus returns to trigger on close

4. Update components as needed
```

**Zone Preset Application Flow:**
```
1. User opens zone editor for camera
2. User clicks "Presets" dropdown
3. Preset options displayed (Full Frame, Top Half, etc.)
4. User selects preset
5. applyPreset() converts normalized coords to canvas coords
6. Zone polygon updated with preset points
7. User can further adjust or save
```

**Multiple Schedule Ranges Flow:**
```
1. User opens camera schedule settings
2. Existing ranges displayed per day
3. User clicks "Add Range" for a day
4. Time picker for start/end time
5. Range saved to database
6. Multiple ranges per day supported
7. Detection logic checks if current time falls in ANY enabled range
```

## Non-Functional Requirements

### Accessibility (NFR21-NFR23)

| Requirement | Target | Verification |
|-------------|--------|--------------|
| Contrast ratio | 4.5:1 minimum (AA) | shadcn/ui default compliant |
| Touch targets | 44x44px minimum | CSS verification |
| Focus visibility | 2px ring, high contrast | Visual verification |
| Screen reader | Labels announced | VoiceOver/NVDA testing |

### Performance

| Metric | Target |
|--------|--------|
| Zone preset application | <100ms |
| Schedule range CRUD | <200ms response |
| Focus navigation | Immediate (no delay) |

## Dependencies and Integrations

### Frontend Dependencies (existing)

| Package | Purpose |
|---------|---------|
| @radix-ui/* | Accessible UI primitives (via shadcn/ui) |
| tailwindcss | Focus ring utilities |

### Database Migration

New migration for:
- `detection_schedule_ranges` table
- `zone_presets` table with seed data for system presets

## Acceptance Criteria (Authoritative)

**Story P5-5.1: Add ARIA Labels to All Interactive Elements**
1. All buttons have aria-label attribute
2. Form inputs have associated <label> elements or aria-label
3. Icon-only buttons have descriptive aria-label
4. Icons without meaning have aria-hidden="true"
5. Dialog components have role="dialog" and aria-modal="true"
6. Alert messages have role="alert" or aria-live

**Story P5-5.2: Implement Keyboard Navigation for Core Workflows**
1. Tab order follows logical reading order
2. All interactive elements reachable via Tab key
3. Focus states visible with ring-2 or equivalent
4. Modal dialogs trap focus when open
5. Escape key closes modal dialogs
6. Enter/Space activates buttons
7. Arrow keys navigate within menus/dropdowns

**Story P5-5.3: Create Detection Zone Preset Templates**
1. ZonePresets component created
2. Five presets available: Full Frame, Top Half, Bottom Half, Center, L-Shape
3. Preset dropdown in zone editor UI
4. One-click applies preset to zone
5. Presets use normalized coordinates (0-1 range)
6. Custom zones still fully supported after applying preset

**Story P5-5.4: Implement Multiple Schedule Time Ranges**
1. Database table detection_schedule_ranges created
2. API endpoints support multiple ranges per day
3. UI allows adding multiple ranges per day
4. UI allows removing individual ranges
5. Detection logic evaluates all ranges for current day
6. Overlapping ranges handled (OR logic - active if in ANY range)

**Story P5-5.5: Update README with Frontend Setup Docs**
1. Prerequisites section includes Node.js version (20+)
2. Installation commands documented (npm install)
3. Development server command (npm run dev)
4. Environment variables documented (.env.local)
5. Common troubleshooting tips included
6. Link to main README from frontend README (or section in main)

## Traceability Mapping

| AC | Spec Section | Component | Test Idea |
|----|--------------|-----------|-----------|
| P5-5.1-1 | Accessibility | All buttons | aria-label audit |
| P5-5.1-2 | Accessibility | Form inputs | Label association test |
| P5-5.1-3 | Accessibility | Icon buttons | aria-label verification |
| P5-5.1-4 | Accessibility | Decorative icons | aria-hidden check |
| P5-5.1-5 | Accessibility | Dialogs | Role attribute check |
| P5-5.1-6 | Accessibility | Alerts | Live region check |
| P5-5.2-1 | Workflows | Tab navigation | Tab order test |
| P5-5.2-2 | Workflows | All elements | Reachability test |
| P5-5.2-3 | NFR | Focus states | Visual focus test |
| P5-5.2-4 | Workflows | Modal dialogs | Focus trap test |
| P5-5.2-5 | Workflows | Modal dialogs | Escape key test |
| P5-5.2-6 | Workflows | Buttons | Activation test |
| P5-5.2-7 | Workflows | Menus | Arrow key test |
| P5-5.3-1 | Data Models | ZonePresets.tsx | Component exists |
| P5-5.3-2 | Data Models | ZONE_PRESETS | Five presets defined |
| P5-5.3-3 | Workflows | Zone editor | Dropdown visible |
| P5-5.3-4 | Workflows | applyPreset | Click applies preset |
| P5-5.3-5 | Data Models | Coordinates | Normalized range test |
| P5-5.3-6 | Workflows | Zone editor | Custom edit after preset |
| P5-5.4-1 | Data Models | Migration | Table exists |
| P5-5.4-2 | APIs | Schedule endpoints | Multiple ranges API |
| P5-5.4-3 | Workflows | Schedule UI | Add range action |
| P5-5.4-4 | Workflows | Schedule UI | Remove range action |
| P5-5.4-5 | Integration | Detection logic | Multi-range evaluation |
| P5-5.4-6 | Integration | Detection logic | Overlap handling |
| P5-5.5-1 | Data Models | README.md | Prerequisites section |
| P5-5.5-2 | Data Models | README.md | Install command |
| P5-5.5-3 | Data Models | README.md | Dev server command |
| P5-5.5-4 | Data Models | README.md | Env vars documented |
| P5-5.5-5 | Data Models | README.md | Troubleshooting tips |
| P5-5.5-6 | Data Models | README.md | Link/section exists |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1: Scope creep** - Accessibility can expand infinitely; focus on core workflows
- **R2: Breaking changes** - Adding ARIA may affect existing test selectors
- **R3: Browser compatibility** - Some ARIA features vary by browser; test in Chrome + Safari

**Assumptions:**
- **A1:** shadcn/ui components already have good baseline accessibility
- **A2:** Focus rings visible against all background colors in current theme
- **A3:** Users want zone presets for common scenarios, not custom preset creation
- **A4:** Multiple time ranges per day covers scheduling needs (not per-minute granularity)

**Open Questions:**
- **Q1:** Should users be able to create custom named presets? → Defer, use system presets only
- **Q2:** Maximum number of schedule ranges per day? → No limit, practical max ~5
- **Q3:** Add CI workflow status badge to README? → Yes, add after CI epic complete

## Test Strategy Summary

**Automated Tests:**
- Component tests for ZonePresets (render, click handlers)
- Component tests for ScheduleRangeEditor
- API tests for schedule range CRUD
- Unit tests for detection schedule evaluation logic

**Manual Tests (Required):**
- Screen reader testing (VoiceOver on macOS, NVDA on Windows)
- Keyboard-only navigation through all core workflows
- Zone preset application verification
- Multiple schedule ranges with detection verification

**Accessibility Audit:**
- Use axe DevTools browser extension
- Lighthouse accessibility audit
- Manual WCAG 2.1 AA checklist review
