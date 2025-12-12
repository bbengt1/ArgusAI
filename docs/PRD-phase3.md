# ArgusAI - Phase 3 PRD

**Author:** Brent
**Date:** 2025-12-05
**Version:** 1.0

---

## Executive Summary

Phase 3 transforms the ArgusAI from snapshot-based event descriptions to video-aware analysis. By leveraging motion clips from UniFi Protect, the system will generate richer, more accurate AI descriptions that capture action, narrative, and intent - information fundamentally impossible to derive from single frames.

This phase builds on the UniFi Protect integration completed in Phase 2, extending it to download and analyze motion video clips rather than just event thumbnails.

### What Makes This Special

> **A single frame cannot capture action or narrative.** These are inherently temporal concepts.

The same snapshot of "person at door" could mean:
- Delivery driver dropped package and left
- Visitor knocked and waited
- Someone casing the house, trying door handles

Only video reveals the truth. Phase 3 gives users **configurable analysis depth** - from fast single-frame alerts to rich video-based narratives - with per-camera control over the cost/quality trade-off.

---

## Project Classification

**Technical Type:** Full-stack web application (Python FastAPI + Next.js)
**Domain:** Home security / AI vision analysis
**Complexity:** Medium-High (video processing, multi-provider AI, real-time events)
**Field Type:** Brownfield (extending existing Phase 1 + Phase 2 codebase)

### Prior Work

- **Phase 1:** Core event detection system with RTSP/USB cameras, motion detection, AI descriptions (single snapshot), alert rules, dashboard
- **Phase 2:** UniFi Protect integration with controller management, camera discovery, smart detection events, doorbell support, multi-camera correlation

---

## Success Criteria

### Primary Success Metrics

1. **Description Quality Improvement**
   - Users report AI descriptions are "more accurate" and "tell the full story"
   - Reduction in ambiguous descriptions ("motion detected", "person present")
   - Descriptions include temporal information (direction, action, sequence)

2. **User Control Over Cost/Quality**
   - Users can configure analysis mode per camera
   - Cost estimates visible before configuration
   - No surprise AI API costs

3. **Operational Reliability**
   - Video clip downloads succeed >99% of the time
   - Graceful fallback when video analysis fails
   - Clear visibility into AI usage and costs

### What "Done" Looks Like

- User configures front door camera for `video_native` mode
- Motion event triggers clip download from Protect
- AI analyzes video and returns: "Delivery driver in brown uniform arrived, placed package on doorstep, took photo, and departed toward street"
- User sees description with confidence indicator and cost tracking

---

## Product Scope

### MVP - Minimum Viable Product

**Epic P3-1: Motion Clip Download Infrastructure**
- Download motion clips from UniFi Protect API
- Temporary storage management for clips
- Error handling and retry logic for failed downloads
- Integration with existing Protect event pipeline

**Epic P3-2: Multi-Frame Analysis Mode**
- Extract key frames from video clips (3-5 frames)
- Frame selection algorithm (evenly spaced initially)
- Update AI service to send multiple images
- Mode-specific prompts optimized for frame sequences
- Support across all AI providers (OpenAI, Claude, Gemini, Grok)

**Epic P3-3: Analysis Mode Configuration**
- Add `analysis_mode` field to Camera model
- Three modes: `single_frame`, `multi_frame`, `video_native`
- Per-camera configuration UI in settings
- Mode descriptions and trade-off explanations
- Automatic fallback chain (video_native → multi_frame → single_frame)

### Growth Features (Post-MVP)

**Epic P3-4: Native Video Analysis**
- Send full video clips to providers that support it (GPT-4o, Gemini)
- Video format conversion if needed
- Provider capability detection and routing

**Epic P3-5: Audio Analysis for Doorbells**
- Extract audio from doorbell event clips
- Transcribe conversations/sounds
- Include audio context in AI descriptions
- "Doorbell rang, person said 'Amazon delivery'"

**Epic P3-6: Confidence Scoring & Quality Indicators**
- AI returns confidence score with description
- Detect vague/uncertain descriptions
- Flag low-confidence events for review
- Option to re-analyze with higher-quality mode

**Epic P3-7: Cost Monitoring Dashboard**
- Track AI usage per camera, per day, per provider
- Show estimated vs actual costs
- Daily/monthly cost caps with alerts
- Usage trends and projections

### Vision Features (Future)

- Historical context awareness ("Same person as yesterday")
- Daily activity digests with natural language summaries
- Searchable video archive by AI description content
- Behavioral anomaly detection
- User feedback loop improving AI prompts over time

---

## Functional Requirements

### Video Clip Management

- **FR1:** System can download motion clips from UniFi Protect for any event
- **FR2:** System stores clips temporarily during analysis
- **FR3:** System automatically cleans up clips after successful analysis
- **FR4:** System retries failed clip downloads with exponential backoff
- **FR5:** System handles clip download failures gracefully with fallback to snapshot

### Frame Extraction

- **FR6:** System can extract multiple frames from video clips
- **FR7:** System selects frames at configurable intervals (e.g., evenly spaced)
- **FR8:** System can extract 3-10 frames per clip based on configuration
- **FR9:** System filters out blurry or empty frames when possible

### Multi-Image AI Analysis

- **FR10:** AI service accepts multiple images for a single analysis request
- **FR11:** AI service uses mode-specific prompts optimized for frame sequences
- **FR12:** AI service supports multi-image across all configured providers
- **FR13:** System tracks token/cost usage for multi-image requests

### Analysis Mode Configuration

- **FR14:** Each camera has a configurable analysis mode setting
- **FR15:** Users can choose between single_frame, multi_frame, and video_native modes
- **FR16:** UI displays mode descriptions, trade-offs, and estimated costs
- **FR17:** System applies configured mode when processing events from that camera
- **FR18:** System falls back to simpler modes if configured mode fails

### Native Video Analysis (Growth)

- **FR19:** System can send video clips directly to video-capable AI providers
- **FR20:** System detects which providers support video input
- **FR21:** System converts video format if provider requires specific format
- **FR22:** System handles video size/duration limits per provider

### Audio Analysis (Growth)

- **FR23:** System can extract audio track from video clips
- **FR24:** System can transcribe audio using speech-to-text
- **FR25:** System includes audio context in AI description prompt
- **FR26:** System handles clips with no audio gracefully

### Confidence Scoring (Growth)

- **FR27:** AI service returns confidence score with each description
- **FR28:** System detects vague or uncertain descriptions
- **FR29:** Low-confidence events are flagged in the dashboard
- **FR30:** Users can trigger re-analysis with higher-quality mode
- **FR31:** Confidence scores are stored with events for analytics

### Cost Monitoring (Growth)

- **FR32:** System tracks AI API usage per request
- **FR33:** System aggregates usage by camera, day, and provider
- **FR34:** Dashboard displays current usage and costs
- **FR35:** Users can set daily/monthly cost caps
- **FR36:** System alerts users when approaching cost limits
- **FR37:** System can pause AI analysis when cap is reached

### Event Display Updates

- **FR38:** Event cards show which analysis mode was used
- **FR39:** Event cards can display key frames used for analysis (optional)
- **FR40:** Event cards show confidence indicator when available
- **FR41:** Timeline supports filtering by analysis mode

---

## Non-Functional Requirements

### Performance

- **NFR1:** Clip download completes within 10 seconds for typical motion events
- **NFR2:** Frame extraction completes within 2 seconds for 10-second clips
- **NFR3:** Multi-frame AI analysis adds no more than 3x latency vs single-frame
- **NFR4:** Video analysis queue processes events within 30 seconds under normal load

### Reliability

- **NFR5:** Clip download retries up to 3 times with exponential backoff
- **NFR6:** Failed video analysis falls back to snapshot analysis
- **NFR7:** Temporary clip storage is cleaned up within 1 hour of analysis completion
- **NFR8:** System continues processing other events if one clip download fails

### Storage

- **NFR9:** Temporary clip storage does not exceed 1GB under normal operation
- **NFR10:** Clips are stored in configurable location (default: system temp directory)
- **NFR11:** Clip cleanup runs automatically on schedule and after each analysis

### Cost Control

- **NFR12:** Cost estimates are accurate within 20% of actual costs
- **NFR13:** Cost caps are enforced in real-time (not retroactively)
- **NFR14:** Usage data is retained for at least 90 days for analysis

---

## User Experience Principles

### Mode Selection UX

The analysis mode selector should make trade-offs clear:

| Mode | Quality | Speed | Cost | Best For |
|------|---------|-------|------|----------|
| Single Frame | Basic | Fastest | Lowest | High-volume, low-priority cameras |
| Multi-Frame | Good | Moderate | Moderate | Default for most cameras |
| Video Native | Best | Slower | Higher | Critical cameras (front door, etc.) |

### Progressive Disclosure

- Default to `multi_frame` for new cameras (balanced choice)
- Show cost estimates only when user expands advanced settings
- Confidence scores visible but not prominent unless low

### Error Communication

- Clear messages when clip download fails: "Couldn't retrieve video clip - using snapshot instead"
- Cost warnings before they become hard stops
- Explanation when falling back to simpler mode

---

## Technical Constraints

### UniFi Protect API

- Motion clips available via uiprotect library (to be confirmed via spike)
- Clips are MP4 format with H.264 video
- Typical clip duration: 10-30 seconds
- Authentication reuses existing controller credentials

### AI Provider Capabilities

| Provider | Multi-Image | Video | Audio |
|----------|-------------|-------|-------|
| OpenAI GPT-4o | Yes | Yes | TBD |
| Anthropic Claude | Yes | No | No |
| Google Gemini | Yes | Yes | TBD |
| xAI Grok | Yes | TBD | TBD |

### Existing Infrastructure

- Event processing pipeline exists (Phase 1)
- Protect integration exists (Phase 2)
- AI fallback chain exists (Phase 2)
- OpenCV/PyAV available for video processing

---

## Implementation Planning

### Epic Breakdown Required

Requirements will be decomposed into epics and stories following BMad Method.

**Suggested Epic Sequence:**

1. **P3-1: Motion Clip Download** - Foundation, must be first
2. **P3-2: Multi-Frame Analysis** - Core improvement, depends on P3-1
3. **P3-3: Analysis Mode Config** - User control, can parallel with P3-2
4. **P3-4: Video Native Mode** - Enhancement, depends on P3-1 and P3-2
5. **P3-5: Audio Analysis** - Enhancement, depends on P3-1
6. **P3-6: Confidence Scoring** - Polish, can be later
7. **P3-7: Cost Monitoring** - Operations, can be later

**Next Step:** Run `workflow create-epics-and-stories` to create the implementation breakdown.

---

## References

- Product Brief (Phase 1): docs/product-brief.md
- PRD (Phase 1): docs/prd.md
- PRD (Phase 2): docs/PRD-phase2.md
- Architecture: docs/architecture.md
- Brainstorming Session: docs/brainstorming-session-results-2025-12-05.md

---

## Open Questions (To Resolve via Spike)

1. How does uiprotect library expose motion clips? REST endpoint or method?
2. What's the typical clip file size for 10-30 second events?
3. Does GPT-4o video input require specific format/resolution?
4. What's Gemini's video duration limit?
5. Can we extract audio separately or is it embedded in video analysis?

---

_This PRD captures the Phase 3 vision for ArgusAI - transforming from snapshot-based to video-aware AI descriptions that capture the full story of security events._

_Created through collaborative discovery between Brent and AI facilitator._
