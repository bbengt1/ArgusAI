# argusai - Technical Specification

**Author:** Brent
**Date:** 2025-11-15
**Project Level:** Simple (Quick Flow)
**Change Type:** Technical Debt / Deprecation Fixes
**Development Context:** Brownfield - Existing Codebase

---

## Context

### Available Documents

**Documents Loaded:**
- ✅ Product Brief: `docs/product-brief.md` - ArgusAI vision and architecture
- ✅ Architecture Document: `docs/architecture.md` - Event-driven system design
- ✅ Code Review: F2-1 Motion Detection Algorithm review (2025-11-15)

**Origin:**
This tech-spec addresses deprecation warnings identified during Senior Developer review of Story F2-1. The code review flagged two medium/low severity findings that will cause breakage in future library versions.

### Project Stack

**Current Stack (Detected from requirements.txt):**
- **Framework:** FastAPI 0.115.0 (supports lifespan handlers)
- **Language:** Python 3.11+ (datetime.now(timezone.utc) available)
- **Database ORM:** SQLAlchemy 2.0.36 with Alembic migrations
- **Testing:** pytest 7.4.3, pytest-asyncio 0.21.1
- **Camera/CV:** opencv-python 4.12.0
- **Security:** cryptography 41.0.7, python-jose 3.3.0

**Python Version:** 3.11+ (confirmed - datetime.now(timezone.utc) supported)
**FastAPI Version:** 0.115.0 (confirmed - lifespan handlers fully supported since 0.93+)

### Existing Codebase Structure

**Project Organization:**
- `/backend` - Python FastAPI backend
  - `/app` - Application code
    - `/api/v1/` - REST API endpoints
    - `/models/` - SQLAlchemy ORM models
    - `/services/` - Business logic services
    - `/core/` - Core configuration and database
  - `/tests/` - Test suite (78 tests, 100% pass rate)
  - `main.py` - FastAPI application entry point
  - `requirements.txt` - Python dependencies

**Key Files for This Change:**
- `backend/main.py` - FastAPI app with deprecated event handlers (lines 47, 77)
- `backend/app/services/camera_service.py` - Service using datetime.utcnow() (line 419)
- `backend/app/models/camera.py` - SQLAlchemy model with utcnow default (lines 50-51)

**Testing Structure:**
- Test framework: pytest with async support (pytest-asyncio)
- Test location: `/backend/tests/`
- Current status: 78 tests passing, 0 failures
- Test execution: `pytest -v --tb=short`

---

## The Change

### Problem Statement

**Issue:** Code review of Story F2-1 (Motion Detection Algorithm) identified deprecation warnings that will cause application breakage in future library versions:

**FINDING-1 (MEDIUM Severity):**
- **Location:** `main.py:47, 77`
- **Issue:** Using deprecated `@app.on_event("startup")` and `@app.on_event("shutdown")` decorators
- **Impact:** Will break in future FastAPI versions (deprecated since 0.93, removal planned)
- **Evidence:** 3042 deprecation warnings during test execution

**FINDING-2 (LOW Severity):**
- **Location:** `camera_service.py:419`, `camera.py:50-51`
- **Issue:** `datetime.utcnow()` deprecated in Python 3.12+ (scheduled for removal)
- **Impact:** Will break in future Python versions
- **Evidence:** Multiple deprecation warnings in test output

**Business Impact:**
- Future library upgrades blocked until fixed
- Technical debt accumulating
- Developer experience degraded (noisy warnings)
- Risk of runtime breakage if dependencies auto-update

### Proposed Solution

**Approach:** Migrate deprecated patterns to modern, future-proof alternatives in a single focused story.

**Solution 1: FastAPI Lifespan Migration**
- Replace `@app.on_event()` decorators with contextual lifespan handler
- Use `@asynccontextmanager` pattern (FastAPI best practice since 0.93+)
- Maintain identical startup/shutdown behavior
- Zero functional changes - pure refactoring

**Solution 2: Datetime UTC Migration**
- Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
- Update SQLAlchemy model defaults to use timezone-aware datetimes
- Ensure consistency across all datetime usage
- Maintain identical timestamp behavior (UTC, timezone-aware)

**Why One Story:**
Both fixes are:
- Related (library deprecation updates)
- Non-functional (behavior unchanged)
- Low risk (well-documented migration paths)
- Quick to implement (1-2 hours total)

### Scope

**In Scope:**
- ✅ Migrate FastAPI startup/shutdown to lifespan handler in `main.py`
- ✅ Replace `datetime.utcnow()` with `datetime.now(timezone.utc)` in `camera_service.py`
- ✅ Update SQLAlchemy datetime defaults in `camera.py`
- ✅ Verify all 78 existing tests pass after migration
- ✅ Validate no new deprecation warnings appear

**Out of Scope:**
- ❌ New feature development
- ❌ Performance optimizations beyond the migration
- ❌ Additional test creation (existing tests sufficient)
- ❌ Backward compatibility with older FastAPI/Python (direct migration)
- ❌ Migration of other potential deprecations not in code review

---

## Implementation Details

### Source Tree Changes

**Files to MODIFY (3 files):**

1. **`backend/main.py`** - MODIFY
   - **Lines 47-74:** Remove `@app.on_event("startup")` decorator and function
   - **Lines 77-90:** Remove `@app.on_event("shutdown")` decorator and function
   - **New code:** Add `@asynccontextmanager` lifespan function (lines ~15-35)
   - **Line 24:** Update FastAPI initialization to use lifespan parameter

2. **`backend/app/services/camera_service.py`** - MODIFY
   - **Line 419:** Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`
   - **Import change:** Add `timezone` to datetime import (line 12)

3. **`backend/app/models/camera.py`** - MODIFY
   - **Lines 50-51:** Update `created_at` and `updated_at` column defaults
   - **Change:** Replace `default=datetime.utcnow` with `default=lambda: datetime.now(timezone.utc)`
   - **Import change:** Add `timezone` to datetime import (line 7)

**Files to READ/REFERENCE (0 new files created):**
- All changes are modifications to existing files
- No new files, no deleted files

### Technical Approach

**FastAPI Lifespan Migration Pattern:**

Current deprecated pattern:
```python
@app.on_event("startup")
async def startup_event():
    # Startup logic
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # Shutdown logic
    pass

app = FastAPI()
```

**New pattern (FastAPI 0.93+):**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Application starting up...")
    Base.metadata.create_all(bind=engine)
    logger.info("Application startup complete")

    yield  # Application runs here

    # Shutdown logic
    logger.info("Application shutting down...")
    camera_service.stop_all_cameras(timeout=5.0)
    logger.info("Application shutdown complete")

app = FastAPI(
    title="ArgusAI API",
    description="API for camera-based motion detection and AI-powered object description",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # ← Pass lifespan here
)
```

**Datetime Migration Pattern:**

Current deprecated pattern:
```python
from datetime import datetime

# In camera_service.py
"last_frame_time": datetime.utcnow() if status == "connected" else None

# In camera.py (SQLAlchemy model)
created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

**New pattern (Python 3.11+):**
```python
from datetime import datetime, timezone

# In camera_service.py
"last_frame_time": datetime.now(timezone.utc) if status == "connected" else None

# In camera.py (SQLAlchemy model)
created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
```

**Key Differences:**
- `datetime.utcnow()` returns **naive** datetime (no timezone info)
- `datetime.now(timezone.utc)` returns **aware** datetime (with UTC timezone)
- SQLAlchemy requires `lambda:` wrapper for callable defaults (prevents call at import time)

### Existing Patterns to Follow

**Code Style (from existing codebase):**
- **Import style:** Absolute imports, grouped by standard/third-party/local
- **Docstrings:** Triple-quoted strings for modules and functions
- **Logging:** Use module-level logger, structured logging messages
- **Error handling:** Try-except with specific exceptions, log with exc_info=True

**FastAPI Patterns:**
- Event handlers in `main.py` at top level (before route registration)
- Middleware registration after FastAPI instantiation
- Router registration uses `app.include_router()`
- Startup logic includes database table creation

**Datetime Patterns:**
- All timestamps use UTC timezone
- SQLAlchemy models use `DateTime` type (not `DateTime(timezone=True)` - SQLite limitation)
- Timestamps created on server side, not client side

### Integration Points

**Database Integration:**
- SQLAlchemy ORM with SQLite backend
- Database engine created in `app/core/database.py`
- Table creation happens at startup (moving to lifespan)
- No schema changes required (datetime behavior identical)

**Camera Service Integration:**
- Singleton `camera_service` instance imported in `main.py`
- Shutdown calls `camera_service.stop_all_cameras(timeout=5.0)`
- Camera service cleanup must complete during shutdown
- Moving to lifespan ensures proper cleanup order

**Testing Integration:**
- pytest with async support (pytest-asyncio)
- Tests use FastAPI TestClient for endpoint testing
- Lifespan events automatically triggered by TestClient
- No test code changes required (TestClient handles lifespan)

---

## Development Context

### Relevant Existing Code

**Reference Files for Migration:**

1. **`main.py` Current Implementation:**
   - Lines 47-74: Startup event handler (database table creation, camera loading TODO)
   - Lines 77-90: Shutdown event handler (camera cleanup)
   - Pattern: Simple async functions with logging
   - Import: Uses `from fastapi import FastAPI`

2. **`camera_service.py` Datetime Usage:**
   - Line 419: `_update_status()` method creates status dict with timestamp
   - Pattern: Uses `datetime.utcnow()` for "last_frame_time" field
   - Context: Thread-safe status tracking for camera connections

3. **`camera.py` SQLAlchemy Defaults:**
   - Line 50: `created_at = Column(DateTime, default=datetime.utcnow, nullable=False)`
   - Line 51: `updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)`
   - Pattern: Automatic timestamp columns on Camera model

**FastAPI Lifespan Resources:**
- Official docs: https://fastapi.tiangolo.com/advanced/events/
- Migration guide: https://fastapi.tiangolo.com/release-notes/#0930
- Example: Search codebase for any existing lifespan usage (none found)

### Dependencies

**Framework/Libraries:**
- FastAPI 0.115.0 (lifespan support since 0.93.0)
- Python 3.11+ (timezone parameter available)
- contextlib (standard library - asynccontextmanager)
- SQLAlchemy 2.0.36 (no changes needed)
- pytest 7.4.3 (TestClient supports lifespan)

**Internal Modules:**
- `app.core.config` - Settings configuration
- `app.core.database` - Database engine and Base
- `app.api.v1.cameras` - Camera router and camera_service singleton
- `app.api.v1.motion_events` - Motion events router

### Configuration Changes

**No configuration file changes required.**

All changes are code-only:
- Import additions (contextlib, timezone)
- Function signature changes (lifespan context manager)
- Datetime call updates (utcnow → now(timezone.utc))

**Environment variables:** No changes to `.env` or `.env.example`

### Existing Conventions (Brownfield)

**Code Style (Detected from existing files):**
- **Indentation:** 4 spaces (Python PEP 8)
- **Line length:** ~120 characters (relaxed PEP 8)
- **Quotes:** Double quotes for strings
- **Imports:** Grouped and sorted (standard, third-party, local)
- **Logging:** Module-level logger with `logger = logging.getLogger(__name__)`
- **Docstrings:** Triple-quoted, follow Google style

**Error Handling:**
- Try-except blocks with specific exceptions
- Logging with `exc_info=True` for stack traces
- Graceful degradation where possible

**Async Patterns:**
- Use `async def` for async functions
- Use `await` for async calls
- FastAPI dependency injection with `Depends()`

### Test Framework & Standards

**Test Framework:** pytest 7.4.3 with pytest-asyncio 0.21.1

**Test File Locations:**
- `tests/test_api/` - API endpoint tests
- `tests/test_models/` - SQLAlchemy model tests
- `tests/test_services/` - Service layer tests

**Test Patterns:**
- **Naming:** `test_*.py` files, `test_*` functions
- **Fixtures:** pytest fixtures in `conftest.py`
- **Async:** Use `@pytest.mark.asyncio` for async tests
- **Assertions:** Standard assert statements
- **Mocking:** unittest.mock (imported as `from unittest.mock import Mock, patch`)

**Coverage Requirements:**
- No formal coverage requirement
- Current: 78 tests passing, 100% pass rate
- Goal: Maintain 100% pass rate after migration

---

## Implementation Stack

**Runtime Environment:**
- Python 3.11+ (confirmed compatible)
- FastAPI 0.115.0 (lifespan supported)
- Uvicorn ASGI server (included with fastapi[standard])

**Core Dependencies:**
- FastAPI 0.115.0 - Web framework
- SQLAlchemy 2.0.36 - ORM
- Alembic 1.14.0 - Database migrations
- opencv-python 4.12.0 - Camera/CV library
- pydantic 2.10.0 - Data validation

**Testing Stack:**
- pytest 7.4.3 - Test framework
- pytest-asyncio 0.21.1 - Async test support
- httpx 0.25.2 - TestClient backend

**All dependencies already installed** - no new packages required for this migration.

---

## Technical Details

### FastAPI Lifespan Technical Details

**Execution Flow:**
1. FastAPI app instantiation creates lifespan context manager
2. On app startup: Code before `yield` executes
3. App runs and serves requests
4. On app shutdown: Code after `yield` executes
5. Context manager ensures cleanup even on crash

**Key Behaviors:**
- Lifespan runs exactly once (startup + shutdown)
- Exceptions before yield prevent app from starting
- Exceptions after yield are logged but don't prevent shutdown
- TestClient automatically triggers lifespan events

**Database Table Creation:**
- Current: `Base.metadata.create_all(bind=engine)` in startup event
- After migration: Same call in lifespan before yield
- Behavior: Identical (creates tables if not exist, idempotent)

**Camera Cleanup:**
- Current: `camera_service.stop_all_cameras(timeout=5.0)` in shutdown event
- After migration: Same call in lifespan after yield
- Behavior: Identical (stops all camera threads gracefully)

### Datetime Technical Details

**Timezone-Aware vs Naive Datetimes:**
- **Naive:** `datetime.utcnow()` - no timezone info attached
- **Aware:** `datetime.now(timezone.utc)` - includes UTC timezone
- **Advantage:** Aware datetimes prevent timezone bugs, explicit about UTC

**SQLAlchemy Lambda Pattern:**
- **Wrong:** `default=datetime.now(timezone.utc)` - calls once at import, all rows get same timestamp
- **Correct:** `default=lambda: datetime.now(timezone.utc)` - calls on each insert
- **Reason:** SQLAlchemy evaluates defaults at row creation time, lambda defers execution

**Database Storage:**
- SQLite stores datetimes as strings (ISO 8601 format)
- Both naive and aware datetimes stored identically in SQLite
- No database migration required (storage format unchanged)

**Testing Impact:**
- Aware datetimes have `.tzinfo` attribute set to `timezone.utc`
- Comparison between aware and naive datetimes raises TypeError
- Existing tests use `datetime.now(timezone.utc)` in MotionEvent tests (already compatible)

### Edge Cases

**Edge Case 1: TestClient Lifespan Support**
- **Issue:** Old pytest-starlette versions didn't support lifespan
- **Status:** pytest-asyncio 0.21.1 includes TestClient with full lifespan support
- **Action:** No changes needed, existing tests will work

**Edge Case 2: Startup Failure Handling**
- **Current:** Exception in startup event crashes app with traceback
- **After Migration:** Exception before yield crashes app (same behavior)
- **Handling:** Already has try-except in camera loading (commented TODO)

**Edge Case 3: Shutdown Timeout**
- **Current:** Camera service has 5-second timeout for thread cleanup
- **After Migration:** Same timeout behavior preserved
- **Risk:** If threads don't stop, app shutdown delayed but completes

**Edge Case 4: DateTime Comparison**
- **Risk:** Mixing aware and naive datetimes causes TypeError
- **Mitigation:** All datetime usage in codebase will be aware after this change
- **Validation:** Run full test suite to catch any comparison issues

---

## Development Setup

**Prerequisites:**
- Python 3.11+ installed
- Virtual environment activated
- Dependencies installed from requirements.txt

**Setup Steps:**
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (create if needed)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Verify current state
pytest -v --tb=short  # Should show 78 passing tests with deprecation warnings
```

**Development Environment:**
- IDE: VS Code or PyCharm recommended
- Linting: Ruff (if configured) or pylint
- Formatting: Black (if configured)
- Python extension for IDE autocomplete

---

## Implementation Guide

### Setup Steps

**Pre-Implementation Checklist:**
1. ✅ Verify working directory: `backend/`
2. ✅ Activate virtual environment
3. ✅ Run tests to confirm baseline: `pytest -v --tb=short`
4. ✅ Note current deprecation warning count (3042 warnings)
5. ✅ Create feature branch: `git checkout -b fix/deprecation-warnings`
6. ✅ Have code review findings open for reference

### Implementation Steps

**Step 1: Migrate FastAPI Lifespan (main.py)**

**1.1: Add contextlib import**
- Location: `backend/main.py:6` (after FastAPI import)
- Action: Add `from contextlib import asynccontextmanager`

**1.2: Create lifespan context manager**
- Location: `backend/main.py:23` (before FastAPI app instantiation)
- Action: Add complete lifespan function with startup and shutdown logic
- Code:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      """Application lifespan handler for startup and shutdown events"""
      # Startup
      logger.info("Application starting up...")
      Base.metadata.create_all(bind=engine)
      logger.info("Database tables created/verified")
      # TODO: Load enabled cameras (when ready)
      logger.info("Application startup complete")

      yield  # App runs here

      # Shutdown
      logger.info("Application shutting down...")
      camera_service.stop_all_cameras(timeout=5.0)
      logger.info("Application shutdown complete")
  ```

**1.3: Update FastAPI initialization**
- Location: `backend/main.py:24` (app = FastAPI(...))
- Action: Add `lifespan=lifespan` parameter
- Code:
  ```python
  app = FastAPI(
      title="ArgusAI API",
      description="API for camera-based motion detection and AI-powered object description",
      version="1.0.0",
      docs_url="/docs",
      redoc_url="/redoc",
      lifespan=lifespan  # ← Add this parameter
  )
  ```

**1.4: Remove old event handlers**
- Location: `backend/main.py:47-90` (entire @app.on_event blocks)
- Action: Delete both `@app.on_event("startup")` and `@app.on_event("shutdown")` functions
- Verify: No references to `@app.on_event` remain in file

**Step 2: Update Datetime Usage (camera_service.py)**

**2.1: Update datetime import**
- Location: `backend/app/services/camera_service.py:12`
- Current: `from datetime import datetime`
- New: `from datetime import datetime, timezone`

**2.2: Replace datetime.utcnow() call**
- Location: `backend/app/services/camera_service.py:419`
- Current: `"last_frame_time": datetime.utcnow() if status == "connected" else None`
- New: `"last_frame_time": datetime.now(timezone.utc) if status == "connected" else None`

**Step 3: Update SQLAlchemy Defaults (camera.py)**

**3.1: Update datetime import**
- Location: `backend/app/models/camera.py:7`
- Current: `from datetime import datetime`
- New: `from datetime import datetime, timezone`

**3.2: Update created_at default**
- Location: `backend/app/models/camera.py:50`
- Current: `created_at = Column(DateTime, default=datetime.utcnow, nullable=False)`
- New: `created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)`

**3.3: Update updated_at defaults**
- Location: `backend/app/models/camera.py:51`
- Current: `updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)`
- New: `updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)`

**Step 4: Verify and Test**

**4.1: Run full test suite**
```bash
pytest -v --tb=short
```
- Expected: 78 tests passing, 0 failures
- Expected: Significantly fewer deprecation warnings (should drop from 3042 to minimal)

**4.2: Check for remaining deprecation warnings**
```bash
pytest -v 2>&1 | grep -i "deprecated" | wc -l
```
- Expected: Very low count (not 3042)
- FastAPI and datetime warnings should be gone

**4.3: Manual smoke test**
```bash
# Start the server
python main.py

# Check logs for:
# - "Application starting up..."
# - "Database tables created/verified"
# - "Application startup complete"

# Stop server (Ctrl+C) and check:
# - "Application shutting down..."
# - "Application shutdown complete"
```

### Testing Strategy

**Test Approach: Existing Test Validation**
- **Goal:** Verify migration doesn't break existing functionality
- **Method:** Run full test suite and confirm 100% pass rate
- **No new tests required:** Migration is refactoring, behavior unchanged

**Test Execution:**
```bash
# Full test suite with verbose output
pytest -v --tb=short

# With coverage (optional)
pytest --cov=app --cov-report=term-missing

# Specific test categories to verify
pytest tests/test_api/ -v           # API endpoints (lifespan affects these)
pytest tests/test_models/ -v        # Models (datetime affects these)
pytest tests/test_services/ -v      # Services (datetime affects camera_service)
```

**Success Criteria:**
1. ✅ All 78 tests pass (100% pass rate maintained)
2. ✅ No new test failures introduced
3. ✅ Deprecation warnings reduced to minimal levels
4. ✅ Manual startup/shutdown logs show lifespan execution
5. ✅ Camera service cleanup executes during shutdown

**Failure Investigation:**
- If tests fail: Check datetime comparison issues (aware vs naive)
- If startup fails: Check lifespan syntax and exception handling
- If warnings persist: Verify all utcnow() calls replaced

### Acceptance Criteria

**AC-1: FastAPI Lifespan Migration Complete**
- ✅ `@app.on_event("startup")` removed from main.py
- ✅ `@app.on_event("shutdown")` removed from main.py
- ✅ `lifespan` context manager implemented with startup/shutdown logic
- ✅ FastAPI app instantiated with `lifespan=lifespan` parameter
- ✅ Server starts successfully and logs "Application startup complete"
- ✅ Server shutdown executes camera cleanup and logs "Application shutdown complete"

**AC-2: Datetime Migration Complete**
- ✅ `datetime.utcnow()` replaced with `datetime.now(timezone.utc)` in camera_service.py
- ✅ SQLAlchemy `created_at` default updated to lambda in camera.py
- ✅ SQLAlchemy `updated_at` defaults updated to lambda in camera.py
- ✅ All datetime objects are timezone-aware (have .tzinfo attribute)

**AC-3: No Functional Regressions**
- ✅ All 78 tests pass (100% pass rate)
- ✅ No new test failures introduced
- ✅ Database table creation works identically
- ✅ Camera service cleanup works identically
- ✅ Timestamp behavior unchanged (still UTC)

**AC-4: Deprecation Warnings Eliminated**
- ✅ FastAPI `on_event` deprecation warnings eliminated (was 3042+ warnings)
- ✅ Python `datetime.utcnow` deprecation warnings eliminated
- ✅ Test execution shows minimal warnings (unrelated to this fix)
- ✅ Clean test output enables detection of future warnings

**AC-5: Code Quality Maintained**
- ✅ Existing code style preserved (imports, formatting, logging)
- ✅ Docstrings added to lifespan function
- ✅ No commented-out code left behind
- ✅ All imports properly organized

---

## Developer Resources

### File Paths Reference

**Files Modified (3 files):**
1. `backend/main.py` - FastAPI app initialization and lifespan
2. `backend/app/services/camera_service.py` - Camera service datetime usage
3. `backend/app/models/camera.py` - SQLAlchemy model datetime defaults

**Files Referenced (no changes):**
- `backend/app/core/database.py` - Database engine and Base
- `backend/app/core/config.py` - Settings configuration
- `backend/requirements.txt` - Dependencies (verify versions)

### Key Code Locations

**Before/After Reference:**

**main.py:**
- Old startup: Lines 47-74 (`@app.on_event("startup")`)
- Old shutdown: Lines 77-90 (`@app.on_event("shutdown")`)
- New lifespan: Lines ~23-40 (`@asynccontextmanager`)
- App init: Line 24 (add `lifespan=lifespan` parameter)

**camera_service.py:**
- Datetime usage: Line 419 (`_update_status` method)
- Import: Line 12 (add `timezone`)

**camera.py:**
- created_at: Line 50 (Column definition)
- updated_at: Line 51 (Column definition)
- Import: Line 7 (add `timezone`)

### Testing Locations

**Test Execution:**
- Working directory: `backend/`
- Command: `pytest -v --tb=short`
- Configuration: `pytest.ini` (if exists)

**Test Files Affected:**
- All tests in `tests/` directory (validation pass)
- No specific test file changes needed
- TestClient automatically handles lifespan

### Documentation to Update

**No documentation updates required** for this technical refactoring.

Optional (if project has):
- CHANGELOG.md - Note deprecation fixes
- README.md - No changes needed
- API docs - Auto-generated, no changes

---

## UX/UI Considerations

**No UI/UX impact** - backend-only technical refactoring.

- No user-facing features affected
- No API endpoint changes
- No database schema changes
- No configuration changes
- Behavior identical from user perspective

---

## Testing Approach

**Test Strategy: Existing Test Validation**

**Framework:** pytest 7.4.3 with pytest-asyncio 0.21.1

**CONFORM TO EXISTING TEST STANDARDS:**
- File naming: `test_*.py`
- Test function naming: `test_*`
- Assertion style: Standard `assert` statements
- Mocking: `unittest.mock` (Mock, patch)
- Async tests: `@pytest.mark.asyncio` decorator
- Fixtures: Defined in `conftest.py`

**Test Strategy:**
- **No new tests required** (per user requirement)
- **Goal:** Verify all 78 existing tests still pass
- **Unit tests:** Already cover models, services, API endpoints
- **Integration tests:** Already cover full request/response cycles
- **Lifespan testing:** TestClient automatically triggers lifespan events

**Coverage:**
- **Target:** Maintain 100% test pass rate
- **Areas validated by existing tests:**
  - FastAPI app initialization (TestClient triggers lifespan)
  - Database table creation (verified in model tests)
  - Camera service operations (verified in service tests)
  - Datetime handling (verified in model and service tests)

**Test Execution:**
```bash
# Run full suite
pytest -v --tb=short

# Expected output:
# ====================== 78 passed in XXs ======================
# With minimal deprecation warnings (not 3042)
```

**Validation Checklist:**
- ✅ All tests pass (78/78)
- ✅ No new failures
- ✅ Deprecation warnings eliminated
- ✅ Test execution time unchanged
- ✅ No test code modifications needed

---

## Deployment Strategy

### Deployment Steps

**Standard Deployment Process:**
1. Merge feature branch to main
2. Verify CI/CD pipeline passes (if configured)
3. Deploy to staging (if exists)
4. Run smoke tests on staging
5. Deploy to production
6. Monitor startup/shutdown logs

**Specific Validation:**
- Check startup logs for "Application startup complete"
- Check shutdown logs for "Application shutdown complete"
- Verify database tables created
- Verify camera cleanup executes

### Rollback Plan

**If Issues Occur:**

**Rollback Method:**
```bash
# Revert the commit
git revert <commit-hash>

# Or checkout previous version
git checkout <previous-commit>

# Redeploy
<standard deployment process>
```

**Indicators for Rollback:**
- App fails to start (lifespan exception)
- Tests fail in production environment
- Database initialization fails
- Camera cleanup hangs on shutdown

**Recovery:**
- Rollback restores old event handler pattern
- Zero data loss (no schema changes)
- Immediate recovery (code-only change)

### Monitoring

**What to Monitor After Deployment:**

**Startup Monitoring:**
- Application startup logs (should see lifespan messages)
- Database connection success
- Table creation/verification success
- No exceptions in startup phase

**Runtime Monitoring:**
- No datetime-related errors in logs
- Timestamp format unchanged in database
- Camera service operations normal

**Shutdown Monitoring:**
- Graceful shutdown completion
- Camera threads stop within timeout
- No resource leaks or hanging processes

**Error Indicators:**
- Exceptions mentioning "lifespan"
- Datetime comparison TypeErrors
- Startup or shutdown timeouts

---
