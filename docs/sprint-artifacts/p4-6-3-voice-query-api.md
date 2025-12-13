# Story P4-6.3: Voice Query API

**Epic:** P4-6 Voice Assistant Integration (Growth)
**Status:** drafted
**Created:** 2025-12-12
**Story Key:** p4-6-3-voice-query-api

---

## User Story

**As a** smart home user with voice assistants (Siri, Alexa, Google)
**I want** to ask natural language questions about my security cameras
**So that** I can get spoken summaries without looking at a screen

---

## Background & Context

Stories P4-6.1 and P4-6.2 established HomeKit motion sensors for Apple Home automations. This story adds a voice query API that can power voice assistant integrations, enabling queries like:

- "What's happening at the front door?"
- "Any activity this morning?"
- "What did the cameras see today?"
- "Was there anyone at the back yard in the last hour?"

The API returns natural language text optimized for text-to-speech (TTS), which can be used by:
- Siri Shortcuts
- Alexa Skills
- Google Assistant Actions
- Custom voice integrations

---

## Acceptance Criteria

### AC1: Query Endpoint
- [ ] POST `/api/v1/voice/query` accepts natural language questions
- [ ] Request body: `{ "query": "string", "camera_id": "optional string" }`
- [ ] Response: `{ "response": "string", "events_found": int, "time_range": {...} }`
- [ ] Response text is optimized for spoken output (no URLs, simple sentences)

### AC2: Time-Based Query Parsing
- [ ] Parse relative time expressions:
  - "today" → since midnight
  - "this morning" → 6 AM to 12 PM
  - "this afternoon" → 12 PM to 6 PM
  - "this evening" → 6 PM to 10 PM
  - "tonight" → 6 PM to midnight
  - "last hour" → past 60 minutes
  - "last X hours/minutes" → past X time units
  - "yesterday" → previous day midnight to midnight
- [ ] Default to "last hour" if no time specified
- [ ] Return parsed time range in response for transparency

### AC3: Camera-Specific Queries
- [ ] Parse camera names from query ("front door", "back yard", "garage")
- [ ] Match camera names case-insensitively and with partial matching
- [ ] Filter events to specific camera when mentioned
- [ ] Handle "all cameras" or no camera specification

### AC4: Response Generation
- [ ] Generate natural language summary of events
- [ ] Format for text-to-speech (short sentences, no abbreviations)
- [ ] Include key details: count, camera(s), main objects detected
- [ ] Examples:
  - "I found 3 events at the front door today. A person was seen twice and a package was delivered once."
  - "No activity detected at the back yard in the last hour."
  - "There were 12 events across all cameras this morning, mostly people and vehicles."

### AC5: Ambiguous Query Handling
- [ ] Handle vague queries gracefully ("anything interesting?")
- [ ] Provide helpful response when no events found
- [ ] Clarify if query couldn't be understood

### AC6: Error Handling
- [ ] Return 400 for empty or malformed queries
- [ ] Return helpful error messages in spoken format
- [ ] Handle database errors gracefully

### AC7: Testing
- [ ] Unit tests for time parsing
- [ ] Unit tests for camera name matching
- [ ] Unit tests for response generation
- [ ] Integration test for full query flow

---

## Technical Implementation

### Task 1: Create Voice Query Service
**File:** `backend/app/services/voice_query_service.py`
- `VoiceQueryService` class with methods:
  - `parse_query(query: str) -> ParsedQuery`
  - `execute_query(parsed: ParsedQuery) -> QueryResult`
  - `generate_response(result: QueryResult) -> str`
- `ParsedQuery` dataclass with time_range, camera_filter, query_type
- `QueryResult` dataclass with events, count, cameras_involved

### Task 2: Implement Time Parser
**File:** `backend/app/services/voice_query_service.py`
- `parse_time_expression(text: str) -> Tuple[datetime, datetime]`
- Handle all relative time expressions from AC2
- Use regex patterns for "last X hours/minutes"
- Return (start_time, end_time) tuple

### Task 3: Implement Camera Name Matcher
**File:** `backend/app/services/voice_query_service.py`
- `match_camera_name(query: str, cameras: List[Camera]) -> Optional[Camera]`
- Fuzzy matching using camera name keywords
- Handle common synonyms ("front door" matches "Front Door Camera")
- Return None for "all cameras" queries

### Task 4: Implement Response Generator
**File:** `backend/app/services/voice_query_service.py`
- `generate_spoken_response(events: List[Event], time_desc: str, camera_name: str) -> str`
- Group events by detected objects
- Generate TTS-friendly sentences
- Handle zero events case

### Task 5: Create API Endpoint
**File:** `backend/app/api/v1/voice.py`
- `POST /api/v1/voice/query` endpoint
- Request/response models with Pydantic
- Wire up VoiceQueryService
- Add to router in `api/v1/__init__.py`

### Task 6: Write Unit Tests
**File:** `backend/tests/test_services/test_voice_query_service.py`
- Test time parsing for all expressions
- Test camera name matching
- Test response generation
- Test edge cases (no events, ambiguous queries)

---

## Dependencies

- **Story P4-6.1 & P4-6.2** - HomeKit integration (completed)
- **Event model** - Query events from database
- **Camera model** - Match camera names

---

## Out of Scope

- Direct Siri/Alexa/Google integration (requires app store deployment)
- Voice input recognition (API receives text)
- Multi-language support (English only)
- Historical trends ("more activity than usual?")

---

## Definition of Done

- [ ] All acceptance criteria verified
- [ ] Unit tests passing
- [ ] API endpoint documented
- [ ] Response text sounds natural when read aloud
- [ ] No security vulnerabilities (auth required for endpoint)
- [ ] Code review completed
