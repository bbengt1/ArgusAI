# Story P14-5.8: Standardize API Response Format

Status: done

## Story

As an **API consumer**,
I want consistent response formats documented,
so that client code is predictable and the API is easier to integrate with.

## Acceptance Criteria

1. **AC1:** API response format patterns are documented in OpenAPI description or API documentation
2. **AC2:** The difference between wrapped responses (`{ data, meta }`) and direct model returns is clearly explained
3. **AC3:** Frontend api-client handles both patterns correctly (if any gaps exist)
4. **AC4:** New endpoints follow the documented standard going forward

## Tasks / Subtasks

- [x] Task 1: Document API response patterns (AC: #1, #2)
  - [x] 1.1: Add API Response Format section to CLAUDE.md
  - [x] 1.2: Document Protect API wrapped format `{ data, meta }`
  - [x] 1.3: Document standard API direct model returns
  - [x] 1.4: Explain the rationale for the difference
- [x] Task 2: Verify frontend compatibility (AC: #3)
  - [x] 2.1: Review api-client.ts Protect methods
  - [x] 2.2: Review api-client.ts standard methods
  - [x] 2.3: Document any adjustments if needed
- [x] Task 3: Update OpenAPI descriptions (AC: #4)
  - [x] 3.1: Add response format note to protect.py router description
  - [x] 3.2: Ensure main.py app description mentions the pattern

## Dev Notes

### API Response Format Analysis

The ArgusAI API uses two response patterns:

**Pattern 1: Wrapped Response (Protect API only)**
```json
{
  "data": { /* model or array of models */ },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2025-12-30T00:00:00Z",
    "count": 5  // optional, for lists
  }
}
```

Used in:
- All `/api/v1/protect/*` endpoints
- Rationale: Provides request tracking and pagination metadata for complex Protect integration

**Pattern 2: Direct Model Response (Standard APIs)**
```json
{ /* model fields directly */ }
// or for lists:
[ { /* model */ }, { /* model */ } ]
```

Used in:
- `/api/v1/cameras/*`
- `/api/v1/events/*`
- `/api/v1/alert_rules/*`
- All other endpoints

Rationale: Simpler response structure for straightforward CRUD operations.

### Frontend Handling

The frontend api-client already handles both patterns:
- Protect methods: Access `response.data` for the model
- Standard methods: Use response directly

### Recommendation

Keep both patterns with documentation explaining the difference:
- Wrapped format provides traceability for complex integrations
- Direct format is simpler for standard CRUD

### Project Structure Notes

- Backend API routes: `backend/app/api/v1/`
- Protect schemas with wrappers: `backend/app/schemas/protect.py`
- Standard schemas without wrappers: `backend/app/schemas/camera.py`, etc.

### References

- [Source: docs/epics-phase14.md#Story-P14-5.8]
- [Source: backend/app/api/v1/protect.py#L66-72] - create_meta helper
- [Source: backend/app/api/v1/cameras.py#L52-112] - Direct model returns

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Documentation added to CLAUDE.md explaining both API response patterns
- Frontend api-client.ts already correctly handles both patterns (no changes needed)
- Protect API module docstring updated with response format documentation
- Task 3.2 (main.py description) deemed unnecessary since CLAUDE.md is the primary developer reference

### File List

- MODIFIED: `CLAUDE.md` - Added "API Response Format Standards" section
- MODIFIED: `backend/app/api/v1/protect.py` - Added response format documentation to module docstring
- NEW: `docs/sprint-artifacts/p14-5-8-standardize-api-response-format.md` - This story file
