# Story P16-3.4: Add Edit Button to Entity Detail Modal

Status: drafted

## Story

As a **user**,
I want **to edit an entity from its detail modal**,
So that **I can make changes while viewing entity details**.

## Acceptance Criteria

1. **AC1**: Given I have the EntityDetail modal open, when I see the header, then there is an Edit button (pencil icon) positioned near the close button
2. **AC2**: Given I click the Edit button, when the click event fires, then the EntityEditModal opens for that entity
3. **AC3**: Given I save changes in EntityEditModal, when the save completes, then the EntityDetail refreshes to show updated values
4. **AC4**: The Edit button has a tooltip showing "Edit entity"
5. **AC5**: The Edit button works on both desktop and mobile layouts

## Tasks / Subtasks

- [ ] Task 1: Add Edit button to EntityDetail component header (AC: 1, 4, 5)
  - [ ] Import Pencil icon from lucide-react
  - [ ] Import Tooltip components from shadcn/ui
  - [ ] Import EntityEditModal component
  - [ ] Add Edit button in DialogHeader area
  - [ ] Add tooltip with "Edit entity" text
- [ ] Task 2: Wire up EntityEditModal integration (AC: 2, 3)
  - [ ] Add state for edit modal open/close
  - [ ] Add onClick handler for edit button
  - [ ] Pass entity data to EntityEditModal
  - [ ] Handle onUpdated callback to refetch entity data
- [ ] Task 3: Write tests for Edit button functionality (AC: all)
  - [ ] Test Edit button renders in EntityDetail header
  - [ ] Test clicking Edit opens EntityEditModal
  - [ ] Test tooltip appears on hover

## Dev Notes

- **Component to modify**: `frontend/components/entities/EntityDetail.tsx`
- **Modal component**: `frontend/components/entities/EntityEditModal.tsx` (created in P16-3.2)
- **Icon**: Use `Pencil` from lucide-react
- **Nested modal pattern**: Follow existing EventDetailModal pattern in EntityDetail

### Project Structure Notes

- EntityDetail uses Dialog from shadcn/ui with DialogHeader
- Uses useEntity hook to fetch entity details
- Already has nested modal pattern with EventDetailModal
- EntityEditModal expects `EntityEditData` interface with: id, entity_type, name, notes, is_vip, is_blocked, thumbnail_path

### References

- [Source: docs/epics-phase16.md#Story-P16-3.4]
- [Source: frontend/components/entities/EntityDetail.tsx] - Component to modify
- [Source: frontend/components/entities/EntityEditModal.tsx] - Modal to integrate

### Learnings from Previous Stories

**From Story P16-3.3 (Edit Button on EntityCard)**

- EntityEditModal component at `frontend/components/entities/EntityEditModal.tsx`
- Modal accepts props: `open`, `onOpenChange`, `entity` (EntityEditData), `onUpdated`
- EntityEditData interface requires: id, entity_type, name, notes (optional), is_vip (optional), is_blocked (optional), thumbnail_path (optional)
- Modal handles success toast and query invalidation internally

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5

### Debug Log References

### Completion Notes List

### File List

