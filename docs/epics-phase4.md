# Phase 4 Epics: Intelligent Context & Smart Home Integration

**Source PRD:** `docs/PRD-phase4.md`
**Phase Focus:** Temporal intelligence, smart home integration, mobile notifications, user feedback

---

## Epic P4-1: Push Notifications & PWA

**Goal:** Enable real-time push notifications on mobile and desktop, with Progressive Web App support for native-like mobile experience.

**Business Value:** Users receive instant alerts without keeping the app open, improving response time to security events.

### Stories

#### Story P4-1.1: Implement Web Push Backend
- Add VAPID key generation and storage
- Create push subscription management API
- Implement notification queue with delivery tracking
- Add retry logic for failed deliveries
- Track delivery success metrics

#### Story P4-1.2: Create Push Subscription UI
- Add notification permission request flow
- Build subscription management in settings
- Show notification preview
- Handle permission denied gracefully

#### Story P4-1.3: Rich Notification Formatting
- Include thumbnail in notifications
- Add action buttons (View, Dismiss)
- Implement notification collapse (same event updates)
- Deep link to event details

#### Story P4-1.4: Notification Preferences
- Per-camera notification toggles
- Object type filters (only notify for persons)
- Quiet hours configuration
- Notification sound selection

#### Story P4-1.5: PWA Manifest & Service Worker
- Create PWA manifest with icons
- Implement service worker for offline support
- Add install prompt for mobile users
- Cache critical assets for offline access

---

## Epic P4-2: Home Assistant Integration

**Goal:** Seamlessly integrate with Home Assistant via MQTT, enabling users to create automations based on AI-detected events.

**Business Value:** Users can trigger smart home actions (lights, locks, announcements) based on what the AI sees, not just motion detection.

### Stories

#### Story P4-2.1: MQTT Client Implementation
- Add Paho MQTT client to backend
- Implement connection management with auto-reconnect
- Create event serialization for MQTT payloads
- Add MQTT configuration in settings

#### Story P4-2.2: Home Assistant Discovery
- Implement MQTT Discovery protocol
- Create sensor entities for each camera
- Publish device configuration on startup
- Handle entity availability/unavailability

#### Story P4-2.3: Event Publishing
- Publish events to camera-specific topics
- Include full event metadata in payload
- Add thumbnail URL in event data
- Implement QoS settings for reliability

#### Story P4-2.4: Integration Settings UI
- MQTT broker configuration form
- Connection test functionality
- Discovery enable/disable toggle
- Topic prefix customization

#### Story P4-2.5: Camera Status Sensors
- Publish camera online/offline status
- Add last event timestamp sensor
- Create event count sensors (today, this week)
- Binary sensor for recent activity

---

## Epic P4-3: Temporal Context Engine

**Goal:** Give AI descriptions historical context by identifying recurring visitors, detecting patterns, and enriching descriptions with "seen before" information.

**Business Value:** Transform isolated events into contextual narratives - "This is your regular mail carrier" vs "Unknown person at door."

### Stories

#### Story P4-3.1: Event Embedding Generation
- Integrate CLIP or SigLIP model
- Generate embeddings for event thumbnails
- Store embeddings in database
- Implement batch processing for existing events

#### Story P4-3.2: Similarity Search
- Implement cosine similarity search
- Create efficient vector indexing
- Find similar events within time window
- Optimize for sub-500ms queries

#### Story P4-3.3: Recurring Visitor Detection
- Cluster similar embeddings
- Create recognized entity records
- Track first seen, last seen, occurrence count
- Match new events to known entities

#### Story P4-3.4: Context-Enhanced AI Prompts
- Include similarity results in AI prompt
- Add "previously seen" context to descriptions
- Format historical information naturally
- A/B test context inclusion impact

#### Story P4-3.5: Pattern Detection
- Analyze time-of-day patterns
- Detect day-of-week regularity
- Identify unusual timing anomalies
- Create pattern summary data

#### Story P4-3.6: Entity Management UI
- List recognized entities (people, vehicles)
- Allow naming entities
- Delete/merge entity records
- Show entity occurrence history

---

## Epic P4-4: Activity Summaries & Digests

**Goal:** Generate natural language summaries of activity, delivered as daily digests or on-demand reports.

**Business Value:** Users get a quick overview of "what happened" without scrolling through individual events.

### Stories

#### Story P4-4.1: Summary Generation Service
- Create LLM-based summary generator
- Process events for time period
- Generate natural language narrative
- Handle edge cases (no events, many events)

#### Story P4-4.2: Daily Digest Scheduler
- Implement scheduled digest generation
- Configure digest delivery time
- Track digest generation status
- Handle generation failures gracefully

#### Story P4-4.3: Digest Delivery
- Email delivery option
- Push notification with summary
- In-app digest viewing
- Configurable delivery channels

#### Story P4-4.4: Summary UI in Dashboard
- Add summary card to dashboard
- Show today/yesterday summary
- Quick stats (event counts, highlights)
- Link to full summary view

#### Story P4-4.5: On-Demand Summary Generation
- "Summarize last X hours" feature
- Custom time period selection
- Immediate summary generation
- Loading state and error handling

---

## Epic P4-5: User Feedback & Learning

**Goal:** Collect user feedback on AI descriptions to improve accuracy over time.

**Business Value:** System learns from corrections, reducing false positives and improving description quality.

### Stories

#### Story P4-5.1: Feedback Collection UI
- Add thumbs up/down to event cards
- Quick feedback button (single tap)
- Optional correction text input
- Feedback confirmation toast

#### Story P4-5.2: Feedback Storage & API
- Create feedback database model
- Implement feedback submission API
- Track feedback by event, user, camera
- Aggregate feedback statistics

#### Story P4-5.3: Accuracy Dashboard
- Show feedback statistics in settings
- Per-camera accuracy metrics
- Trend analysis over time
- Export feedback data

#### Story P4-5.4: Feedback-Informed Prompts
- Analyze common corrections
- Identify prompt improvement opportunities
- A/B test prompt variations
- Document prompt evolution

---

## Epic P4-6: Voice Assistant Integration (Growth)

**Goal:** Enable voice queries and HomeKit integration for hands-free security monitoring.

**Business Value:** Users can ask "What's happening at the front door?" and get AI-powered responses.

### Stories

#### Story P4-6.1: HomeKit Accessory Server
- Implement HAP-python accessory
- Create motion sensor accessories per camera
- Handle accessory pairing
- Manage accessory state updates

#### Story P4-6.2: HomeKit Motion Events
- Trigger motion sensor on new events
- Reset motion after timeout
- Handle multiple rapid events
- Sync state with actual events

#### Story P4-6.3: Voice Query API
- Create natural language query endpoint
- Parse time-based queries ("today", "this morning")
- Generate spoken response text
- Handle ambiguous queries

---

## Epic P4-7: Behavioral Anomaly Detection (Growth)

**Goal:** Automatically flag unusual activity by learning normal patterns and detecting deviations.

**Business Value:** Proactive security alerts for genuinely unusual events, reducing alert fatigue from routine activity.

### Stories

#### Story P4-7.1: Baseline Activity Learning
- Collect activity statistics per camera
- Build time-of-day activity model
- Build day-of-week activity model
- Update baseline continuously

#### Story P4-7.2: Anomaly Scoring
- Compare events to baseline
- Calculate anomaly score
- Define severity thresholds
- Handle new cameras (no baseline)

#### Story P4-7.3: Anomaly Alerts
- Flag high-anomaly events
- Add anomaly indicator to event cards
- Create anomaly-specific notifications
- Allow anomaly threshold adjustment

---

## Epic P4-8: Person & Vehicle Recognition (Growth)

**Goal:** Identify and name recurring people and vehicles for personalized alerts.

**Business Value:** "John is at the door" instead of "Person detected" - familiar vs stranger distinction.

### Stories

#### Story P4-8.1: Face Embedding Storage
- Extract face regions from thumbnails
- Generate face embeddings
- Store with privacy controls
- Handle no-face scenarios

#### Story P4-8.2: Person Matching
- Match faces to known persons
- Handle multiple people in frame
- Confidence thresholds for matching
- Handle aging/appearance changes

#### Story P4-8.3: Vehicle Recognition
- Detect vehicles in frames
- Extract vehicle characteristics
- Match recurring vehicles
- Vehicle type classification

#### Story P4-8.4: Named Entity Alerts
- Use names in notifications
- "Known person" vs "Stranger" classification
- VIP alerts for specific people
- Blocklist for unwanted alerts

---

## Definition of Done (All Stories)

- [ ] All acceptance criteria verified
- [ ] Unit tests passing (70%+ coverage for new code)
- [ ] Integration tests for API endpoints
- [ ] No TypeScript/Python type errors
- [ ] Code review completed
- [ ] Documentation updated
- [ ] No new security vulnerabilities
- [ ] Performance within NFR limits

---

## Epic Dependencies

```
P4-1 (Push/PWA) ──────────────────────────────────────┐
                                                       │
P4-2 (Home Assistant) ────────────────────────────────┤
                                                       │
P4-3 (Context) ───────┬───────────────────────────────┤
                      │                                │
                      ├──► P4-7 (Anomaly Detection)    │
                      │                                │
                      └──► P4-8 (Person Recognition)   │
                                                       │
P4-4 (Summaries) ──────────────────────────────────── │
                                                       │
P4-5 (Feedback) ───────────────────────────────────── │
                                                       │
P4-6 (Voice) ─────────────────────────────────────────┘
```

**Parallel Work Possible:**
- P4-1 (Push) and P4-2 (Home Assistant) can proceed in parallel
- P4-4 (Summaries) and P4-5 (Feedback) can proceed in parallel
- P4-3 (Context) is prerequisite for P4-7 and P4-8

---

## Estimated Effort

| Epic | Stories | Complexity | Estimate |
|------|---------|------------|----------|
| P4-1 | 5 | Medium | 2-3 weeks |
| P4-2 | 5 | Medium | 2 weeks |
| P4-3 | 6 | High | 3-4 weeks |
| P4-4 | 5 | Medium | 1-2 weeks |
| P4-5 | 4 | Low | 1-2 weeks |
| P4-6 | 3 | High | 2-3 weeks |
| P4-7 | 3 | Medium | 2 weeks |
| P4-8 | 4 | High | 3 weeks |

**Total MVP (P4-1 through P4-5):** 9-13 weeks
**Total with Growth (P4-6 through P4-8):** 16-21 weeks

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-10 | 1.0 | Initial Phase 4 epics creation |
