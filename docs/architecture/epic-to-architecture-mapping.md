# Epic to Architecture Mapping

| Epic/Feature | Architecture Components | Key Files |
|--------------|------------------------|-----------|
| **F1: Camera Integration** | Camera service, RTSP capture, USB support | `camera_service.py`, `cameras.py` API, `CameraForm.tsx` |
| **F2: Motion Detection** | OpenCV background subtraction, zone filtering | `motion_detection.py`, `event_processor.py` |
| **F3: AI Descriptions** | Multi-provider AI service, fallback logic | `ai_service.py`, OpenAI/Gemini/Claude SDKs |
| **F4: Event Storage** | SQLAlchemy models, event API, database migrations | `event.py` model, `events.py` API, Alembic migrations |
| **F5: Alert Rules** | Rule engine, condition evaluation, cooldown | `alert_service.py`, `alert_rules.py` API, `AlertRuleForm.tsx` |
| **F6: Dashboard UI** | Next.js pages, React components, WebSocket updates | `app/events/page.tsx`, `EventTimeline.tsx`, WebSocket context |
| **F7: Authentication** | JWT tokens, password hashing, session management | `security.py`, `auth.py` API, `AuthContext.tsx` |
| **F8: System Admin** | Settings API, logging, health check | `settings.py` API, `logging.py`, `health.py` |
| **F9: Webhooks** | HTTP POST with retry, webhook dispatch service | `webhook_service.py`, alert rule webhook actions |

---
