# Story 9.3.3: Implement Package False Positive Feedback

Status: drafted

## Story

As a **user**,
I want **to mark package detections as incorrect**,
So that **the system learns what is and isn't a package in my context**.

## Acceptance Criteria

1. **AC-3.3.1:** Given event with smart_detection_type="package", when viewing card, then "Not a package" button visible
2. **AC-3.3.2:** Given non-package event, when viewing card, then "Not a package" button not visible
3. **AC-3.3.3:** Given I click "Not a package", when submitted, then feedback stored with correction_type="not_package"
4. **AC-3.3.4:** Given I click "Not a package", when submitted, then toast confirms "Feedback recorded"
5. **AC-3.3.5:** Given I click "Not a package", when viewing button again, then shows "Marked as not a package"
6. **AC-3.3.6:** Given multiple "not_package" feedbacks exist, when prompt refinement runs, then examples included

## Tasks / Subtasks

- [ ] Task 1: Add correction_type field to EventFeedback model (AC: 3.3.3)
  - [ ] Add correction_type column to event_feedback table
  - [ ] Create Alembic migration for new column
  - [ ] Update FeedbackCreate and FeedbackResponse schemas
- [ ] Task 2: Update feedback API endpoint (AC: 3.3.3)
  - [ ] Accept correction_type in POST /api/v1/events/{id}/feedback
  - [ ] Store correction_type in database
- [ ] Task 3: Add "Not a package" button to FeedbackButtons component (AC: 3.3.1, 3.3.2)
  - [ ] Add smartDetectionType prop to FeedbackButtons
  - [ ] Show "Not a package" button only when type is "package"
  - [ ] Style button appropriately
- [ ] Task 4: Handle "Not a package" click (AC: 3.3.3, 3.3.4, 3.3.5)
  - [ ] Submit feedback with rating="not_helpful" and correction_type="not_package"
  - [ ] Show toast "Feedback recorded"
  - [ ] Update button to show "Marked as not a package" after submission
- [ ] Task 5: Pass smartDetectionType from EventCard to FeedbackButtons
  - [ ] Pass event.smart_detection_type to FeedbackButtons
- [ ] Task 6: Write unit tests
  - [ ] Backend: Test feedback storage with correction_type
  - [ ] Frontend: Test button visibility logic
  - [ ] Frontend: Test button state changes
- [ ] Task 7: Run all tests to verify

## Dev Notes

### Technical Approach

Add a `correction_type` field to the feedback model to track specific types of corrections beyond just "not helpful". For package false positives, users can quickly mark events as "not a package" with a single click.

### Database Migration

```python
# Add correction_type column
op.add_column('event_feedback',
    sa.Column('correction_type', sa.String(50), nullable=True)
)
```

### Correction Types

- `not_package` - Event incorrectly classified as package
- (Future: `not_person`, `not_vehicle`, `not_animal`)

### UI Changes

The FeedbackButtons component will show an additional "Not a package" button (Package icon with X) when the event's smart_detection_type is "package".

```tsx
{smartDetectionType === 'package' && (
  <Button onClick={handleNotPackage}>
    {correctionType === 'not_package' ? 'Marked as not a package' : 'Not a package'}
  </Button>
)}
```

### Source Components

- `backend/app/models/event_feedback.py` - Add correction_type field
- `backend/app/schemas/feedback.py` - Update schemas
- `backend/app/api/v1/events.py` - Update feedback endpoint
- `frontend/components/events/FeedbackButtons.tsx` - Add button
- `frontend/components/events/EventCard.tsx` - Pass detection type

### Learnings from Previous Stories

**From Story p9-3-2-attempt-frame-overlay-text-extraction (Status: done)**

- Settings toggles in frontend use immediate API update pattern
- Component tests important for UI changes
- TypeScript types need updating when adding new fields

### Testing Standards

- Backend: Test correction_type storage and retrieval
- Frontend: Component tests for button visibility
- Frontend: Component tests for button state changes
- Integration: End-to-end feedback flow

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P9-3.md#P9-3.3]
- [Source: docs/epics-phase9.md#Story P9-3.3]
- [Backlog: IMP-013]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List

