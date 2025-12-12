# argusai - Epic Breakdown

**Date:** 2025-11-15
**Project Level:** Simple (Quick Flow)

---

## Epic 1: Deprecation Fixes

**Slug:** deprecation-fixes

### Goal

Eliminate deprecation warnings from FastAPI and Python datetime usage to ensure future library compatibility and maintain a clean, professional codebase. This technical debt fix prevents future breakage when dependencies are upgraded and improves developer experience by removing noisy warnings from test output.

### Scope

**In Scope:**
- ✅ Migrate FastAPI event handlers to lifespan pattern (main.py)
- ✅ Replace datetime.utcnow() with datetime.now(timezone.utc) (camera_service.py, camera.py)
- ✅ Verify all 78 existing tests pass after migration
- ✅ Eliminate 3042+ deprecation warnings from test output

**Out of Scope:**
- ❌ New feature development
- ❌ Performance optimizations beyond the migration
- ❌ Additional test creation (existing tests sufficient)
- ❌ Backward compatibility with older library versions
- ❌ Other deprecations not identified in code review

### Success Criteria

1. ✅ FastAPI `@app.on_event()` decorators completely removed and replaced with lifespan handler
2. ✅ All `datetime.utcnow()` calls replaced with `datetime.now(timezone.utc)`
3. ✅ Application starts and shuts down successfully with new lifespan pattern
4. ✅ All 78 tests pass with 100% pass rate (no regressions)
5. ✅ Deprecation warnings reduced from 3042+ to minimal levels
6. ✅ No functional changes to application behavior (timestamps, startup/shutdown logic identical)

### Dependencies

**Prerequisites:**
- None (can be implemented immediately)

**External Dependencies:**
- FastAPI 0.115.0 (already installed, supports lifespan)
- Python 3.11+ (already installed, supports timezone parameter)

**Internal Dependencies:**
- camera_service singleton (modified for datetime)
- Database engine and Base (used in lifespan)
- All 78 existing tests (for validation)

---

## Story Map - Epic 1

```
Epic: Deprecation Fixes (2 points)
└── Story 1.1: Migrate Deprecated Patterns (2 points)
    Dependencies: None
    Outcome: Clean codebase ready for future library upgrades
```

---

## Stories - Epic 1

### Story 1.1: Migrate Deprecated Patterns

As a **developer**,
I want **deprecation warnings eliminated from FastAPI event handlers and datetime usage**,
So that **the codebase is future-proof and library upgrades won't break the application**.

**Acceptance Criteria:**

- **AC #1:** `@app.on_event("startup")` and `@app.on_event("shutdown")` removed from main.py
- **AC #2:** Lifespan context manager implemented with identical startup/shutdown behavior
- **AC #3:** All `datetime.utcnow()` calls replaced with `datetime.now(timezone.utc)`
- **AC #4:** All 78 tests pass with 100% pass rate
- **AC #5:** Deprecation warnings reduced from 3042+ to minimal

**Prerequisites:** None

**Technical Notes:**
- Use `@asynccontextmanager` pattern for FastAPI lifespan
- Update SQLAlchemy defaults to use lambda for callable execution
- Maintain identical functional behavior (pure refactoring)

**Estimated Effort:** 2 story points (1-2 hours)

---

## Implementation Timeline - Epic 1

**Total Story Points:** 2

**Estimated Timeline:** 1-2 hours (single development session)

---
