# Epic Technical Specification: Package Delivery Alerts

Date: 2025-12-17
Author: Brent
Epic ID: P7-2
Status: Draft

---

## Overview

Epic P7-2 implements package delivery detection with carrier identification, enabling users to receive alerts when packages from FedEx, UPS, USPS, Amazon, or DHL are delivered. This feature extends the existing AI analysis pipeline to extract carrier information from delivery person uniforms and delivery vehicle markings, creates a new "Package Delivery" alert rule type, triggers HomeKit package sensors with carrier context, and adds a dashboard widget showing recent deliveries.

The implementation builds on the existing AI service (`backend/app/services/ai_service.py`), alert engine (`backend/app/services/alert_engine.py`), and HomeKit package sensor (`backend/app/services/homekit_accessories.py`) established in previous phases.

## Objectives and Scope

### In Scope
- Update AI prompt to identify carriers: FedEx, UPS, USPS, Amazon, DHL
- Add `delivery_carrier` field to event schema
- Extract carrier from AI description using pattern matching
- Store carrier in event record when detected
- Return carrier in event API responses
- Add "Package Delivery" to alert rule types
- Support filtering by carrier (any, specific, multiple carriers)
- Trigger when package detected AND carrier identified
- Include carrier name in alert message
- Support all notification channels (push, webhook, MQTT)
- Trigger HomeKit package sensor on delivery detection
- Create dashboard widget showing recent package deliveries

### Out of Scope
- OCR for reading tracking numbers
- Integration with carrier tracking APIs
- Signature confirmation detection
- Multi-package detection (count of packages)
- Secure package locker integration

## System Architecture Alignment

This epic aligns with the existing AI and alert architecture:

**Components Modified:**
- `backend/app/services/ai_service.py` - Update prompts for carrier detection
- `backend/app/models/event.py` - Add delivery_carrier field
- `backend/app/schemas/event.py` - Add delivery_carrier to response schemas
- `backend/app/services/event_processor.py` - Extract carrier from descriptions
- `backend/app/services/alert_engine.py` - Add package delivery rule type
- `backend/app/models/alert_rule.py` - Add carrier filter to rule config
- `backend/app/services/homekit_service.py` - Enhance package sensor triggers
- `frontend/components/dashboard/` - Add package delivery widget

**Architecture Constraints:**
- AI provider must support vision (OpenAI, Grok, Claude, Gemini)
- Alert rule evaluation happens synchronously in event pipeline
- HomeKit triggers happen asynchronously via existing mechanism

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs |
|----------------|----------------|--------|---------|
| `AIService.describe()` | Generate description with carrier | Image/frames, enhanced prompt | Description with carrier mention |
| `CarrierExtractor` | Extract carrier from AI description | AI description text | Carrier enum or None |
| `EventProcessor` | Process events with carrier extraction | Event with description | Event with delivery_carrier |
| `AlertEngine` | Evaluate package delivery rules | Event, alert rules | Triggered alerts |
| `PackageDeliveryWidget` | Display recent deliveries | Events API | Rendered widget |

### Data Models and Contracts

**Event model additions:**
```python
class Event(Base):
    # Existing fields...
    delivery_carrier: Optional[str] = Column(String(32), nullable=True)
    # Values: 'fedex', 'ups', 'usps', 'amazon', 'dhl', None
```

**Carrier extraction patterns:**
```python
CARRIER_PATTERNS = {
    'fedex': [r'fedex', r'fed\s*ex', r'federal\s*express'],
    'ups': [r'\bups\b', r'united\s*parcel'],
    'usps': [r'usps', r'postal\s*service', r'mail\s*carrier', r'mailman'],
    'amazon': [r'amazon', r'prime'],
    'dhl': [r'\bdhl\b', r'dhl\s*express'],
}
```

**AlertRule config additions:**
```python
class AlertRuleConfig(BaseModel):
    # Existing fields...
    rule_type: str  # 'any_motion', 'person', 'vehicle', 'package', 'package_delivery'
    carriers: Optional[List[str]] = None  # For package_delivery: ['fedex', 'ups', 'amazon']
```

**EventResponse schema additions:**
```python
class EventResponse(BaseModel):
    # Existing fields...
    delivery_carrier: Optional[str] = Field(None, description="Detected carrier if package delivery")
    delivery_carrier_display: Optional[str] = Field(None, description="Human-readable carrier name")
```

### APIs and Interfaces

**Updated: GET /api/v1/events**

Events now include delivery_carrier field:

```json
{
  "events": [
    {
      "id": 123,
      "camera_id": "abc-123",
      "smart_detection_type": "package",
      "delivery_carrier": "amazon",
      "delivery_carrier_display": "Amazon",
      "description": "An Amazon delivery driver in a blue vest placing a package at the front door.",
      "thumbnail_url": "/api/v1/events/123/thumbnail",
      "timestamp": "2025-12-17T14:30:00Z"
    }
  ]
}
```

**Updated: GET /api/v1/events?delivery_carrier=amazon,fedex**

Filter events by carrier.

**Updated: POST /api/v1/alert-rules**

New rule_type for package delivery:

```json
{
  "name": "Package Delivery Alert",
  "rule_type": "package_delivery",
  "cameras": ["abc-123", "def-456"],
  "carriers": ["fedex", "ups", "amazon"],
  "channels": ["push", "webhook"],
  "schedule": null,
  "enabled": true
}
```

**New: GET /api/v1/events/recent-deliveries**

Get recent package deliveries for dashboard widget:

```
GET /api/v1/events/recent-deliveries?limit=5

Response 200:
{
  "deliveries": [
    {
      "id": 123,
      "camera_name": "Front Door",
      "carrier": "amazon",
      "carrier_display": "Amazon",
      "timestamp": "2025-12-17T14:30:00Z",
      "thumbnail_url": "/api/v1/events/123/thumbnail"
    }
  ],
  "total_today": 3
}
```

### Workflows and Sequencing

**Carrier Detection Flow:**
```
1. Motion/Smart event received from camera
      ↓
2. AI service processes with enhanced prompt
   Prompt includes: "If you see a delivery person or truck,
   identify the carrier: FedEx, UPS, USPS, Amazon, or DHL."
      ↓
3. AI returns description mentioning carrier
   "An Amazon delivery driver in a blue vest placing a package..."
      ↓
4. CarrierExtractor parses description
   Pattern match against known carriers
      ↓
5. Event saved with delivery_carrier='amazon'
      ↓
6. Alert engine evaluates package_delivery rules
   Check if carrier matches rule filter
      ↓
7. If match: trigger notifications
   Push, webhook, MQTT with carrier in message
      ↓
8. HomeKit package sensor triggered with carrier context
```

**Alert Rule Evaluation for Package Delivery:**
```
1. Event with smart_detection_type='package' received
      ↓
2. Check if delivery_carrier is set
      ↓
3. Find rules where rule_type='package_delivery'
      ↓
4. For each rule:
   - Check if camera matches
   - Check schedule (if set)
   - Check carriers filter:
     * If carriers is None or empty: match any carrier
     * If carriers is set: delivery_carrier must be in list
      ↓
5. Trigger matched alerts with message:
   "Package delivered by {carrier} at {camera}"
```

## Non-Functional Requirements

### Performance

- Carrier extraction: < 10ms per description (regex matching)
- No additional AI calls (carrier extracted from existing description)
- Recent deliveries endpoint: < 100ms
- Dashboard widget render: < 200ms

### Security

- No PII collected from delivery persons
- Carrier detection purely visual (uniforms, vehicles)
- Event data subject to existing retention policies

### Reliability/Availability

- Carrier detection is best-effort (None if not identified)
- Alerts trigger even if carrier unknown (for generic package rules)
- Failed carrier extraction logged but doesn't fail event processing

### Observability

- Log carrier extraction success/failure rates
- Prometheus metrics: `argusai_carrier_detections_total{carrier="amazon"}`
- Dashboard shows carrier distribution in delivery widget

## Dependencies and Integrations

| Dependency | Version | Purpose |
|------------|---------|---------|
| OpenAI/Anthropic/Gemini | - | AI vision for description generation |
| HAP-python | 4.9+ | HomeKit package sensor (existing) |
| sonner | - | Toast notifications (existing) |

**Integration Points:**
- AI service (existing) - enhanced prompts
- Alert engine (existing) - new rule type
- HomeKit service (existing) - package sensor
- Push notification service (existing)
- MQTT service (existing)
- Webhook service (existing)

## Acceptance Criteria (Authoritative)

### Story P7-2.1: Add Carrier Detection to AI Analysis
1. AI prompt updated to identify FedEx, UPS, USPS, Amazon, DHL
2. `delivery_carrier` field added to Event model
3. Carrier extracted from AI description using pattern matching
4. Carrier stored in event record when detected
5. Carrier returned in event API responses

### Story P7-2.2: Create Package Delivery Alert Rule Type
1. "Package Delivery" added to alert rule types
2. Support filtering by carrier (any, specific carrier, multiple carriers)
3. Rule triggers when package detected AND carrier identified
4. Carrier name included in alert message
5. All notification channels supported (push, webhook, MQTT)

### Story P7-2.3: Add Package Delivery to HomeKit
1. Existing package sensor triggered on delivery detection
2. Carrier info logged for debugging
3. Separate sensors per carrier option available (config)
4. Delivery detection logged

### Story P7-2.4: Create Package Delivery Dashboard Widget
1. Widget shows last 5 package deliveries on dashboard
2. Each delivery displays: timestamp, camera, carrier, thumbnail
3. Link to full event detail available
4. Events page filterable by "Package Delivery"

## Traceability Mapping

| AC# | Spec Section | Component/API | Test Idea |
|-----|--------------|---------------|-----------|
| P7-2.1-1 | Detailed Design / AIService | ai_service.py prompts | Unit: verify prompt includes carrier detection |
| P7-2.1-2 | Data Models | Event model | Migration: add column, verify schema |
| P7-2.1-3 | Detailed Design / CarrierExtractor | carrier_extractor.py | Unit: test pattern matching for each carrier |
| P7-2.1-4 | Workflows | EventProcessor | Integration: process event, verify carrier saved |
| P7-2.1-5 | APIs / GET events | events.py | Integration: get event, verify carrier in response |
| P7-2.2-1 | Data Models / AlertRuleConfig | alert_rule.py | Unit: verify package_delivery type allowed |
| P7-2.2-2 | Workflows / Alert Evaluation | alert_engine.py | Unit: test carrier filter matching |
| P7-2.2-3 | Workflows / Alert Evaluation | alert_engine.py | Integration: package event triggers rule |
| P7-2.2-4 | Workflows / Alert Triggering | alert_engine.py | Unit: verify carrier in message template |
| P7-2.2-5 | Dependencies | alert channels | Integration: verify push/webhook/MQTT |
| P7-2.3-1 | Workflows / HomeKit | homekit_service.py | Integration: delivery triggers package sensor |
| P7-2.3-2 | NFRs / Observability | homekit_service.py | Unit: verify carrier logged on trigger |
| P7-2.3-3 | Data Models / HomekitConfig | config.py | Unit: per-carrier sensor config option |
| P7-2.3-4 | NFRs / Observability | homekit_service.py | Unit: verify detection logged |
| P7-2.4-1 | APIs / GET recent-deliveries | events.py | Integration: endpoint returns deliveries |
| P7-2.4-2 | Detailed Design / Widget | PackageDeliveryWidget.tsx | E2E: widget renders all fields |
| P7-2.4-3 | APIs / GET events | events.py | Integration: delivery_carrier filter works |
| P7-2.4-4 | Detailed Design / Widget | EventsPage.tsx | E2E: filter dropdown includes Package Delivery |

## Risks, Assumptions, Open Questions

### Risks
- **R1:** AI may not reliably identify carrier from uniform/vehicle
  - *Mitigation:* Provide detailed visual cues in prompt, accept partial detection
- **R2:** Regional carrier uniforms may differ from US patterns
  - *Mitigation:* Start with US carriers, expand based on feedback
- **R3:** Non-uniformed drivers (Amazon Flex, gig economy) harder to identify
  - *Mitigation:* Look for vehicle markings as backup, accept "unknown" carrier

### Assumptions
- **A1:** Major carriers have distinctive uniforms/vehicle colors
- **A2:** AI vision models can distinguish carrier-specific visual cues
- **A3:** Users primarily care about top 5 carriers (FedEx, UPS, USPS, Amazon, DHL)

### Open Questions
- **Q1:** Should we add carrier-specific icons/colors in UI?
  - *Recommendation:* Yes, use carrier brand colors for quick recognition
- **Q2:** Should we track delivery frequency per carrier?
  - *Recommendation:* Defer to future analytics epic
- **Q3:** What about international carriers (Royal Mail, Canada Post)?
  - *Recommendation:* Make carrier list configurable, add regional carriers later

## Test Strategy Summary

### Unit Tests
- Carrier extraction patterns for each carrier (10+ test cases per carrier)
- Alert rule evaluation with carrier filters
- Event schema validation with delivery_carrier field
- AI prompt generation includes carrier detection instructions

### Integration Tests
- `/api/v1/events` returns delivery_carrier
- `/api/v1/events?delivery_carrier=amazon` filters correctly
- `/api/v1/alert-rules` creates package_delivery rule
- `/api/v1/events/recent-deliveries` returns correct format
- Package delivery alert triggers push notification

### E2E Tests
- Dashboard widget displays recent deliveries
- Events page filter includes "Package Delivery"
- Click delivery in widget navigates to event detail
- Alert rule creation UI includes carrier selection

### Tools
- pytest for backend tests
- Vitest + React Testing Library for frontend
- Mock AI responses with carrier mentions
- Test fixtures with sample delivery events
