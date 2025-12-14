# Epic Technical Specification: CI/CD & Testing Infrastructure

Date: 2025-12-14
Author: Brent
Epic ID: P5-3
Status: Draft

---

## Overview

Epic P5-3 establishes automated testing infrastructure for ArgusAI through GitHub Actions CI/CD pipeline and frontend testing framework setup. This epic ensures every pull request is automatically validated through backend tests, frontend tests, linting, and type checking before merge.

The implementation creates a comprehensive CI pipeline that runs pytest for backend, Vitest with React Testing Library for frontend, ESLint for code quality, and TypeScript for type safety. Test coverage reporting provides visibility into code quality metrics.

**PRD Reference:** docs/PRD-phase5.md (FR20-FR26, NFR5, NFR11, NFR14, NFR19-NFR20)

## Objectives and Scope

**In Scope:**
- GitHub Actions workflow file (.github/workflows/ci.yml)
- Backend pytest execution in CI with coverage
- Frontend Vitest + React Testing Library configuration
- Frontend test execution in CI
- ESLint and TypeScript checks in CI
- Test coverage reporting (Codecov or inline)
- FeedbackButtons component tests (TD-002 backlog item)
- Parallel job execution for speed

**Out of Scope:**
- Deployment pipelines (CD to production)
- E2E testing with Playwright/Cypress
- Visual regression testing
- Performance/load testing in CI
- Code coverage enforcement gates (future enhancement)

## System Architecture Alignment

**Architecture Reference:** docs/architecture/phase-5-additions.md

This epic aligns with the Phase 5 CI/CD Architecture section:
- **GitHub Actions Workflow** - Complete ci.yml configuration
- **Frontend Test Configuration** - vitest.config.ts and vitest.setup.ts
- **Parallel Jobs** - Backend and frontend run concurrently

**Key Files:**
- `.github/workflows/ci.yml` - Main workflow definition
- `frontend/vitest.config.ts` - Vitest configuration
- `frontend/vitest.setup.ts` - Test setup with jest-dom
- `frontend/__tests__/` - Test file location

## Detailed Design

### Services and Modules

| File/Module | Responsibility | Location |
|-------------|----------------|----------|
| `ci.yml` | GitHub Actions workflow definition | .github/workflows/ |
| `vitest.config.ts` | Vitest test runner configuration | frontend/ |
| `vitest.setup.ts` | Test environment setup | frontend/ |
| `FeedbackButtons.test.tsx` | Component tests for FeedbackButtons | frontend/__tests__/components/events/ |

### Data Models and Contracts

**GitHub Actions Workflow Structure:**
```yaml
name: CI
on:
  push:
    branches: [main, development]
  pull_request:
    branches: [main, development]

jobs:
  backend-tests:
    # Python 3.11, pytest with coverage
  frontend-tests:
    # Node 20, vitest, eslint, tsc
```

**Vitest Configuration:**
```typescript
// vitest.config.ts
{
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    include: ['**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'lcov']
    }
  }
}
```

### APIs and Interfaces

N/A - This epic is infrastructure-focused, not API-focused.

### Workflows and Sequencing

**CI Pipeline Execution Flow:**
```
PR Created/Updated
    │
    ├─────────────────────────────────────┐
    │                                     │
    ▼                                     ▼
┌─────────────────────┐     ┌─────────────────────┐
│   backend-tests     │     │   frontend-tests    │
│   (parallel)        │     │   (parallel)        │
├─────────────────────┤     ├─────────────────────┤
│ 1. Checkout code    │     │ 1. Checkout code    │
│ 2. Setup Python 3.11│     │ 2. Setup Node 20    │
│ 3. Cache pip deps   │     │ 3. Cache npm deps   │
│ 4. Install deps     │     │ 4. npm ci           │
│ 5. Run ruff lint    │     │ 5. npm run lint     │
│ 6. Run pytest       │     │ 6. npx tsc --noEmit │
│ 7. Upload coverage  │     │ 7. npm run test     │
└─────────────────────┘     │ 8. Upload coverage  │
                            └─────────────────────┘
    │                                     │
    └─────────────────────────────────────┘
                      │
                      ▼
              PR Check Status
              (Pass/Fail)
```

**Test Execution Sequence (Frontend):**
```
1. Vitest loads vitest.config.ts
2. Setup file (vitest.setup.ts) runs:
   - Import jest-dom matchers
   - Configure cleanup after each test
3. Test files discovered (*.test.tsx)
4. Each test file:
   a. Import component under test
   b. Render with @testing-library/react
   c. Query DOM elements
   d. Assert expectations
5. Coverage collected (v8 provider)
6. Results output to console and coverage files
```

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Total CI time | <10 minutes | Time from trigger to completion |
| Backend tests | <5 minutes | pytest execution time |
| Frontend tests | <3 minutes | vitest execution time |
| Lint/type check | <2 minutes | eslint + tsc time |

### Security

- **Secrets management** - API keys stored in GitHub Secrets (NFR11)
- **No credentials in code** - TEST_ENCRYPTION_KEY from secrets
- **Minimal permissions** - Workflow uses default GITHUB_TOKEN

### Reliability/Availability

- **Retry logic** - Actions automatically retry on runner failures (NFR14)
- **Dependency caching** - pip and npm caches reduce flaky installs
- **Timeout limits** - Job timeouts prevent hung workflows

### Observability

- **CI status badges** - Can add to README
- **Coverage reports** - Uploaded to Codecov or displayed inline
- **Test output** - Full test results in Actions logs

## Dependencies and Integrations

### GitHub Actions Dependencies

| Action | Version | Purpose |
|--------|---------|---------|
| actions/checkout | v4 | Clone repository |
| actions/setup-python | v5 | Install Python with caching |
| actions/setup-node | v4 | Install Node.js with caching |
| codecov/codecov-action | v4 | Upload coverage reports |

### Frontend Dev Dependencies (package.json additions)

| Package | Version | Purpose |
|---------|---------|---------|
| vitest | ^2.0.0 | Test runner |
| @vitest/coverage-v8 | ^2.0.0 | Coverage provider |
| @testing-library/react | ^16.0.0 | React component testing |
| @testing-library/jest-dom | ^6.0.0 | DOM matchers |
| @testing-library/user-event | ^14.0.0 | User interaction simulation |
| jsdom | ^24.0.0 | Browser environment |

### Backend Dev Dependencies (requirements-dev.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| pytest-cov | >=4.0.0 | Coverage for pytest |
| ruff | >=0.1.0 | Fast Python linter |

## Acceptance Criteria (Authoritative)

**Story P5-3.1: Create GitHub Actions Workflow for PRs**
1. Workflow file exists at .github/workflows/ci.yml
2. Triggers on push to main and development branches
3. Triggers on pull requests to main and development branches
4. Runs backend-tests and frontend-tests jobs in parallel
5. PR is blocked from merge if any check fails

**Story P5-3.2: Add Backend Pytest Execution to CI**
1. pytest runs in ubuntu-latest runner
2. Python 3.11 used (matching local development)
3. Dependencies installed from requirements.txt
4. Test database uses SQLite (DATABASE_URL env var)
5. ENCRYPTION_KEY set from GitHub Secrets
6. pytest exits with non-zero on test failure
7. Coverage report generated (--cov flag)

**Story P5-3.3: Set up Vitest + React Testing Library**
1. vitest.config.ts created in frontend directory
2. vitest.setup.ts imports jest-dom matchers
3. jsdom environment configured for browser simulation
4. Path alias '@' resolves correctly in tests
5. `npm run test` script added to package.json
6. Sample test runs successfully locally

**Story P5-3.4: Add Frontend Test Execution to CI**
1. npm run test executes vitest in CI
2. Tests run in jsdom environment (headless)
3. Job fails if any test fails
4. Test output visible in GitHub Actions logs

**Story P5-3.5: Add ESLint and TypeScript Checks to CI**
1. npm run lint executes ESLint
2. npx tsc --noEmit runs type checking
3. Lint errors fail the job
4. Type errors fail the job
5. Error messages visible in CI output

**Story P5-3.6: Configure Test Coverage Reporting**
1. Backend coverage generated with pytest-cov (XML format)
2. Frontend coverage generated with @vitest/coverage-v8 (lcov format)
3. Coverage uploaded to Codecov (or displayed in CI output)
4. Coverage percentages visible in PR or CI logs

**Story P5-3.7: Write FeedbackButtons Component Tests**
1. Test file created at frontend/__tests__/components/events/FeedbackButtons.test.tsx
2. Tests for thumbs up button click handler
3. Tests for thumbs down button click handler
4. Tests for loading state (disabled during submission)
5. Tests for already-submitted state
6. Tests for ARIA labels on buttons
7. All tests pass in local and CI environments

## Traceability Mapping

| AC | Spec Section | Component/API | Test Idea |
|----|--------------|---------------|-----------|
| P5-3.1-1 | Workflows | ci.yml | File existence check |
| P5-3.1-2 | Workflows | ci.yml | Push trigger test |
| P5-3.1-3 | Workflows | ci.yml | PR trigger test |
| P5-3.1-4 | Workflows | ci.yml | Parallel jobs check |
| P5-3.1-5 | Integration | GitHub | Branch protection test |
| P5-3.2-1 | Workflows | backend-tests job | Runner config check |
| P5-3.2-2 | Workflows | setup-python | Python version check |
| P5-3.2-3 | Workflows | pip install | Dependency install test |
| P5-3.2-4 | Workflows | pytest env | DATABASE_URL test |
| P5-3.2-5 | Security | GitHub Secrets | ENCRYPTION_KEY test |
| P5-3.2-6 | Workflows | pytest | Exit code test |
| P5-3.2-7 | Workflows | pytest-cov | Coverage file test |
| P5-3.3-1 | Data Models | vitest.config.ts | Config file test |
| P5-3.3-2 | Data Models | vitest.setup.ts | Setup file test |
| P5-3.3-3 | Data Models | vitest.config.ts | Environment check |
| P5-3.3-4 | Data Models | vitest.config.ts | Alias resolution test |
| P5-3.3-5 | Dependencies | package.json | Script exists test |
| P5-3.3-6 | Integration | vitest | Local run test |
| P5-3.4-1 | Workflows | frontend-tests job | npm test execution |
| P5-3.4-2 | Data Models | vitest.config.ts | jsdom env test |
| P5-3.4-3 | Workflows | vitest | Exit code test |
| P5-3.4-4 | Observability | CI logs | Output visibility test |
| P5-3.5-1 | Workflows | frontend-tests job | Lint execution test |
| P5-3.5-2 | Workflows | frontend-tests job | tsc execution test |
| P5-3.5-3 | Workflows | eslint | Error exit code test |
| P5-3.5-4 | Workflows | tsc | Error exit code test |
| P5-3.5-5 | Observability | CI logs | Error message test |
| P5-3.6-1 | Workflows | pytest-cov | XML coverage test |
| P5-3.6-2 | Data Models | vitest.config.ts | lcov coverage test |
| P5-3.6-3 | Workflows | codecov-action | Upload test |
| P5-3.6-4 | Observability | CI output | Percentage display test |
| P5-3.7-1 | Integration | Test file | File exists test |
| P5-3.7-2 | Integration | FeedbackButtons | Thumbs up test |
| P5-3.7-3 | Integration | FeedbackButtons | Thumbs down test |
| P5-3.7-4 | Integration | FeedbackButtons | Loading state test |
| P5-3.7-5 | Integration | FeedbackButtons | Submitted state test |
| P5-3.7-6 | Integration | FeedbackButtons | ARIA label test |
| P5-3.7-7 | Integration | vitest | All tests pass |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1: Flaky tests** - Network-dependent tests may fail intermittently; use mocks
- **R2: CI minutes usage** - Parallel jobs use more minutes; monitor usage
- **R3: Dependency conflicts** - New test deps may conflict with existing; test locally first

**Assumptions:**
- **A1:** GitHub Actions available on repository (not enterprise-restricted)
- **A2:** Codecov integration approved (or use inline coverage display)
- **A3:** Existing eslint config is valid and tests pass
- **A4:** Backend tests currently pass (no new failures introduced)

**Open Questions:**
- **Q1:** Should we enforce coverage thresholds? → Defer, start with reporting only
- **Q2:** Use Codecov or GitHub's built-in coverage? → Start with Codecov, well-established
- **Q3:** Add workflow status badge to README? → Yes, add in P5-5.5 story

## Test Strategy Summary

**Unit Tests:**
- FeedbackButtons.test.tsx - Component rendering, interactions, states
- Additional component tests as needed (growth)

**Integration Tests:**
- CI workflow syntax validation (GitHub validates on push)
- Local test execution verification

**Manual Tests (Required):**
- Create test PR to verify full CI pipeline
- Verify branch protection rules work
- Check coverage report accessibility

**Test Environment:**
- GitHub Actions ubuntu-latest runner
- Python 3.11, Node 20
- SQLite test database
- Mock API calls in frontend tests
