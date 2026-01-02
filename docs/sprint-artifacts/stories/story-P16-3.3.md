# Story P16-3.3: Add Edit Button to Entity Card

Status: drafted

## Story

As a **user**,
I want **an Edit button on entity cards**,
So that **I can quickly access the edit modal from the entities page**.

## Acceptance Criteria

1. **AC1**: Given I am viewing the Entities page, when I see an entity card, then there is an Edit button (pencil icon) in the card actions area
2. **AC2**: Given I click the Edit button, when the click event fires, then the EntityEditModal opens for that entity
3. **AC3**: Given I click the Edit button, the card click handler does NOT fire (stopPropagation prevents entity detail modal from opening)
4. **AC4**: The Edit button has a tooltip showing "Edit entity"
5. **AC5**: The Edit button is visible on hover for desktop, or always visible on mobile/touch devices

## Tasks / Subtasks

- [ ] Task 1: Add Edit button to EntityCard component (AC: 1, 4, 5)
  - [ ] Import Pencil icon from lucide-react
  - [ ] Add Edit button in card actions area alongside existing buttons
  - [ ] Add tooltip with "Edit entity" text
  - [ ] Style for hover visibility on desktop
- [ ] Task 2: Wire up EntityEditModal integration (AC: 2, 3)
  - [ ] Import EntityEditModal component
  - [ ] Add state for edit modal open/close
  - [ ] Add onClick handler with stopPropagation
  - [ ] Pass entity data to EntityEditModal
  - [ ] Handle onUpdated callback to refresh entity list
- [ ] Task 3: Write tests for Edit button functionality (AC: all)
  - [ ] Test Edit button renders on entity card
  - [ ] Test clicking Edit opens EntityEditModal
  - [ ] Test clicking Edit does not open detail modal (stopPropagation)
  - [ ] Test tooltip appears on hover

## Dev Notes

- **Component to modify**: `frontend/components/entities/EntityCard.tsx`
- **Modal component**: `frontend/components/entities/EntityEditModal.tsx` (created in P16-3.2)
- **Icon**: Use `Pencil` from lucide-react
- **Event handling**: Must use `e.stopPropagation()` to prevent card click from opening detail modal

### Project Structure Notes

- EntityCard already has action buttons pattern (e.g., "Add Alert" button)
- Follow existing button styling in EntityCard
- EntityEditModal expects `EntityEditData` interface with: id, entity_type, name, notes, is_vip, is_blocked, thumbnail_path

### References

- [Source: docs/epics-phase16.md#Story-P16-3.3]
- [Source: frontend/components/entities/EntityCard.tsx] - Component to modify
- [Source: frontend/components/entities/EntityEditModal.tsx] - Modal to integrate

### Learnings from Previous Story

**From Story P16-3.2 (EntityEditModal)**

- EntityEditModal component created at `frontend/components/entities/EntityEditModal.tsx`
- Modal accepts props: `open`, `onOpenChange`, `entity` (EntityEditData), `onUpdated`
- EntityEditData interface requires: id, entity_type, name, notes (optional), is_vip (optional), is_blocked (optional), thumbnail_path (optional)
- useUpdateEntity hook extended in `frontend/hooks/useEntities.ts`
- Modal handles success toast and query invalidation internally

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List

