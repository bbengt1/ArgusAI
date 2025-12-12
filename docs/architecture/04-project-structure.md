# Project Structure

[← Back to Architecture Index](./README.md) | [← Previous: Technology Stack](./03-technology-stack.md) | [Next: Epic Mapping →](./05-epic-mapping.md)

---

## Complete Project Structure

```
argusai/
├── backend/
│   ├── main.py                          # FastAPI app entry point, server startup
│   ├── requirements.txt                 # Python dependencies with pinned versions
│   ├── .env.example                     # Environment variables template
│   ├── .env                             # Actual env vars (gitignored)
│   ├── alembic.ini                      # Alembic configuration
│   ├── alembic/                         # Database migrations
│   │   ├── versions/                    # Migration version scripts
│   │   │   └── 001_initial_schema.py
│   │   └── env.py                       # Alembic environment config
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/                         # API route handlers
│   │   │   ├── __init__.py
│   │   │   └── v1/                      # API version 1
│   │   │       ├── __init__.py
│   │   │       ├── cameras.py          # GET/POST/PUT/DELETE /api/v1/cameras
│   │   │       ├── events.py           # GET /api/v1/events, GET /api/v1/events/{id}
│   │   │       ├── alert_rules.py      # CRUD for /api/v1/alert-rules
│   │   │       ├── settings.py         # GET/PUT /api/v1/settings
│   │   │       ├── health.py           # GET /api/health (no auth)
│   │   │       ├── auth.py             # POST /api/v1/login, /logout (Phase 1.5)
│   │   │       └── websocket.py        # WebSocket endpoint /ws
│   │   ├── core/                        # Core system modules
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Pydantic Settings for env vars
│   │   │   ├── security.py             # JWT auth, password hashing, API key encryption
│   │   │   ├── database.py             # SQLAlchemy engine, session management
│   │   │   └── logging.py              # Structured logging configuration
│   │   ├── models/                      # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── camera.py               # Camera model (id, name, rtsp_url, etc.)
│   │   │   ├── event.py                # Event model (id, timestamp, description, etc.)
│   │   │   ├── alert_rule.py           # AlertRule model (conditions, actions)
│   │   │   ├── user.py                 # User model (Phase 1.5)
│   │   │   └── system_setting.py       # SystemSetting model (key-value config)
│   │   ├── schemas/                     # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── camera.py               # CameraCreate, CameraUpdate, CameraResponse
│   │   │   ├── event.py                # EventResponse, EventList, EventFilters
│   │   │   ├── alert_rule.py           # AlertRuleCreate, AlertRuleUpdate
│   │   │   └── user.py                 # UserLogin, UserResponse (Phase 1.5)
│   │   ├── services/                    # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── camera_service.py       # Camera capture thread, RTSP handling, reconnect logic
│   │   │   ├── motion_detection.py     # OpenCV background subtraction, zone filtering
│   │   │   ├── ai_service.py           # Multi-provider AI calls (OpenAI, Gemini, Claude)
│   │   │   ├── event_processor.py      # Event pipeline: capture→AI→store→alert
│   │   │   ├── alert_service.py        # Evaluate rules, trigger actions, cooldown tracking
│   │   │   ├── webhook_service.py      # HTTP POST with retry, timeout handling
│   │   │   └── websocket_manager.py    # WebSocket connection pool, broadcast messages
│   │   └── utils/                       # Utility modules
│   │       ├── __init__.py
│   │       ├── image_processing.py     # Resize, compress, thumbnail generation
│   │       ├── encryption.py           # Fernet encrypt/decrypt for API keys
│   │       └── validators.py           # Custom Pydantic validators
│   ├── tests/                           # Pytest test suite
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Pytest fixtures
│   │   ├── test_api/                   # API endpoint tests
│   │   │   ├── test_cameras.py
│   │   │   ├── test_events.py
│   │   │   └── test_alert_rules.py
│   │   └── test_services/              # Service layer tests
│   │       ├── test_motion_detection.py
│   │       ├── test_ai_service.py
│   │       └── test_event_processor.py
│   └── data/                            # Runtime data directory (gitignored)
│       ├── app.db                       # SQLite database file
│       ├── thumbnails/                  # Event thumbnail images
│       │   └── {event_id}.jpg
│       └── logs/                        # Application log files
│           ├── app.log
│           └── error.log
├── frontend/
│   ├── package.json                     # npm dependencies
│   ├── next.config.js                   # Next.js configuration
│   ├── tailwind.config.js               # Tailwind CSS configuration
│   ├── tsconfig.json                    # TypeScript configuration
│   ├── .env.local.example               # Frontend env vars template
│   ├── .env.local                       # Actual env vars (gitignored)
│   ├── components.json                  # shadcn/ui configuration
│   ├── public/                          # Static assets
│   │   ├── favicon.ico
│   │   ├── icons/                       # App icons
│   │   └── images/                      # Static images
│   ├── app/                             # Next.js App Router pages
│   │   ├── layout.tsx                  # Root layout (nav, auth provider)
│   │   ├── page.tsx                    # Dashboard home (redirect to /events)
│   │   ├── globals.css                 # Global styles, Tailwind directives
│   │   ├── events/                     # Event management
│   │   │   ├── page.tsx                # Event timeline (main dashboard)
│   │   │   └── [id]/
│   │   │       └── page.tsx            # Event detail modal/page
│   │   ├── cameras/                    # Camera management
│   │   │   ├── page.tsx                # Camera grid view
│   │   │   ├── new/
│   │   │   │   └── page.tsx            # Add camera form
│   │   │   └── [id]/
│   │   │       ├── page.tsx            # Camera detail/edit
│   │   │       └── live/
│   │   │           └── page.tsx        # Full-screen camera view
│   │   ├── alert-rules/                # Alert rule management
│   │   │   ├── page.tsx                # Rules list
│   │   │   ├── new/
│   │   │   │   └── page.tsx            # Create rule form
│   │   │   └── [id]/
│   │   │       └── page.tsx            # Edit rule form
│   │   ├── settings/                   # System settings
│   │   │   └── page.tsx                # Settings tabs (general, AI, detection)
│   │   ├── login/                      # Authentication (Phase 1.5)
│   │   │   └── page.tsx                # Login form
│   │   └── api/                        # Next.js API routes (optional proxy)
│   │       └── [...path]/
│   │           └── route.ts            # Catch-all proxy to backend
│   ├── components/                      # React components
│   │   ├── ui/                         # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── form.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── select.tsx
│   │   │   ├── table.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...                     # Other shadcn components as needed
│   │   ├── layout/
│   │   │   ├── Header.tsx              # Top navigation bar
│   │   │   ├── Sidebar.tsx             # Side navigation (optional)
│   │   │   └── Footer.tsx              # Footer (optional)
│   │   ├── events/
│   │   │   ├── EventCard.tsx           # Single event card in timeline
│   │   │   ├── EventTimeline.tsx       # Scrollable event list
│   │   │   ├── EventDetail.tsx         # Expanded event view
│   │   │   ├── EventFilters.tsx        # Filter controls (date, camera, type)
│   │   │   └── EventSearch.tsx         # Search bar component
│   │   ├── cameras/
│   │   │   ├── CameraGrid.tsx          # Grid of camera previews
│   │   │   ├── CameraPreview.tsx       # Single camera preview tile
│   │   │   ├── CameraForm.tsx          # Add/edit camera form
│   │   │   ├── CameraStatus.tsx        # Connection status indicator
│   │   │   └── AnalyzeNowButton.tsx    # Manual analysis trigger
│   │   ├── alerts/
│   │   │   ├── AlertRuleCard.tsx       # Single rule display
│   │   │   ├── AlertRuleForm.tsx       # Rule creation/edit form
│   │   │   ├── AlertRuleTest.tsx       # Test rule against past events
│   │   │   └── ConditionBuilder.tsx    # Visual condition builder
│   │   └── common/
│   │       ├── Loading.tsx             # Loading spinner
│   │       ├── ErrorBoundary.tsx       # Error handling wrapper
│   │       ├── NotificationBell.tsx    # WebSocket notification indicator
│   │       ├── ConfirmDialog.tsx       # Confirmation modal
│   │       └── EmptyState.tsx          # No data placeholder
│   ├── lib/                             # Frontend utilities
│   │   ├── api-client.ts               # Typed API client wrapper
│   │   ├── websocket.ts                # WebSocket client class
│   │   ├── utils.ts                    # Helper functions (cn, formatDate, etc.)
│   │   └── constants.ts                # Frontend constants (API URL, etc.)
│   ├── hooks/                           # Custom React hooks
│   │   ├── useEvents.ts                # Fetch/filter events
│   │   ├── useCameras.ts               # Camera CRUD operations
│   │   ├── useAlertRules.ts            # Alert rule CRUD
│   │   ├── useWebSocket.ts             # WebSocket connection hook
│   │   ├── useAuth.ts                  # Auth state (Phase 1.5)
│   │   └── useToast.ts                 # Toast notifications
│   ├── types/                           # TypeScript type definitions
│   │   ├── event.ts                    # Event, EventFilters types
│   │   ├── camera.ts                   # Camera, CameraConfig types
│   │   ├── alert-rule.ts               # AlertRule, RuleCondition types
│   │   └── user.ts                     # User, AuthState types
│   └── context/                         # React Context providers
│       ├── AuthContext.tsx             # Authentication state
│       └── WebSocketContext.tsx        # WebSocket connection state
├── docker-compose.yml                   # Docker orchestration (optional)
├── Dockerfile.backend                   # Backend container
├── Dockerfile.frontend                  # Frontend container
├── .gitignore                           # Git ignore patterns
├── README.md                            # Project documentation
└── docs/                                # Documentation directory
    ├── architecture.md                  # This document!
    ├── prd/                            # Product requirements
    │   ├── README.md
    │   ├── 01-overview-goals.md
    │   ├── 02-personas-stories.md
    │   └── 03-functional-requirements.md
    └── api/                            # API documentation
        └── openapi.json                # OpenAPI spec (auto-generated)
```

---

---

[← Previous: Technology Stack](./03-technology-stack.md) | [Next: Epic Mapping →](./05-epic-mapping.md) | [Back to Index](./README.md)
