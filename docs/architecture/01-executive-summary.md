# Executive Summary

[← Back to Architecture Index](./README.md)

---

## Architectural Overview

The ArgusAI uses an **event-driven architecture** that processes camera feeds through motion detection, generates natural language descriptions via AI models, and delivers real-time notifications to a web dashboard. The system prioritizes simplicity and privacy by storing semantic descriptions rather than video footage, making it suitable for security, accessibility, and home automation use cases.

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│                    (Web Browser)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS / WebSocket
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    FRONTEND (Next.js 15)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Dashboard   │  │   Camera     │  │  Alert Rule  │         │
│  │   (Events)   │  │  Management  │  │  Management  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  React Server Components + Client Components                    │
│  Tailwind CSS + shadcn/ui Components                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ REST API + WebSocket
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  API Routes  │  │   Services   │  │   Models     │         │
│  │  (REST/WS)   │  │   (Logic)    │  │ (Database)   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                 │
│                            │                                     │
│  ┌─────────────────────────▼──────────────────────────┐        │
│  │           Event Processing Pipeline                 │        │
│  │                                                      │        │
│  │  Motion Detection → Frame Capture → AI Analysis    │        │
│  │       → Event Storage → Alert Evaluation           │        │
│  │           → Webhook Dispatch → WS Broadcast        │        │
│  └──────────────────────────────────────────────────┬─┘        │
└──────────────────────┬──────────────────────────────┼──────────┘
                       │                               │
        ┌──────────────▼─────────────┐    ┌───────────▼──────────┐
        │  Camera (RTSP/USB)         │    │  SQLite Database     │
        │  - OpenCV Capture          │    │  - Events            │
        │  - Motion Detection        │    │  - Cameras           │
        └────────────────────────────┘    │  - Alert Rules       │
                                          │  - Settings          │
                       │                  └──────────────────────┘
        ┌──────────────▼─────────────┐              │
        │  AI Services (Multi)       │    ┌─────────▼────────────┐
        │  - OpenAI GPT-4o-mini     │    │  Webhooks (External) │
        │  - Google Gemini Flash    │    │  - Home Assistant    │
        │  - Anthropic Claude       │    │  - IFTTT, Zapier     │
        └────────────────────────────┘    └──────────────────────┘
```

---

## Key Architectural Principles

### 1. Description-First Storage
**Store semantic event descriptions, NOT video footage**

- **Privacy:** Descriptions less sensitive than video, easier GDPR compliance
- **Storage:** 1 event = ~50KB vs 1 minute video = 10MB (200x smaller)
- **Searchability:** Natural language searchable, video is not
- **Accessibility:** Descriptions readable by screen readers

### 2. Event-Driven Processing
**Motion detection triggers AI analysis (not continuous)**

- **Cost:** Reduces AI API calls by 95%+ vs continuous analysis
- **Performance:** System can handle 2+ events/day per camera efficiently
- **Privacy:** Only analyze when motion detected, not 24/7 recording
- **Scalability:** Async processing handles burst events without blocking

### 3. Real-Time User Experience
**WebSocket pushes updates to dashboard instantly**

- **Responsiveness:** Events appear in UI within 2 seconds of detection
- **Engagement:** Live feed keeps users connected to their space
- **No Polling:** Efficient communication, lower server load
- **Graceful Degradation:** Falls back to REST API if WebSocket fails

### 4. Multi-Provider AI Resilience
**Support 3 AI providers with automatic fallback**

- **Reliability:** One provider down doesn't break system (3-tier fallback)
- **Cost Optimization:** Switch to cheapest/free provider dynamically
- **Quality Options:** A/B test which gives best descriptions
- **User Choice:** Users select provider based on preference/ethics

### 5. Zero-Configuration Database
**SQLite file-based database requires no setup**

- **Simplicity:** Single file, no database server to install/configure
- **Portability:** Copy file = full backup, easy to distribute
- **Performance:** Sufficient for 10,000+ events (tested)
- **Migration Path:** SQLAlchemy makes PostgreSQL upgrade easy in Phase 2

### 6. Scale-Ready Foundation
**Single camera MVP designed for multi-camera Phase 2**

- **Modular Services:** Camera service supports multiple instances
- **Database Schema:** Foreign keys ready for multi-camera relationships
- **Event Queue:** Architecture supports distributed processing
- **API Design:** Endpoints accept camera_id parameter for future use

---

## Core Data Flow

### Primary Event Flow (Motion → Description → Alert)

```
1. CAMERA CAPTURE
   └─> OpenCV VideoCapture running in background thread
       └─> Captures frames at 5 FPS (configurable)

2. MOTION DETECTION
   └─> Background subtraction algorithm (MOG2)
       └─> Compares current frame to background model
           └─> Motion detected? → Trigger event processing
           └─> No motion? → Continue monitoring

3. EVENT PROCESSING (Async Pipeline)
   ├─> Capture optimal frame (motion peak, not first/last)
   ├─> Pre-process image (resize, compress, optimize for AI)
   ├─> Call AI service with prompt
   │   ├─> Try OpenAI GPT-4o-mini (primary)
   │   ├─> Fallback to Google Gemini Flash if fails
   │   └─> Fallback to Anthropic Claude if both fail
   ├─> Parse AI response (description + confidence)
   ├─> Extract objects detected (person, vehicle, package, etc.)
   ├─> Generate thumbnail (640x480 JPEG, <200KB)
   └─> Store event in database

4. ALERT EVALUATION
   └─> Load all active alert rules
       └─> For each rule:
           ├─> Check cooldown (skip if in cooldown period)
           ├─> Evaluate conditions (object types, time, camera, etc.)
           └─> If matched:
               ├─> Execute actions (dashboard notification, webhook)
               ├─> Update cooldown timestamp
               └─> Increment trigger count

5. NOTIFICATION DISPATCH
   ├─> WebSocket: Broadcast event to all connected clients
   ├─> Webhook: HTTP POST to configured URLs (retry 3x)
   └─> Dashboard: Show notification bell badge

6. DASHBOARD UPDATE
   └─> Frontend receives WebSocket message
       ├─> Add event to timeline
       ├─> Update notification count
       ├─> Play sound (if enabled)
       └─> Show toast notification
```

### Manual Analysis Flow (User-Triggered)

```
1. USER CLICKS "Analyze Now" Button
   └─> API call: POST /api/v1/cameras/{id}/analyze

2. CAPTURE CURRENT FRAME
   └─> Get latest frame from camera capture thread
       └─> No motion detection required

3. PROCESS SAME AS MOTION-TRIGGERED
   └─> AI analysis → Store event → Evaluate alerts → Notify

4. RETURN EVENT TO USER
   └─> Response includes event_id and description
       └─> Frontend navigates to event detail or shows in timeline
```

---

## Technology Stack Summary

### Frontend Stack
- **Framework:** Next.js 15.x (App Router with React Server Components)
- **Language:** TypeScript 5.x (strict mode)
- **Styling:** Tailwind CSS 3.x + shadcn/ui component library
- **State Management:** React Context (no Redux needed for MVP)
- **Real-Time:** Native WebSocket API
- **Icons:** lucide-react
- **Date/Time:** date-fns

### Backend Stack
- **Framework:** FastAPI 0.115+ (ASGI async framework)
- **Language:** Python 3.11+ (async/await support)
- **Server:** Uvicorn (included with FastAPI)
- **Database:** SQLite 3.x + SQLAlchemy 2.0+ (async ORM)
- **Migrations:** Alembic
- **Computer Vision:** opencv-python 4.8+
- **AI SDKs:** openai, google-generativeai, anthropic
- **Auth:** python-jose (JWT) + passlib (bcrypt)
- **Encryption:** cryptography (Fernet for API keys)

### Integration Stack
- **API Protocol:** REST (JSON) + WebSocket
- **Camera Protocol:** RTSP (IP cameras) + DirectShow/V4L2 (USB)
- **Webhook Protocol:** HTTPS POST with retry logic
- **Authentication:** JWT tokens in HTTP-only cookies

---

## Deployment Model

### MVP Deployment (Development)
```
localhost:3000  → Next.js frontend (npm run dev)
localhost:8000  → FastAPI backend (uvicorn main:app --reload)
```

### Production Deployment (Docker)
```
Docker Compose with 2 containers:
├─> frontend:3000  (Next.js production build)
└─> backend:8000   (FastAPI with Uvicorn)
    ├─> data/app.db        (SQLite database - volume mount)
    ├─> data/thumbnails/   (Event images - volume mount)
    └─> /dev/video0        (USB camera - device mount)
```

**Benefits:**
- Single `docker-compose up` command starts everything
- Persistent data via volume mounts
- Easy to distribute to beta testers
- Scales to multi-camera by running multiple backend containers

---

## Security Overview

### Authentication (Phase 1.5)
- JWT tokens stored in HTTP-only cookies (XSS protection)
- bcrypt password hashing (slow by design)
- Token expiration: 24 hours
- Refresh token support (optional)

### Data Security
- AI API keys encrypted with Fernet (symmetric encryption)
- RTSP passwords encrypted in database
- No plain text secrets in logs
- Input validation on all API endpoints (Pydantic schemas)

### Network Security
- CORS configured for frontend origin only
- HTTPS in production (TLS 1.2+)
- WebSocket over WSS (secure WebSocket)
- Rate limiting on sensitive endpoints

---

## Performance Targets

### Response Time Targets
- **Dashboard page load:** <2 seconds
- **Event API query:** <500ms (p95)
- **Motion → Description:** <5 seconds (p95)
- **WebSocket message delivery:** <100ms

### Throughput Targets
- **Events per day:** 50+ per camera
- **Concurrent WebSocket connections:** 10+ clients
- **Database size:** <100MB for 10,000 events
- **AI API calls:** <1000 per month (free tier)

### Resource Limits
- **CPU:** <20% average (single core)
- **Memory:** <512MB backend, <256MB frontend
- **Disk I/O:** Minimal (SQLite + thumbnail writes)
- **Network:** <10 Mbps for RTSP stream

---

## Scalability Path

### MVP (Phase 1) - Current
- **Cameras:** 1 camera
- **Users:** 1 user (Phase 1.5: multi-user)
- **Events:** 10,000+ supported
- **Database:** SQLite
- **Processing:** Single FastAPI instance

### Phase 2 - Multi-Camera
- **Cameras:** 4-8 cameras per user
- **Users:** Multiple users with separate accounts
- **Events:** 100,000+ events
- **Database:** PostgreSQL (better concurrency)
- **Processing:** Celery + Redis queue

### Phase 3 - Enterprise
- **Cameras:** Unlimited per organization
- **Users:** Teams with role-based access
- **Events:** Millions of events with archiving
- **Database:** PostgreSQL with partitioning
- **Processing:** Kubernetes cluster, horizontal scaling

---

## Risk Mitigation

### Technical Risks
| Risk | Mitigation | Status |
|------|------------|--------|
| AI provider outage | Multi-provider fallback (3 tiers) | ✅ Addressed |
| Camera disconnection | Auto-reconnect with exponential backoff | ✅ Addressed |
| Database corruption | Automatic backups, transaction safety | ✅ Addressed |
| Memory leaks | Proper cleanup, monitoring, restarts | ✅ Addressed |

### Business Risks
| Risk | Mitigation | Status |
|------|------------|--------|
| High AI costs | Free-tier providers, motion-triggered only | ✅ Addressed |
| Privacy concerns | No video storage, description-only | ✅ Addressed |
| User adoption | <10 min setup time, intuitive UI | ✅ Addressed |
| Competitive pressure | Unique value prop (descriptions > video) | ✅ Addressed |

---

## Success Metrics

### Technical Metrics
- ✅ 95%+ system uptime
- ✅ <5 second event processing latency
- ✅ 90%+ AI description success rate
- ✅ <20% motion detection false positive rate

### User Metrics
- ✅ 85%+ description usefulness rating
- ✅ <10 minute setup time
- ✅ 70%+ user retention at 30 days
- ✅ 2+ events per day per user

### Business Metrics
- ✅ 3+ validated use cases
- ✅ <$50 total AI costs during beta
- ✅ 10+ successful beta deployments
- ✅ 40+ NPS score

---

[Next: Project Initialization →](./02-project-initialization.md) | [Back to Index](./README.md)
