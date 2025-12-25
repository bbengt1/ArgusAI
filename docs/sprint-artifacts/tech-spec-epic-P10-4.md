# Epic Technical Specification: Entity Management UX

Date: 2025-12-25
Author: Brent
Epic ID: P10-4
Status: Draft

---

## Overview

Epic P10-4 enhances the entity management user experience by reducing friction in key workflows. Currently, users must navigate through multiple screens to assign entities to events, cannot create entities proactively, and cannot modify feedback once submitted. This epic adds direct entity assignment from event cards, manual entity creation for pre-registering known people and vehicles, and the ability to edit or remove previously submitted feedback.

Building on the entity system established in Phase 4 and enhanced in Phase 9 (P9-4), this epic focuses purely on UX improvements rather than entity extraction or matching logic. The goal is to reduce clicks, increase user control, and provide a more intuitive entity management experience.

## Objectives and Scope

**In Scope:**
- Add entity assignment action directly from event cards (FR33-FR35)
- Create EntitySelectModal for quick entity search and selection
- Implement manual entity creation with form (FR36-FR39)
- Support vehicle-specific fields (color, make, model) in creation form
- Allow optional reference image upload for manual entities
- Enable feedback modification after initial submission (FR40-FR42)
- Show "edited" indicator when feedback has been changed (FR43)

**Out of Scope:**
- Entity extraction logic improvements (completed in P9-4)
- Entity merge functionality (completed in P9-4)
- Event-entity unlinking UI changes (completed in P9-4)
- Face/embedding-based entity matching
- Bulk entity operations
- Entity deletion (handled by retention policy)

## System Architecture Alignment

This epic extends the existing entity management components from Phase 4 and Phase 9:

| Component | Files Affected | Changes |
|-----------|---------------|---------|
| EventCard | `frontend/components/events/EventCard.tsx` | Add entity action button |
| EntitySelectModal | `frontend/components/entities/EntitySelectModal.tsx` | NEW: Quick entity picker |
| Entities Page | `frontend/app/entities/page.tsx` | Add "Create Entity" button |
| EntityCreateModal | `frontend/components/entities/EntityCreateModal.tsx` | NEW: Entity creation form |
| Entity API | `backend/app/api/v1/entities.py` | Add create endpoint |
| FeedbackButtons | `frontend/components/feedback/FeedbackButtons.tsx` | Add edit/remove support |
| Feedback API | `backend/app/api/v1/feedback.py` | Add PUT/DELETE endpoints |
| Feedback Model | `backend/app/models/event_feedback.py` | Add updated_at field |

### Entity Management UX Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Entity Management UX                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Event Cards                      Entities Page                  │
│  ┌──────────────────┐            ┌──────────────────┐           │
│  │ EventCard        │            │ EntitiesPage     │           │
│  │  └─ EntityAction │            │  └─ CreateButton │           │
│  │      └─ Modal    │            │      └─ Modal    │           │
│  └────────┬─────────┘            └────────┬─────────┘           │
│           │                               │                      │
│           ▼                               ▼                      │
│  ┌──────────────────────────────────────────────────┐           │
│  │              EntitySelectModal                     │           │
│  │  - Search existing entities                        │           │
│  │  - Select to assign                                │           │
│  │  - Create new inline                               │           │
│  └────────────────────────────────────────────────────┘           │
│                          │                                        │
│                          ▼                                        │
│  ┌──────────────────────────────────────────────────┐           │
│  │              Entity APIs                           │           │
│  │  POST /api/v1/context/entities     (create)       │           │
│  │  POST /api/v1/events/{id}/entity   (assign)       │           │
│  │  PUT /api/v1/events/{id}/feedback  (update)       │           │
│  │  DELETE /api/v1/events/{id}/feedback (remove)     │           │
│  └────────────────────────────────────────────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs |
|---------------|----------------|--------|---------|
| EntitySelectModal | Display searchable entity list for quick selection | Search query, event context | Selected entity or new creation |
| EntityCreateModal | Form for manual entity creation | Entity type, name, metadata | Created entity |
| EntityActionButton | Trigger entity assignment from event cards | Event data | Modal open action |
| FeedbackManager | Handle feedback edit/remove operations | Feedback ID, new rating/correction | Updated or removed feedback |

### Data Models and Contracts

**Enhanced EventFeedback Model:**
```python
class EventFeedback(Base):
    __tablename__ = "event_feedback"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID, ForeignKey("events.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    rating = Column(String, nullable=False)  # 'helpful', 'not_helpful'
    correction = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # ADDED

    @property
    def was_edited(self) -> bool:
        """Check if feedback was modified after creation."""
        if not self.updated_at:
            return False
        return self.updated_at > self.created_at + timedelta(seconds=1)
```

**Entity Creation Request Schema:**
```python
class EntityCreateRequest(BaseModel):
    type: Literal["person", "vehicle", "animal"]
    name: str | None = None
    description: str | None = None
    # Vehicle-specific (optional)
    vehicle_color: str | None = None
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    # Reference image (base64 encoded)
    reference_image: str | None = None
```

**Feedback Update Request Schema:**
```python
class FeedbackUpdateRequest(BaseModel):
    rating: Literal["helpful", "not_helpful"] | None = None
    correction: str | None = None
```

### APIs and Interfaces

**Entity Management Endpoints (New/Modified):**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/context/entities` | Create a new entity manually |
| GET | `/api/v1/context/entities` | List entities (existing, add search) |
| POST | `/api/v1/events/{id}/entity` | Assign entity to event (existing P9-4) |

**Create Entity Request:**
```json
POST /api/v1/context/entities
{
  "type": "vehicle",
  "name": "Dad's Truck",
  "vehicle_color": "white",
  "vehicle_make": "ford",
  "vehicle_model": "f150",
  "description": "Father's work truck"
}
```

**Create Entity Response:**
```json
{
  "id": "uuid",
  "type": "vehicle",
  "name": "Dad's Truck",
  "display_name": "Dad's Truck",
  "vehicle_color": "white",
  "vehicle_make": "ford",
  "vehicle_model": "f150",
  "vehicle_signature": "white-ford-f150",
  "event_count": 0,
  "created_at": "2025-12-25T12:00:00Z"
}
```

**Entity Search Request:**
```
GET /api/v1/context/entities?search=toyota&type=vehicle&limit=10
```

**Entity Search Response:**
```json
{
  "entities": [
    {
      "id": "uuid",
      "type": "vehicle",
      "display_name": "White Toyota Camry",
      "vehicle_signature": "white-toyota-camry",
      "event_count": 15,
      "thumbnail_url": "/api/v1/events/{latest_event_id}/thumbnail"
    }
  ],
  "total": 3
}
```

**Feedback Update/Delete Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| PUT | `/api/v1/events/{id}/feedback` | Update existing feedback |
| DELETE | `/api/v1/events/{id}/feedback` | Remove feedback |

**Update Feedback Request:**
```json
PUT /api/v1/events/{event_id}/feedback
{
  "rating": "not_helpful",
  "correction": "This is actually a FedEx driver, not UPS"
}
```

**Update Feedback Response:**
```json
{
  "id": "uuid",
  "event_id": "uuid",
  "rating": "not_helpful",
  "correction": "This is actually a FedEx driver, not UPS",
  "created_at": "2025-12-25T10:00:00Z",
  "updated_at": "2025-12-25T12:30:00Z",
  "was_edited": true
}
```

### Workflows and Sequencing

**Entity Assignment from Event Card Flow:**

```
1. User views event card in timeline or grid
2. User clicks "Entity" action button (icon: user-plus or tag)
3. EntitySelectModal opens with:
   - Search input at top
   - List of recent/relevant entities
   - "Create New Entity" button at bottom
4. User searches by typing (filters existing entities)
5. User clicks entity to select
6. Confirmation: "Assign [Event] to [Entity Name]?"
7. On confirm:
   a. POST /api/v1/events/{id}/entity { entity_id: "uuid" }
   b. Entity link created
   c. Event card updates to show entity badge
   d. Toast: "Event assigned to [Entity Name]"
8. Modal closes
```

**Manual Entity Creation Flow:**

```
1. User navigates to Entities page
2. User clicks "Create Entity" button
3. EntityCreateModal opens with form:
   - Type selector: Person | Vehicle | Animal
   - Name input (optional)
   - Description textarea (optional)
   - If Vehicle selected:
     - Color dropdown
     - Make input (with autocomplete)
     - Model input (with autocomplete)
   - Reference image upload (optional)
4. User fills form and clicks "Create"
5. Validation:
   - For vehicles: require at least color + make OR make + model
   - Name optional but recommended
6. On submit:
   a. POST /api/v1/context/entities
   b. Generate vehicle_signature if vehicle
   c. Process reference image if provided
   d. Return created entity
7. Success toast: "Entity created successfully"
8. Modal closes, entity list refreshes
9. New entity appears in list with 0 events
```

**Feedback Modification Flow:**

```
1. User views event with existing feedback (thumbs up/down shown)
2. User clicks the feedback button again
3. Popover or modal shows options:
   - "Change to [opposite]" - switch rating
   - "Edit correction" - modify text (if not_helpful)
   - "Remove feedback" - clear entirely
4. User selects action:

   If "Change":
   a. PUT /api/v1/events/{id}/feedback { rating: "helpful" }
   b. UI updates to show new rating
   c. "Edited" indicator appears

   If "Edit correction":
   a. Text input appears with current correction
   b. User modifies and saves
   c. PUT /api/v1/events/{id}/feedback { correction: "..." }

   If "Remove":
   a. Confirm dialog: "Remove your feedback?"
   b. DELETE /api/v1/events/{id}/feedback
   c. Buttons return to neutral state
   d. Toast: "Feedback removed"
```

---

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Entity search response | <200ms | API response time (searchable list) |
| Modal open animation | <100ms | Time to interactive |
| Entity creation | <300ms | API response time |
| Feedback update | <200ms | API response time |
| Image upload processing | <2s | For reference image up to 2MB |

### Security

- Entity creation requires authentication
- Feedback modification only allowed for own feedback
- Reference image upload limited to 2MB, validated mime types
- No secrets or sensitive data in entity metadata

### Reliability

- Entity creation should be atomic
- Feedback modification should not lose data on failure
- Modal should handle API errors gracefully
- Image upload should show progress and handle failures

### Observability

| Signal | Type | Purpose |
|--------|------|---------|
| entity.created | Counter | Track manual entity creation |
| entity.assigned_from_card | Counter | Track quick assignment usage |
| feedback.modified | Counter | Track feedback edits |
| feedback.removed | Counter | Track feedback removals |

---

## Dependencies and Integrations

### Backend Dependencies

No new dependencies required - using existing stack:

```
fastapi>=0.115.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
python-multipart>=0.0.5  # For file upload
```

### Frontend Dependencies

No new dependencies required - using existing shadcn/ui components:

```json
{
  "dependencies": {
    "@radix-ui/react-dialog": "existing",
    "@radix-ui/react-popover": "existing",
    "@radix-ui/react-dropdown-menu": "existing"
  }
}
```

### Internal Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Entity System | P4, P9-4 | Base entity model and APIs |
| Feedback System | P4 | Existing feedback model |
| EventCard Component | P4 | Existing event display |
| EntityList Component | P9-4 | Existing entity list |
| shadcn/ui | Current | Dialog, Form, Button components |

---

## Acceptance Criteria (Authoritative)

### P10-4.1: Add Entity Assignment from Event Cards

**AC-4.1.1:** Given I view an event card, when I look at the actions, then I see an "Entity" button (icon)
**AC-4.1.2:** Given I click the Entity button, when the modal opens, then I see a searchable list of existing entities
**AC-4.1.3:** Given the modal is open, when I type in the search box, then entities are filtered by name/type
**AC-4.1.4:** Given I select an entity, when I confirm, then the event is linked to that entity
**AC-4.1.5:** Given assignment succeeds, when I view the event card, then the entity badge/name is displayed
**AC-4.1.6:** Given the event already has an entity, when I click Entity button, then I see "Change Entity" option
**AC-4.1.7:** Given I'm in the modal, when I click "Create New", then I can create an entity inline

### P10-4.2: Implement Manual Entity Creation

**AC-4.2.1:** Given I'm on the Entities page, when I view the header, then I see a "Create Entity" button
**AC-4.2.2:** Given I click Create Entity, when the modal opens, then I see a form with type, name, description
**AC-4.2.3:** Given I select type "Vehicle", when I view the form, then color, make, model fields appear
**AC-4.2.4:** Given I fill the form with valid data, when I submit, then the entity is created
**AC-4.2.5:** Given the entity is created, when I view the list, then it appears with 0 events
**AC-4.2.6:** Given I create a vehicle entity, when I view it, then signature is auto-generated
**AC-4.2.7:** Given I upload a reference image, when creation succeeds, then image is stored and displayed
**AC-4.2.8:** Given I submit invalid data (vehicle without make), when submitted, then validation error shown

### P10-4.3: Allow Feedback Modification

**AC-4.3.1:** Given I have submitted thumbs up feedback, when I click thumbs up again, then I see options menu
**AC-4.3.2:** Given the options menu, when I click "Change to thumbs down", then rating changes
**AC-4.3.3:** Given rating changed, when I view the event, then "edited" indicator appears
**AC-4.3.4:** Given thumbs down with correction, when I click again, then I can edit the correction text
**AC-4.3.5:** Given I edit correction, when saved, then updated text is stored
**AC-4.3.6:** Given I want to remove feedback, when I click "Remove", then confirmation shown
**AC-4.3.7:** Given I confirm removal, when complete, then feedback is deleted
**AC-4.3.8:** Given feedback removed, when I view event, then buttons return to neutral state

### P10-4.4: Show Feedback History Indicator

**AC-4.4.1:** Given feedback was never edited, when I view the event, then no "edited" indicator shown
**AC-4.4.2:** Given feedback was edited, when I view the event, then small "edited" badge visible
**AC-4.4.3:** Given I hover over "edited" badge, when tooltip appears, then it shows edit timestamp
**AC-4.4.4:** Given feedback created and updated same second, when viewed, then not marked as edited

---

## Traceability Mapping

| AC | Spec Section | Component(s) | Test Idea |
|----|--------------|--------------|-----------|
| AC-4.1.1-2 | Entity Assignment | EventCard, EntitySelectModal | Component render test |
| AC-4.1.3 | Entity Assignment | EntitySelectModal | Search filter test |
| AC-4.1.4-5 | Entity Assignment | entities.py, EventCard | Integration test |
| AC-4.1.6-7 | Entity Assignment | EntitySelectModal | State handling test |
| AC-4.2.1-2 | Entity Creation | EntitiesPage, EntityCreateModal | Component render test |
| AC-4.2.3 | Entity Creation | EntityCreateModal | Conditional fields test |
| AC-4.2.4-6 | Entity Creation | entities.py, EntityCreateModal | Integration test |
| AC-4.2.7 | Entity Creation | entities.py | File upload test |
| AC-4.2.8 | Entity Creation | EntityCreateModal | Validation test |
| AC-4.3.1-3 | Feedback Modification | FeedbackButtons | State change test |
| AC-4.3.4-5 | Feedback Modification | FeedbackButtons, feedback.py | Edit flow test |
| AC-4.3.6-8 | Feedback Modification | FeedbackButtons, feedback.py | Delete flow test |
| AC-4.4.1-4 | Feedback Indicator | FeedbackButtons | Render logic test |

---

## Risks, Assumptions, Open Questions

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Entity search slow with many entities | Low | Medium | Add pagination, limit initial load to 50 |
| Users create duplicate entities | Medium | Low | Show similar matches during creation |
| Reference image storage grows large | Low | Low | Limit image size, compress on upload |
| Feedback edit conflicts | Low | Low | Use updated_at for optimistic locking |

### Assumptions

- Users understand the entity concept from P4/P9-4
- Entity list API supports search parameter (may need to add)
- Existing FeedbackButtons component can be extended for edit mode
- shadcn/ui Dialog handles nested modals gracefully

### Open Questions

- **Q1:** Should entity creation modal also be accessible from the entity select modal?
  - **A:** Yes - add "Create New" at bottom of entity list for quick creation flow

- **Q2:** Maximum size for reference images?
  - **A:** 2MB limit, resize to 512x512 max on server

- **Q3:** Should we show edit history beyond the indicator?
  - **A:** No - just "edited" indicator with timestamp tooltip is sufficient

- **Q4:** Keyboard navigation for entity select modal?
  - **A:** Yes - support arrow keys and Enter for accessibility

---

## Test Strategy Summary

### Test Levels

| Level | Scope | Tools | Coverage |
|-------|-------|-------|----------|
| Unit | API validators | pytest | Entity creation validation |
| Integration | Entity/Feedback APIs | pytest | CRUD operations |
| Component | Modals, forms | vitest, RTL | Render, interactions |
| E2E | Full flows | Manual | User journeys |

### Test Cases by Story

**P10-4.1 (Entity Assignment):**
- Component: Entity button renders on event card
- Component: Modal opens with entity list
- Component: Search filters entities
- Integration: Entity assignment API works
- Integration: Event card updates after assignment

**P10-4.2 (Entity Creation):**
- Component: Create button renders on page
- Component: Modal form renders correctly
- Component: Vehicle fields appear conditionally
- Component: Validation errors display
- Integration: Entity created in database
- Integration: Image upload works
- Unit: Signature generation

**P10-4.3 (Feedback Modification):**
- Component: Options appear on feedback click
- Component: Rating change UI works
- Component: Correction edit works
- Integration: PUT feedback works
- Integration: DELETE feedback works
- Component: Confirmation dialog

**P10-4.4 (Feedback Indicator):**
- Component: "Edited" badge renders when edited
- Component: Badge hidden when not edited
- Component: Tooltip shows timestamp
- Unit: was_edited property logic

### Test Data

- Entities: Mix of named/unnamed, person/vehicle types
- Vehicles: Various color/make/model combinations
- Feedback: Edited and non-edited samples
- Events: With and without entity assignments

---

_Generated by BMAD Epic Tech Context Workflow_
_Date: 2025-12-25_
_For: Brent_
