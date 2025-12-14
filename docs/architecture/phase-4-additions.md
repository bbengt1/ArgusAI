# Phase 4 Additions

This section documents the architectural additions for Phase 4, which adds intelligent context awareness, smart home integration, and mobile notifications.

## Phase 4 Executive Summary

Phase 4 transforms the system from reactive event detection to an **intelligent context-aware assistant**. Key capabilities:

- **Temporal Intelligence:** Recognize recurring visitors, detect patterns, enrich descriptions with history
- **Smart Home Integration:** Native Home Assistant support via MQTT, HomeKit accessories
- **Mobile Notifications:** Push notifications with thumbnails, PWA for native mobile experience
- **User Feedback Loop:** Learn from corrections to improve AI accuracy over time
- **Activity Summaries:** Daily digests and natural language activity reports

**Key Architectural Principles (Phase 4):**
1. **Privacy-First:** Face embeddings stored locally only, never sent to cloud
2. **Graceful Degradation:** Context engine failure doesn't block event processing
3. **Standard Protocols:** MQTT for smart home, Web Push for notifications
4. **Incremental Enhancement:** Each feature independently valuable

## Phase 4 Technology Stack Additions

```python
# Phase 4: Push Notifications
pywebpush>=2.0.0           # Web Push notifications with VAPID

# Phase 4: Smart Home Integration
paho-mqtt>=2.0.0           # MQTT client for Home Assistant
HAP-python>=4.9.0          # HomeKit Accessory Protocol (optional)

# Phase 4: Image Embeddings
sentence-transformers>=2.2.0  # For CLIP/SigLIP embeddings
# OR
openai-clip>=1.0.0         # OpenAI CLIP model

# Phase 4: Vector Search (if using PostgreSQL)
pgvector>=0.2.0            # Vector similarity search
```

## Phase 4 Project Structure Additions

```
backend/
├── app/
│   ├── services/
│   │   ├── context_service.py       # Temporal context engine
│   │   ├── embedding_service.py     # Image embedding generation
│   │   ├── similarity_service.py    # Vector similarity search
│   │   ├── push_notification_service.py  # Web Push
│   │   ├── mqtt_service.py          # MQTT publishing
│   │   ├── homekit_service.py       # HomeKit accessories
│   │   ├── digest_service.py        # Activity summaries
│   │   └── feedback_service.py      # User feedback collection
│   ├── models/
│   │   ├── event_embedding.py       # Vector embeddings
│   │   ├── recognized_entity.py     # Known people/vehicles
│   │   ├── push_subscription.py     # Push subscriptions
│   │   └── event_feedback.py        # User feedback
│   └── api/v1/
│       ├── context.py               # Context API endpoints
│       ├── push.py                  # Push notification endpoints
│       ├── summaries.py             # Digest endpoints
│       ├── feedback.py              # Feedback endpoints
│       └── integrations.py          # MQTT/HomeKit status

frontend/
├── app/
│   ├── manifest.json                # PWA manifest
│   └── service-worker.ts            # Push notification handler
├── components/
│   ├── notifications/
│   │   └── PushSettings.tsx         # Push preferences
│   ├── feedback/
│   │   └── FeedbackButtons.tsx      # Thumbs up/down
│   └── entities/
│       └── EntityList.tsx           # Recognized entities
└── public/
    └── icons/                       # PWA icons
```

## Phase 4 Database Schema Additions

```sql
-- Event embeddings for similarity search
CREATE TABLE event_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    embedding VECTOR(512),  -- CLIP embedding dimension
    model_version TEXT NOT NULL,  -- Track embedding model
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id)
);

CREATE INDEX idx_event_embeddings_vector ON event_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Recognized entities (people, vehicles)
CREATE TABLE recognized_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,  -- 'person', 'vehicle'
    name TEXT,  -- User-assigned name (nullable)
    reference_embedding VECTOR(512),
    first_seen_at TIMESTAMP NOT NULL,
    last_seen_at TIMESTAMP NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    metadata JSONB,  -- Additional attributes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entity-event associations
CREATE TABLE entity_events (
    entity_id UUID NOT NULL REFERENCES recognized_entities(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    similarity_score FLOAT NOT NULL,
    PRIMARY KEY (entity_id, event_id)
);

-- Push notification subscriptions
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);

-- Push notification preferences
CREATE TABLE push_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    camera_id UUID REFERENCES cameras(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT TRUE,
    object_types TEXT[],  -- Filter by object type
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    UNIQUE(user_id, camera_id)
);

-- User feedback on events
CREATE TABLE event_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    rating TEXT NOT NULL,  -- 'helpful', 'not_helpful'
    correction TEXT,  -- User-provided correction
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, user_id)
);

-- Activity digests
CREATE TABLE activity_digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_type TEXT NOT NULL,  -- 'daily', 'weekly'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    summary TEXT NOT NULL,  -- Generated summary
    event_count INTEGER NOT NULL,
    highlights JSONB,  -- Key events
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP
);

-- MQTT configuration
CREATE TABLE mqtt_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broker_host TEXT NOT NULL,
    broker_port INTEGER DEFAULT 1883,
    username TEXT,
    password TEXT,  -- Encrypted
    topic_prefix TEXT DEFAULT 'liveobject',
    discovery_enabled BOOLEAN DEFAULT TRUE,
    qos INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Phase 4 API Contracts

### Context API

**GET /api/v1/context/similar/{event_id}**
- Find events similar to the specified event
- Query params: `limit=10`, `min_similarity=0.7`, `days_back=30`
- Response:
```json
{
  "data": [
    {
      "event_id": "uuid",
      "similarity_score": 0.92,
      "timestamp": "2025-12-09T14:30:00Z",
      "description": "Similar event description"
    }
  ]
}
```

**GET /api/v1/context/patterns/{camera_id}**
- Get activity patterns for a camera
- Response:
```json
{
  "data": {
    "hourly_distribution": {"08": 5, "09": 12, ...},
    "daily_distribution": {"monday": 23, ...},
    "peak_hours": ["09:00", "17:00"],
    "average_events_per_day": 8.5
  }
}
```

**GET /api/v1/entities**
- List recognized entities
- Query params: `type=person|vehicle`, `named_only=true`

**PUT /api/v1/entities/{id}**
- Update entity (assign name)
- Body: `{ "name": "Mail Carrier" }`

### Push Notification API

**POST /api/v1/push/subscribe**
- Register push subscription
- Body:
```json
{
  "endpoint": "https://fcm.googleapis.com/...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}
```

**DELETE /api/v1/push/subscribe**
- Unsubscribe from push

**GET /api/v1/push/preferences**
- Get notification preferences

**PUT /api/v1/push/preferences**
- Update preferences
- Body:
```json
{
  "enabled": true,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "07:00",
  "cameras": {
    "uuid1": {"enabled": true, "object_types": ["person"]},
    "uuid2": {"enabled": false}
  }
}
```

### Summaries API

**GET /api/v1/summaries/daily**
- Query params: `date=2025-12-10`

**GET /api/v1/summaries/weekly**
- Query params: `week=2025-W50`

**POST /api/v1/summaries/generate**
- Trigger on-demand summary
- Body: `{ "start": "2025-12-10T00:00:00Z", "end": "2025-12-10T23:59:59Z" }`

### Feedback API

**POST /api/v1/events/{id}/feedback**
- Submit feedback
- Body: `{ "rating": "helpful" }` or `{ "rating": "not_helpful", "correction": "..." }`

**GET /api/v1/feedback/stats**
- Get feedback statistics
- Response:
```json
{
  "total_feedback": 150,
  "helpful_rate": 0.85,
  "by_camera": { "uuid": { "helpful": 45, "not_helpful": 8 } }
}
```

### Integrations API

**GET /api/v1/integrations/mqtt/status**
- Get MQTT connection status

**POST /api/v1/integrations/mqtt/test**
- Test MQTT publish

**PUT /api/v1/integrations/mqtt/config**
- Update MQTT configuration

## Phase 4 Service Architecture

### Context Service Flow

```
Event Created
     │
     ▼
┌─────────────────┐
│ Embedding       │ Generate CLIP embedding
│ Service         │ for thumbnail
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Similarity      │ Find similar past events
│ Service         │ within time window
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context         │ Match to known entities
│ Service         │ Add historical context
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ AI Service      │ Enhanced prompt with
│ (existing)      │ context information
└─────────────────┘
```

### Push Notification Flow

```
Event Created
     │
     ▼
┌─────────────────┐
│ Check           │ User preferences,
│ Preferences     │ quiet hours
└────────┬────────┘
         │ (if enabled)
         ▼
┌─────────────────┐
│ Format          │ Create rich notification
│ Notification    │ with thumbnail
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Push Service    │ Send via Web Push API
│                 │ Track delivery
└─────────────────┘
```

### MQTT Publishing Flow

```
Event Created
     │
     ▼
┌─────────────────┐
│ MQTT Service    │ Check connection
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Serialize       │ Format event as JSON
│ Event           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Publish         │ To camera topic
│                 │ QoS 1 for reliability
└─────────────────┘
```

## Phase 4 ADRs

### ADR-P4-001: Image Embedding Model Selection

**Decision:** Use CLIP (ViT-B/32) for image embeddings

**Context:**
- Need vector representations for similarity search
- Must run locally (privacy requirement)
- Should be fast enough for real-time processing

**Options Considered:**
1. OpenAI CLIP - Good quality, well-documented
2. SigLIP - Newer, potentially better quality
3. ResNet features - Simpler but less semantic

**Decision:** CLIP ViT-B/32
- 512-dimensional embeddings (good balance)
- ~100ms inference time per image
- Strong semantic understanding
- Well-supported by sentence-transformers

**Status:** Proposed

---

### ADR-P4-002: MQTT vs REST for Home Assistant

**Decision:** MQTT with Home Assistant Discovery

**Context:**
- Need to integrate with Home Assistant
- Want automatic entity discovery
- Must be reliable and low-latency

**Options Considered:**
1. REST API polling from HA
2. MQTT publishing with Discovery
3. Custom Home Assistant integration

**Decision:** MQTT
- Native HA support via MQTT Discovery
- Real-time event delivery
- Standard protocol, works with other systems
- QoS ensures delivery

**Status:** Accepted

---

### ADR-P4-003: Vector Database Choice

**Decision:** pgvector extension for PostgreSQL, fall back to SQLite with numpy

**Context:**
- Need efficient similarity search
- Must work with existing database setup
- Should scale to 100k+ embeddings

**Options Considered:**
1. pgvector (PostgreSQL extension)
2. Pinecone (cloud vector DB)
3. Milvus (self-hosted vector DB)
4. SQLite + numpy (simple approach)

**Decision:**
- Primary: pgvector if PostgreSQL
- Fallback: SQLite + numpy cosine similarity for MVP
- Cloud options rejected (privacy, self-hosted requirement)

**Status:** Proposed

---

## Phase 4 Performance Considerations

**Embedding Generation:**
- Target: <200ms per image
- Batch processing for backfill
- Cache embeddings (never regenerate)

**Similarity Search:**
- Target: <100ms for top-10 similar
- Use IVFFlat index with pgvector
- Limit search to recent events (configurable window)

**Push Notifications:**
- Target: <5 seconds from event to notification
- Async sending (don't block event pipeline)
- Batch notifications if multiple events in quick succession

**MQTT Publishing:**
- Target: <100ms added latency
- Connection pooling
- Reconnect with exponential backoff

## Phase 4 Validation Checklist

- ✅ PRD Phase 4 functional requirements have architectural support
- ✅ Privacy requirements addressed (local embeddings, no cloud vectors)
- ✅ Smart home integration via standard MQTT protocol
- ✅ Push notification architecture with Web Push API
- ✅ Context engine designed with graceful degradation
- ✅ Feedback collection and storage designed
- ✅ Database schema supports all new features
- ✅ API contracts defined for all new endpoints
- ✅ Performance targets established

---

**Phase 4 Architecture Update:**
- **Updated by:** Claude Code
- **Date:** 2025-12-10
- **PRD Reference:** `docs/PRD-phase4.md`
- **Epics Reference:** `docs/epics-phase4.md`

---
