# ArgusAI - Phase 4 PRD

**Author:** Brent
**Date:** 2025-12-10
**Version:** 1.0

---

## Executive Summary

Phase 4 transforms the ArgusAI from a reactive event system into an **intelligent context-aware assistant**. By remembering past events, detecting patterns, and integrating with smart home ecosystems, the system becomes proactive - telling you not just what's happening, but what's unusual, what you should know, and automating responses to routine events.

This phase builds on the video-aware AI descriptions from Phase 3, adding temporal intelligence and ecosystem connectivity.

### What Makes This Special

> **Events don't happen in isolation.** Context transforms data into insight.

The same "person at door" event means very different things:
- **Without context:** "A person is at your front door"
- **With context:** "The Amazon driver is back - they delivered a package yesterday at the same time. This is their 3rd delivery this week."

Phase 4 gives users **intelligent awareness** - understanding patterns, recognizing familiar visitors, and seamlessly connecting to their smart home for automated responses.

---

## Project Classification

**Technical Type:** Full-stack web application (Python FastAPI + Next.js)
**Domain:** Home security / AI vision analysis / Smart home integration
**Complexity:** High (temporal analytics, face matching, ecosystem APIs, mobile push)
**Field Type:** Brownfield (extending existing Phase 1-3 codebase)

### Prior Work

- **Phase 1:** Core event detection system with RTSP/USB cameras, motion detection, AI descriptions, alert rules, dashboard
- **Phase 2:** UniFi Protect integration with controller management, camera discovery, smart detection events, doorbell support, multi-camera correlation
- **Phase 3:** Video clip analysis with multi-frame/video-native modes, audio transcription, confidence scoring, cost monitoring

---

## Success Criteria

### Primary Success Metrics

1. **Contextual Intelligence**
   - 50%+ of descriptions include relevant historical context
   - Users report "the system knows my home" feeling
   - Reduction in false alerts through pattern learning

2. **Smart Home Integration**
   - Works with Home Assistant, HomeKit, and major voice assistants
   - Users can trigger automations based on AI descriptions
   - Event data accessible via standard protocols (MQTT, webhooks)

3. **Mobile Accessibility**
   - Push notifications delivered within 5 seconds
   - Rich notifications with thumbnails and quick actions
   - PWA installable on iOS and Android

4. **Continuous Improvement**
   - User feedback loop improves description accuracy
   - System learns camera-specific patterns
   - False positive rate decreases over time

### What "Done" Looks Like

- User gets push notification: "Regular mail carrier arrived - they visit Mon/Wed/Fri around 2pm"
- Homekit scene triggers automatically when "car in driveway" is detected
- User says "Hey Siri, who's been at my door today?" and gets a summary
- Weekly digest email: "Your home this week: 12 deliveries, 3 visitors, 1 unusual event flagged"

---

## Product Scope

### MVP - Minimum Viable Product

**Epic P4-1: Temporal Context Engine**
- Store event embeddings for similarity matching
- Detect recurring visitors/vehicles across events
- Add "seen before" context to AI descriptions
- Time-of-day and day-of-week pattern detection

**Epic P4-2: Activity Summaries & Digests**
- Daily activity digest generation
- Weekly summary reports
- Natural language summaries ("Quiet day - just the mail carrier")
- Email/notification delivery of summaries

**Epic P4-3: Push Notifications (Mobile)**
- Web Push API integration for browser notifications
- Rich notifications with thumbnails
- Notification preferences and quiet hours
- Progressive Web App (PWA) manifest for mobile install

**Epic P4-4: Home Assistant Integration**
- MQTT broker connection for event publishing
- Home Assistant auto-discovery (MQTT Discovery)
- Custom sensors for camera status and event counts
- Automation triggers on AI description content

### Growth Features (Post-MVP)

**Epic P4-5: Voice Assistant Integration**
- HomeKit integration via HAP-python
- Alexa skill for event queries
- Google Home integration
- Natural language queries ("What happened while I was out?")

**Epic P4-6: User Feedback & Learning**
- Thumbs up/down on event descriptions
- Correction submission UI
- Feedback-informed prompt refinement
- Per-camera prompt customization based on feedback

**Epic P4-7: Behavioral Anomaly Detection**
- Learn normal activity patterns per camera
- Flag unusual events automatically
- Anomaly scoring and alerting
- "Unusual activity at 2am" type notifications

**Epic P4-8: Person & Vehicle Recognition**
- Face embedding storage (privacy-conscious)
- Vehicle make/model detection
- Named person/vehicle tagging
- "Known person" vs "stranger" classification

### Vision Features (Future)

- Geofencing integration (different modes when home vs away)
- Multi-user support with per-user preferences
- Integration with commercial alarm systems
- Predictive alerting ("Vehicle slowing down - may stop")
- Natural language search across all event history

---

## Functional Requirements

### Temporal Context

- **FR1:** System stores event embeddings for similarity comparison
- **FR2:** System identifies recurring visitors based on appearance similarity
- **FR3:** System detects time-based patterns (daily, weekly)
- **FR4:** AI descriptions include historical context when relevant
- **FR5:** System maintains a "familiar faces/vehicles" registry

### Activity Summaries

- **FR6:** System generates natural language daily summaries
- **FR7:** System sends digest notifications at configurable times
- **FR8:** Summaries include event counts, highlights, and anomalies
- **FR9:** Users can query activity for any time period

### Push Notifications

- **FR10:** System supports Web Push for browser notifications
- **FR11:** Notifications include thumbnail preview
- **FR12:** Users can configure notification preferences per camera
- **FR13:** Quiet hours prevent notifications during specified times
- **FR14:** PWA is installable on mobile devices

### Home Assistant Integration

- **FR15:** System publishes events to MQTT broker
- **FR16:** Home Assistant discovers sensors automatically
- **FR17:** Events include structured data for automation triggers
- **FR18:** System reports camera online/offline status

### Voice Assistants

- **FR19:** HomeKit accessory for camera status
- **FR20:** Voice queries return recent event summaries
- **FR21:** Voice triggers can request manual analysis

### User Feedback

- **FR22:** Users can rate event descriptions (helpful/not helpful)
- **FR23:** Users can submit description corrections
- **FR24:** System tracks accuracy metrics per camera
- **FR25:** Feedback influences future prompt engineering

### Anomaly Detection

- **FR26:** System learns baseline activity patterns
- **FR27:** Events deviating from baseline are flagged
- **FR28:** Anomaly severity is scored (low/medium/high)
- **FR29:** Users can adjust sensitivity per camera

---

## Non-Functional Requirements

### NFR1: Privacy & Data Protection

- Face embeddings stored locally only (never cloud)
- User can delete all historical context data
- No PII transmitted to AI providers beyond image content
- Configurable retention for context data (separate from event retention)

### NFR2: Performance

- Context lookup adds <500ms to event processing
- Push notifications delivered within 5 seconds
- Digest generation completes within 60 seconds
- MQTT publishing adds <100ms latency

### NFR3: Reliability

- MQTT connection auto-reconnects on failure
- Push notification delivery tracked and retried
- Context engine gracefully degrades if unavailable
- HomeKit accessory remains responsive during high load

### NFR4: Scalability

- Context database handles 100,000+ events
- Embedding search efficient with vector indexing
- Summary generation parallelizable

---

## Technical Architecture

### New Components

**Temporal Context Service**
- SQLite or PostgreSQL with vector extension (pgvector)
- CLIP or similar model for image embeddings
- Cosine similarity for visitor matching
- Time-series analysis for pattern detection

**Notification Service**
- Web Push API with VAPID keys
- Push subscription management
- Notification queue with retry logic
- Rich notification formatting

**MQTT Bridge**
- Paho MQTT client for publishing
- Home Assistant MQTT Discovery payloads
- Event serialization to JSON
- Connection management with auto-reconnect

**Digest Generator**
- Scheduled job (daily/weekly)
- LLM-based summary generation
- Template system for email formatting
- Delivery via configured channels

### Database Additions

```sql
-- Event embeddings for similarity search
CREATE TABLE event_embeddings (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    embedding VECTOR(512),  -- CLIP embedding
    created_at TIMESTAMP
);

-- Recognized entities (people, vehicles)
CREATE TABLE recognized_entities (
    id UUID PRIMARY KEY,
    entity_type TEXT,  -- 'person', 'vehicle'
    name TEXT,  -- User-assigned name (nullable)
    reference_embedding VECTOR(512),
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    occurrence_count INTEGER
);

-- Push subscriptions
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    endpoint TEXT,
    p256dh_key TEXT,
    auth_key TEXT,
    created_at TIMESTAMP
);

-- User feedback
CREATE TABLE event_feedback (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    user_id UUID REFERENCES users(id),
    rating TEXT,  -- 'helpful', 'not_helpful'
    correction TEXT,  -- User-provided correction
    created_at TIMESTAMP
);
```

### API Additions

```
# Context
GET  /api/v1/context/similar/{event_id}     # Find similar past events
GET  /api/v1/context/patterns/{camera_id}   # Get activity patterns
GET  /api/v1/entities                        # List recognized entities
PUT  /api/v1/entities/{id}                   # Name an entity

# Summaries
GET  /api/v1/summaries/daily?date=2025-12-10
GET  /api/v1/summaries/weekly?week=2025-W50
POST /api/v1/summaries/generate              # Trigger manual generation

# Notifications
POST /api/v1/push/subscribe                  # Register push subscription
DELETE /api/v1/push/subscribe                # Unsubscribe
GET  /api/v1/push/preferences                # Get notification preferences
PUT  /api/v1/push/preferences                # Update preferences

# Feedback
POST /api/v1/events/{id}/feedback            # Submit feedback
GET  /api/v1/feedback/stats                  # Accuracy metrics

# Integrations
GET  /api/v1/integrations/mqtt/status        # MQTT connection status
POST /api/v1/integrations/mqtt/test          # Test MQTT publish
GET  /api/v1/integrations/homekit/status     # HomeKit status
```

---

## Integration Specifications

### Home Assistant MQTT Discovery

Events published to `homeassistant/sensor/liveobject/{camera_id}/state`:

```json
{
  "event_id": "uuid",
  "camera_name": "Front Door",
  "description": "Person at door with package",
  "objects_detected": ["person", "package"],
  "confidence": 85,
  "timestamp": "2025-12-10T14:30:00Z",
  "thumbnail_url": "http://localhost:8000/api/v1/thumbnails/..."
}
```

Discovery config published to `homeassistant/sensor/liveobject_{camera_id}/config`:

```json
{
  "name": "Front Door Events",
  "unique_id": "liveobject_camera_uuid",
  "state_topic": "homeassistant/sensor/liveobject/uuid/state",
  "value_template": "{{ value_json.description }}",
  "json_attributes_topic": "homeassistant/sensor/liveobject/uuid/state",
  "device": {
    "identifiers": ["liveobject"],
    "name": "Live Object AI",
    "manufacturer": "Live Object AI",
    "model": "Classifier"
  }
}
```

### HomeKit Integration

Camera exposed as HomeKit Motion Sensor:
- Motion detected = event created in last 30 seconds
- Accessory name = camera name
- Service type = MotionSensor

Optional: Camera accessory type (requires additional streaming work)

### Web Push Notification Format

```json
{
  "title": "Front Door: Person Detected",
  "body": "Delivery driver with package, facing door",
  "icon": "/icons/notification-192.png",
  "image": "data:image/jpeg;base64,...",  // Thumbnail
  "badge": "/icons/badge-72.png",
  "tag": "event-uuid",  // Collapse duplicate notifications
  "data": {
    "event_id": "uuid",
    "url": "/events?highlight=uuid"
  },
  "actions": [
    {"action": "view", "title": "View"},
    {"action": "dismiss", "title": "Dismiss"}
  ]
}
```

---

## Dependencies & Third-Party Services

### New Backend Dependencies

- `paho-mqtt` - MQTT client for Home Assistant
- `pywebpush` - Web Push notifications
- `sentence-transformers` or `clip` - Image embeddings
- `pgvector` - Vector similarity (if using PostgreSQL)
- `HAP-python` - HomeKit accessory server

### New Frontend Dependencies

- Service Worker for push notifications
- PWA manifest and icons
- `next-pwa` - PWA plugin for Next.js

### External Services

- MQTT Broker (user-provided, typically Mosquitto)
- Email service for digests (optional, user-configured)
- No new cloud dependencies

---

## Development Phases

### Phase 4.1: Push Notifications & PWA (2-3 weeks)
- Web Push implementation
- PWA manifest and service worker
- Notification preferences UI
- Mobile install experience

### Phase 4.2: Home Assistant Integration (2 weeks)
- MQTT publishing
- Home Assistant discovery
- Camera sensors and event attributes
- Integration settings UI

### Phase 4.3: Temporal Context (3-4 weeks)
- Event embedding generation
- Similarity search
- Pattern detection
- Context-enhanced descriptions

### Phase 4.4: Activity Summaries (1-2 weeks)
- Daily digest generation
- Email delivery
- Summary UI in dashboard

### Phase 4.5: User Feedback (1-2 weeks)
- Feedback collection UI
- Accuracy tracking
- Feedback integration with prompts

---

## Risks & Mitigation

### High-Priority Risks

**Risk 1: Embedding Model Performance**
- **Impact:** Slow context lookup degrades user experience
- **Mitigation:** Use efficient models (MiniLM), implement caching, set timeouts

**Risk 2: Privacy Concerns with Face Matching**
- **Impact:** Users uncomfortable with facial recognition
- **Mitigation:** Make it opt-in, local-only storage, clear data deletion

**Risk 3: Home Assistant Compatibility**
- **Impact:** Different HA versions may have different MQTT requirements
- **Mitigation:** Test with multiple HA versions, follow official discovery spec

### Medium-Priority Risks

**Risk 4: Push Notification Delivery**
- **Impact:** Notifications delayed or not received
- **Mitigation:** Implement delivery tracking, fallback to in-app notifications

**Risk 5: Context Database Size**
- **Impact:** Embedding storage grows large
- **Mitigation:** Implement retention policy, deduplicate similar embeddings

---

## Open Questions

1. **Embedding Model Choice:** CLIP vs SigLIP vs custom model?
2. **HomeKit Camera Streaming:** Worth the complexity for camera accessory type?
3. **Alexa/Google Integration:** Custom skill or via Home Assistant bridge?
4. **Digest Delivery:** Email only, or also in-app/push?
5. **Feedback Impact:** How directly should feedback modify prompts?

---

## Success Metrics

### Phase 4.1 (Push/PWA)
- 80%+ of users enable push notifications
- PWA installed by 30%+ of mobile users
- Notification delivery success rate >95%

### Phase 4.2 (Home Assistant)
- Successful discovery in 3+ HA versions
- 50%+ of users with HA enable integration
- <100ms average MQTT publish latency

### Phase 4.3 (Context)
- 50%+ of events include historical context
- User satisfaction with context accuracy >70%
- Context lookup <500ms p95

### Phase 4.4 (Summaries)
- 60%+ of users enable daily digests
- Summary generation <60 seconds
- User open rate for digest emails >40%

---

## Appendix

### Glossary

- **Embedding:** Vector representation of an image for similarity comparison
- **MQTT:** Lightweight messaging protocol used by Home Assistant
- **PWA:** Progressive Web App - installable web application
- **VAPID:** Web Push authentication protocol
- **HAP:** HomeKit Accessory Protocol
- **Context:** Historical information enriching current event understanding

### Related Documents

- Phase 1-3 PRDs: `docs/prd.md`, `docs/PRD-phase2.md`, `docs/PRD-phase3.md`
- Brainstorming Results: `docs/brainstorming-session-results-2025-12-05.md`
- Architecture: `docs/architecture.md`

---

**Version History**

| Version | Date       | Author | Changes                |
|---------|------------|--------|------------------------|
| 1.0     | 2025-12-10 | Brent  | Initial Phase 4 PRD    |
