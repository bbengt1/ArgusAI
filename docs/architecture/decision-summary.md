# Decision Summary

| Category | Decision | Version/Details | Affects | Rationale |
|----------|----------|----------------|---------|-----------|
| **Frontend Framework** | Next.js | 15.x with App Router | All UI features | React Server Components, built-in optimization, excellent DX |
| **Frontend Language** | TypeScript | 5.x | All frontend code | Type safety, better tooling, catches errors early |
| **Frontend Styling** | Tailwind CSS + shadcn/ui | 3.x / latest | All UI components | Rapid development, mobile-responsive, professional components |
| **Backend Framework** | FastAPI | 0.115+ | All API endpoints | Async support, automatic docs, WebSocket support, excellent performance |
| **Backend Language** | Python | 3.11+ | All backend code | Ecosystem for CV/AI, async/await support, team familiarity |
| **Database** | SQLite | 3.x | Event storage, settings | Zero-config, sufficient for MVP scale, easy backup |
| **ORM** | SQLAlchemy | 2.0+ with async | Database access | Type-safe queries, migrations support, async operations |
| **Camera Library** | OpenCV | 4.8+ | Camera capture, motion | Industry standard, RTSP support, cross-platform |
| **Motion Detection** | OpenCV MOG2 | Built-in | F2 (Motion Detection) | Background subtraction, adaptive, proven algorithm |
| **AI Primary** | OpenAI GPT-4o-mini | Latest API | F3 (AI Descriptions) | Best cost/performance, reliable API, good descriptions |
| **AI Fallback** | Google Gemini Flash | Latest API | F3 (AI Descriptions) | Free tier available, good quality, automatic fallback |
| **AI Tertiary** | Anthropic Claude Haiku | Latest API | F3 (AI Descriptions) | Additional fallback option, excellent quality |
| **Authentication** | JWT + HTTP-only cookies | python-jose | F7 (Auth) | Stateless, secure, XSS protection |
| **Password Hashing** | bcrypt | via passlib | F7 (Auth) | Industry standard, secure, slow by design |
| **API Key Encryption** | Fernet (symmetric) | cryptography lib | F7.2 | Secure storage of AI API keys |
| **WebSocket** | FastAPI/Starlette | Built-in | F6.6 (Real-time) | Native support, no additional services needed |
| **Background Tasks** | FastAPI BackgroundTasks | Built-in | F3 (AI processing) | Simple async tasks, no external queue needed for MVP |
| **State Management** | React Context | Built-in | Frontend global state | Sufficient for MVP, no Redux complexity |
| **Icons** | lucide-react | Latest | All UI icons | Consistent, lightweight, good selection |
| **Date Formatting** | date-fns | Latest | All date displays | Lightweight, immutable, locale support |

---
