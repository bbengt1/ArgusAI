# PRD: User Personas & Stories

[← Back to PRD Index](./README.md) | [← Previous: Overview & Goals](./01-overview-goals.md) | [Next: Functional Requirements →](./03-functional-requirements.md)

---

## User Personas

### Persona 1: Security-Conscious Homeowner (Primary)

**Profile: Sarah, 42**

**Demographics:**
- Lives in suburban home with spouse and two children (ages 8 and 12)
- Works full-time as marketing manager
- Travels 3-4 times per year for business
- Household income: $120,000
- Tech comfort: Medium (uses smartphone apps, smart lock, Nest thermostat)

**Context:**
- Recently had package stolen from porch
- Neighborhood Facebook group discusses security concerns
- Has Ring doorbell but finds alerts overwhelming (mostly false positives)
- Wants to feel safe when traveling for work
- Values peace of mind over advanced features

**Goals & Motivations:**
- Know immediately when packages delivered
- Detect suspicious activity before incident occurs
- Receive meaningful alerts, not noise
- Review what happened when away from home
- Protect family and property

**Pain Points:**
- Current doorbell camera: 50+ alerts per day, 49 are false positives
- Can't easily search footage for "when was package delivered?"
- Hours of footage to review after trips
- Doesn't trust system to alert for real threats
- Alert fatigue - now ignores most notifications

**Technology Usage:**
- iPhone user (Safari browser)
- Checks phone throughout day
- Comfortable with app setup but not technical configuration
- Expects things to "just work"
- Reads reviews before trying new products

**Jobs to Be Done:**
1. Know when packages delivered so can retrieve quickly
2. Detect suspicious activity to take action before incident
3. Review what happened when away to verify security
4. Reduce false alarms to trust the system again

**Success Looks Like:**
- Receives 3-5 meaningful alerts per day (not 50)
- Can search "package delivery" and find all relevant events
- Descriptions detailed enough to make decisions (answer door? call police?)
- Setup took less than 10 minutes
- Confident leaving home knowing system watching

---

### Persona 2: Tech-Savvy Smart Home Enthusiast (Secondary)

**Profile: Marcus, 35**

**Demographics:**
- Lives in urban townhouse with partner
- Works as software developer
- Household income: $180,000
- Tech comfort: Very High (runs Home Assistant, multiple custom integrations)

**Context:**
- Has 15+ smart home devices (lights, locks, thermostats, sensors)
- Runs Home Assistant on Raspberry Pi
- Writes custom automations and scripts
- Active in r/homeautomation and Home Assistant forums
- Values privacy and local control

**Goals & Motivations:**
- Trigger complex automations based on visual detection
- Integrate security with entire smart home ecosystem
- Customize every aspect of the system
- Access data programmatically for custom dashboards
- Maintain privacy with local processing where possible

**Pain Points:**
- Existing security cameras don't integrate well with Home Assistant
- Basic motion detection too simple for interesting automations
- Commercial solutions don't provide API access
- Cloud-dependent systems violate privacy principles
- Can't customize alert logic beyond simple rules

**Technology Usage:**
- Multiple browsers, comfortable with developer tools
- Writes YAML configurations and Python scripts
- Uses API documentation to build integrations
- Contributes to open-source projects
- Comfortable with command-line setup

**Jobs to Be Done:**
1. Trigger automations based on what camera sees (not just motion)
2. Access event data programmatically for custom use cases
3. Customize alert logic beyond basic rules
4. Integrate deeply with Home Assistant
5. Run system locally for privacy and control

**Success Looks Like:**
- Webhook fires when "person + package" detected → automation announces delivery
- When Marcus detected → lights adjust to his preferences
- API access allows custom Grafana dashboard
- System runs on local network without cloud dependency
- Complex rules like "alert if vehicle parks for >5 minutes between 10pm-6am"

---

### Persona 3: Accessibility User (Secondary)

**Profile: Linda, 58 (Visually Impaired)**

**Demographics:**
- Lives independently in single-story home
- Retired teacher
- Has mobility challenges (uses walker occasionally)
- Tech comfort: Medium (uses iPhone with VoiceOver screen reader)

**Context:**
- Legally blind (macular degeneration)
- Depends on audio feedback for information
- Wants to maintain independence
- Concerned about answering door for strangers
- Has caregiver visit 3x per week

**Goals & Motivations:**
- Understand who's at door before answering
- Know when expected visitors (caregiver, family) arrive
- Verify delivery people vs solicitors
- Monitor outdoor activity without going outside
- Maintain sense of security and independence

**Pain Points:**
- Can't see video doorbell feeds
- Audio doorbells only say "someone at door" (not helpful)
- Must ask visitors to identify themselves verbally
- Worries about answering door to strangers
- Feels vulnerable not knowing what's happening outside

**Technology Usage:**
- iPhone with VoiceOver screen reader
- Prefers audio notifications to visual
- Large text and high contrast settings
- Voice control (Siri) when possible
- Needs accessible interfaces (WCAG compliant)

**Jobs to Be Done:**
1. Get detailed audio description of who's at door
2. Distinguish between delivery people, family, and strangers
3. Verify visitors without going to door
4. Understand outdoor activity without visual inspection
5. Feel secure and independent in own home

**Success Looks Like:**
- Notification reads aloud: "Adult male, approximately 40s, brown UPS uniform, carrying package"
- Can distinguish "woman in her 30s with blonde hair and red jacket" (niece Sarah)
- Descriptions detailed enough to make "answer door?" decision
- Interface works perfectly with VoiceOver
- Audio notifications automatic (no need to check screen)

---

## User Stories

### Package Delivery & Theft Prevention

```
US-1: Package Delivery Notification
As a homeowner (Sarah)
I want to be notified when a package is delivered
So that I can retrieve it quickly or ask a neighbor to secure it

Acceptance Criteria:
- Alert sent within 30 seconds of delivery person leaving
- Description includes: delivery company, package placement, person appearance
- Alert includes thumbnail image of the delivery
- Can configure "package detected" as alert condition
- Works with major delivery services (UPS, FedEx, USPS, Amazon)

Priority: MUST HAVE
Estimate: 4 points
Dependencies: F2 (Motion Detection), F3 (AI Descriptions), F5 (Alert Rules)
```

```
US-2: Suspicious Activity Detection
As a homeowner (Sarah)
I want to be alerted when someone suspicious is near my property
So that I can take action before an incident occurs

Acceptance Criteria:
- Alert triggered for loitering (person present >2 minutes with minimal movement)
- Alert triggered for repeated passes (same person 3+ times in 30 minutes)
- Description includes person appearance and behavior
- Time-of-day rules (e.g., any person after 10pm is suspicious)
- Can set "suspicious behavior" alert rules

Priority: MUST HAVE
Estimate: 5 points
Dependencies: F2 (Motion Detection), F3 (AI Descriptions), F5 (Alert Rules)
Note: Duration tracking is COULD HAVE for MVP (repeated passes only)
```

```
US-3: Review Event History
As a homeowner (Sarah)
I want to see what happened when I was away
So that I can understand activity patterns and verify security

Acceptance Criteria:
- Timeline view of all events with timestamps
- Filter by date range and event type (person, vehicle, package, animal)
- Search functionality for event descriptions (keyword search)
- Click event to see full details and thumbnail image
- Export events to CSV/JSON for record-keeping

Priority: MUST HAVE (except export = SHOULD HAVE)
Estimate: 5 points
Dependencies: F4 (Event Storage), F6 (Dashboard)
```

### Smart Home Integration

```
US-4: Webhook Integration for Automation
As a smart home enthusiast (Marcus)
I want to trigger webhooks when events occur
So that I can automate my home based on what the camera sees

Acceptance Criteria:
- Configure webhook URL per alert rule
- Webhook payload includes full event data (JSON format)
- Webhook fires within 2 seconds of event storage
- Test webhook button to verify configuration works
- Custom headers support (for authentication tokens)
- Retry logic (3 attempts with exponential backoff)

Priority: SHOULD HAVE
Estimate: 5 points
Dependencies: F5 (Alert Rules), F9 (Webhook Integration)
```

```
US-5: Custom Alert Rules
As a smart home enthusiast (Marcus)
I want to define complex alert conditions
So that I can fine-tune when I'm notified

Acceptance Criteria:
- Combine multiple conditions with AND/OR logic
- Time-based conditions (only alert during specific hours/days)
- Object-based conditions (person + package, vehicle + specific characteristics)
- NOT logic (exclude certain conditions)
- Test rule button shows which past events would match
- Rules saved and persisted across restarts

Priority: SHOULD HAVE (basic rules = MUST HAVE)
Estimate: 8 points
Dependencies: F5 (Alert Rules)
```

```
US-6: API Access to Events
As a smart home enthusiast (Marcus)
I want API access to event history
So that I can build custom dashboards and integrations

Acceptance Criteria:
- RESTful API endpoints for event queries
- Filter by date range, camera, object type
- Pagination for large result sets (100+ events)
- API key authentication
- API documentation (OpenAPI/Swagger)
- CORS support for web-based custom dashboards

Priority: COULD HAVE
Estimate: 5 points
Dependencies: F4 (Event Storage), F7 (Authentication)
```

### Accessibility

```
US-7: Detailed Visitor Descriptions
As a visually impaired user (Linda)
I want rich descriptions of people at my door
So that I can decide whether to answer without seeing them

Acceptance Criteria:
- Description includes: approximate age, gender presentation, clothing colors/style
- Description includes: what they're carrying (clipboard, package, flowers, etc.)
- Description includes: vehicle information if visible in frame
- Confidence score indicates identification accuracy
- Description detailed enough to distinguish between people
- Natural language that's clear when read by screen reader

Priority: MUST HAVE
Estimate: 3 points (part of F3)
Dependencies: F3 (AI Descriptions)
Note: This is about prompt optimization, not new functionality
```

```
US-8: Audio Notifications
As a visually impaired user (Linda)
I want to hear event notifications read aloud
So that I'm aware without checking my phone screen

Acceptance Criteria:
- Text-to-speech reads event description aloud
- Volume adjustable in settings
- Option to repeat last notification
- Compatible with screen readers (VoiceOver, TalkBack)
- Notification sound plays before description (alert user)
- Can pause/resume audio playback

Priority: SHOULD HAVE (Phase 2)
Estimate: 8 points
Dependencies: F6 (Dashboard), Mobile app or browser TTS API
Note: May require native mobile app for best experience
```

### System Configuration

```
US-9: Easy Camera Setup
As a homeowner (Sarah)
I want to add my camera quickly and easily
So that I can start monitoring without technical frustration

Acceptance Criteria:
- Form with clear fields: Name, RTSP URL, Username, Password
- Test connection button with live feedback ("Testing..." → "Success!" or error)
- Preview thumbnail appears after successful connection
- Clear error messages for connection failures (with troubleshooting hints)
- Help text explains how to find RTSP URL for common brands
- Save camera configuration persists across restarts

Priority: MUST HAVE
Estimate: 5 points
Dependencies: F1 (Camera Integration), F6 (Dashboard)
```

```
US-10: Configure Motion Detection Zones
As a homeowner (Sarah)
I want to define where motion should be detected
So that I don't get alerts for tree branches or street traffic

Acceptance Criteria:
- Draw rectangle zones on camera preview image
- Multiple zones per camera
- Enable/disable zones independently
- Ignore motion outside defined zones
- Visual indication of active zones on live preview
- Zone configuration saved per camera

Priority: SHOULD HAVE
Estimate: 8 points
Dependencies: F1 (Camera Integration), F2 (Motion Detection), F6 (Dashboard)
```

### Manual Analysis

```
US-11: On-Demand Analysis
As a homeowner (Sarah)
I want to manually analyze what the camera sees right now
So that I can check on something without waiting for motion

Acceptance Criteria:
- "Analyze Now" button on each camera preview
- Bypasses motion detection (works even when motion disabled)
- Same AI processing as automatic triggers
- Result appears in event timeline
- Processing indicator shows "Analyzing..." state
- Works from mobile dashboard

Priority: SHOULD HAVE
Estimate: 3 points
Dependencies: F3 (AI Descriptions), F6 (Dashboard)
```

---

## Jobs to Be Done Framework

### Main Job: "Help me understand what's happening in my video feeds in real-time"

**When** I notice motion or want to check my property...

**I want to** quickly understand what's happening without watching video...

**So I can** make informed decisions and take appropriate action...

**Because** my time is valuable and I need actionable information, not raw footage.

### Functional Jobs

1. **Detect meaningful events** - Identify when something important happens
2. **Describe in natural language** - Understand what's happening without seeing it
3. **Alert appropriately** - Notify me when I need to know, not constantly
4. **Review history** - Find and review past events easily
5. **Trigger automations** - Respond automatically based on what's seen

### Emotional Jobs

1. **Feel secure** - Know my property is being monitored intelligently
2. **Reduce anxiety** - Trust the system to alert for real threats
3. **Maintain control** - Customize system to my specific needs
4. **Feel empowered** - Act on information rather than feeling helpless
5. **Gain independence** (accessibility) - Understand environment without assistance

### Social Jobs

1. **Be a responsible homeowner** - Protect property and family
2. **Be a good neighbor** - Retrieve packages quickly, maintain security
3. **Be tech-savvy** (Marcus) - Show off smart home capabilities
4. **Maintain independence** (Linda) - Live independently despite disability

---

[← Previous: Overview & Goals](./01-overview-goals.md) | [Next: Functional Requirements →](./03-functional-requirements.md)
