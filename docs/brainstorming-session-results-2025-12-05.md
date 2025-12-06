# Brainstorming Session Results

**Session Date:** 2025-12-05
**Facilitator:** Brainstorming Facilitator (Claude)
**Participant:** Brent

## Session Start

**Approach Selected:** AI-Recommended Techniques

**Planned Techniques:**
1. First Principles Thinking (creative) - 15-20 min
2. Question Storming (deep) - 10-15 min
3. SCAMPER Method (structured) - 15-20 min

**Session Focus:** Improving AI description quality by moving from single-frame snapshots to motion clips downloaded from UniFi Protect.

## Executive Summary

**Topic:** Improving AI description quality through video clip analysis

**Session Goals:** Explore how to leverage UniFi Protect motion clips instead of single snapshots to generate richer, more accurate AI descriptions of security events.

**Techniques Used:** First Principles Thinking, Question Storming, SCAMPER Method

**Total Ideas Generated:** 46+ (5 from First Principles, 39 questions, 36 from SCAMPER)

### Key Themes Identified:

1. **Temporal information is fundamental** - Single frames cannot capture action, narrative, or intent
2. **Configuration-driven flexibility** - Users need control over cost/quality trade-offs
3. **Layered approach** - Quick alerts first, detailed analysis second
4. **Context enrichment** - Historical data, cross-camera correlation, and metadata improve descriptions
5. **Operational concerns matter** - Error handling, cost monitoring, and confidence scoring are critical

## Technique Sessions

### Technique 1: First Principles Thinking

**Duration:** ~15 minutes

**Core Question:** What is the ideal input to give an AI to describe a security event as accurately as possible?

**Fundamental Truths Discovered:**

1. **Video captures temporal information that snapshots cannot:**
   - Direction of movement
   - Speed/velocity
   - Behavior patterns (walking vs. running vs. lurking)
   - Sequence of events (arrived → did something → left)

2. **Video reveals intent and purpose:**
   - Same snapshot can mean completely different things depending on before/after
   - Example: "Person at door" could be delivery driver or someone casing the house

3. **Video resolves ambiguity:**
   - Falling vs. bending to pick something up
   - Dog vs. coyote (movement patterns differ)
   - Waving hello vs. signaling for help

**Problem Analysis - Current System Failures:**
- Poorly timed snapshots (person's back, blurry motion) ✓
- Ambiguous actions (can't tell what they're doing) ✓
- Missing the story (arrival → action → departure) ✓

**Key Realization:**
> A single frame, no matter how well-selected, cannot capture **action** or **narrative**. These are inherently temporal concepts.

**Solution Architecture - Configuration-Driven Flexibility:**

| Mode | Use Case | Trade-off |
|------|----------|-----------|
| single_frame | Legacy/fast alerts | Lowest cost, lowest quality |
| multi_frame | Balanced default | Good quality, moderate cost |
| video_native | Premium analysis | Highest quality, higher cost |

**Ideas Generated:**
1. Three analysis modes - single_frame, multi_frame, video_native
2. Per-camera configuration - high-value cameras get video_native
3. Cost estimation UI - show users estimated cost per mode
4. Quality comparison tool - let users see same event analyzed both ways
5. Automatic fallback - try video_native, fall back to multi_frame if unsupported

---

### Technique 2: Question Storming

**Duration:** ~10 minutes

**Objective:** Map out all unknowns before designing the solution.

#### UniFi Protect API Questions:
1. How does Protect expose motion clips? REST API? WebSocket event with download URL?
2. What video format are the clips in? (MP4, H.264, etc.)
3. What's the typical clip duration? Is it configurable?
4. Can we request a specific time range, or only pre-defined motion events?
5. Are clips available immediately, or is there processing delay?
6. What authentication is needed to download clips?
7. Does the uiprotect Python library support clip downloads?

#### AI Provider Questions:
8. Which providers support native video input? (GPT-4o? Gemini? Claude?)
9. What video formats do they accept?
10. What's the max video duration/file size?
11. How is video priced vs. images? (tokens? seconds? frames?)
12. What's the latency difference between video and multi-image?

#### Architecture Questions:
13. Where do we store downloaded clips? Temporary? Persistent?
14. How do we handle clip download failures?
15. Should clip analysis be synchronous or queued?

#### Reliability & Error Handling:
16. How to handle AI API call failures? (Retry? Fallback provider? Queue for later?)
17. What's the retry strategy for transient failures vs. permanent failures?
18. Should we cache successful descriptions to avoid re-processing?

#### Quality & Confidence:
19. How do we handle uncertain AI descriptions? (Confidence scores? Flag for review?)
20. Can we detect when the AI says "I can't tell" or gives a vague answer?
21. Should we re-analyze with a different mode if confidence is low?
22. How do we measure description quality over time?

#### Cost & Usage Management:
23. How do we monitor AI usage? (Per camera? Per day? Per provider?)
24. How do we manage token usage? (Budgets? Alerts? Hard limits?)
25. Should there be a daily/monthly cost cap?
26. How do we show users their current usage and projected costs?

#### Context & Memory:
27. Should the AI have context about previous events? ("Same person as 5 minutes ago")
28. How much historical context is useful vs. noise?
29. Can we use Protect's face detection to provide "known person" context?
30. Should we maintain per-camera context? ("This camera often sees the mail carrier at 2pm")

#### Multi-Frame Specific:
31. How do we select the "best" frames from a clip? (Sharpness? Motion blur? Face visibility?)
32. How many frames is optimal? 3? 5? 10?
33. Should frames be evenly spaced or intelligently selected?

#### Video Native Specific:
34. Do we send the whole clip or trim to key moments?
35. What if the clip is 30 seconds but the action is 3 seconds?
36. Should we include audio? (Doorbell voice, car sounds, dog barking)

#### User Experience:
37. How do we show users the difference between modes?
38. Should users see the frames/video that was analyzed?
39. How do we explain when a description is uncertain?

**Total Questions Generated:** 39

---

### Technique 3: SCAMPER Method

**Duration:** ~15 minutes

**Objective:** Systematically generate concrete solutions using 7 creative lenses.

#### S - Substitute
| Current | Substitute With | Benefit |
|---------|-----------------|---------|
| Single snapshot | Multiple frames | Captures action sequence |
| Single snapshot | Video clip | Full temporal context |
| Protect thumbnail | Self-extracted frames | Better quality control |
| Single AI call | Tiered analysis | Cost/quality flexibility |
| Generic prompt | Mode-specific prompts | Better results per mode |
| Synchronous processing | Async queue for video | Better performance |

#### C - Combine
1. Video + Audio → Richer descriptions ("Doorbell rang, person said 'Amazon delivery'")
2. Multiple cameras + same timestamp → Cross-camera tracking
3. Protect smart detection + AI analysis → Pre-filter then describe
4. Historical context + current event → "Same vehicle seen yesterday"
5. User feedback + AI learning → Improve based on corrections
6. Motion metadata + frame selection → Pick peak-action frames

#### A - Adapt
1. From surveillance industry → Clip pre-roll/post-roll (3s before/after motion)
2. From YouTube → Thumbnail generation algorithms for best frame
3. From security monitoring → Tiered alert escalation (uncertain → human review)
4. From dashcams → Extract key moments based on motion intensity
5. From video editing → Scene change detection for distinct "acts"
6. From smart assistants → Natural language summaries ("While away, 3 deliveries arrived")

#### M - Modify/Magnify
1. Magnify prompt → Detailed instructions (clothing, direction, carrying items)
2. Modify event cards → Show key frames used, not just one thumbnail
3. Magnify metadata → Include time, day, weather in AI context
4. Modify alert rules → Trigger on description content ("Alert if 'package'")
5. Magnify confidence → Show score, highlight uncertain descriptions
6. Modify retention → Keep clips longer for interesting events

#### P - Put to Other Uses
1. Activity summaries → Daily digest of events
2. Searchable archive → Search by AI description
3. Behavioral analytics → Detect unusual activity patterns
4. Training data → User-verified descriptions improve models
5. Insurance documentation → Detailed incident reports
6. Pet monitoring → Track pet activity throughout day

#### E - Eliminate
1. Eliminate redundant processing → Skip if no smart detection + minimal motion
2. Eliminate duplicates → Dedupe same-scene analyses
3. Eliminate empty frames → Don't send frames with nothing visible
4. Eliminate vague descriptions → Re-analyze or discard "motion detected"
5. Eliminate manual config → Auto-detect best mode per camera
6. Eliminate storage bloat → Delete clips after successful analysis

#### R - Reverse/Rearrange
1. Reverse trigger → User requests "analyze last 5 minutes"
2. Rearrange priority → Doorbell/front door first, backyard later
3. Reverse feedback → User ratings improve prompts
4. Rearrange pipeline → Quick alert first, background video analysis for detail
5. Reverse storage → Store by default, delete if "nothing interesting"
6. Rearrange UI → Description prominent, thumbnail secondary

**Ideas Generated from SCAMPER:** 36

---

## Idea Categorization

### Immediate Opportunities

_Ideas ready to implement soon - foundational work_

1. **Three analysis modes** (single_frame, multi_frame, video_native) - core architecture
2. **Download motion clips from Protect API** - prerequisite for everything
3. **Multi-frame extraction** from clips (3-5 key frames)
4. **Mode-specific AI prompts** - optimize for each input type
5. **Per-camera analysis mode configuration** - UI settings
6. **Async processing queue** for video analysis - performance

### Future Innovations

_Ideas requiring more development/research_

1. **Native video analysis** with GPT-4o/Gemini - needs provider research
2. **Audio inclusion** for doorbell conversations
3. **Confidence scoring** and uncertain description handling
4. **Cost monitoring dashboard** with usage tracking
5. **Intelligent frame selection** (sharpness, motion intensity)
6. **Quick alert + background detail** pipeline (two-phase analysis)
7. **Cross-camera event correlation** with timestamps

### Moonshots

_Ambitious, transformative concepts_

1. **Historical context awareness** ("Same person as yesterday")
2. **Daily activity digests** with natural language summaries
3. **Searchable video archive** by AI description
4. **Behavioral anomaly detection** ("Unusual activity at 2am")
5. **User feedback loop** improving AI over time
6. **Face recognition integration** with Protect's detection

### Insights and Learnings

_Key realizations from the session_

1. **A single frame cannot capture action or narrative** - These are inherently temporal concepts
2. **The same snapshot can tell completely different stories** - Video reveals intent
3. **Users have different priorities** - Cost vs. quality vs. latency trade-offs vary
4. **80% of improvement may come from multi-frame** - Full video may be overkill for many cases
5. **Operational concerns are as important as features** - Error handling, monitoring, confidence matter

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Download Motion Clips from Protect API

- **Rationale:** Without clip access, nothing else works. This is the foundation for all video-based improvements.
- **Next steps:**
  1. Research uiprotect library for clip download capability
  2. Identify the API endpoint/method for motion clip retrieval
  3. Determine clip format and duration options
  4. Implement clip download service with error handling
  5. Add temporary storage management for downloaded clips
- **Resources needed:** uiprotect library documentation, test Protect controller, local storage for clips

#### #2 Priority: Multi-Frame Extraction + Analysis

- **Rationale:** Works with all current AI providers (GPT-4o, Claude, Gemini), delivers 80% of quality improvement with moderate complexity.
- **Next steps:**
  1. Implement frame extraction from video clips (OpenCV/PyAV)
  2. Build frame selection algorithm (evenly spaced or motion-based)
  3. Update AI service to accept multiple images
  4. Create multi-frame specific prompts ("These frames show a sequence...")
  5. Test with GPT-4o, Claude, Gemini multi-image support
- **Resources needed:** OpenCV/PyAV (already in project), AI provider docs on multi-image limits, test clips

#### #3 Priority: Three Analysis Modes with Per-Camera Config

- **Rationale:** Gives users control over cost/quality trade-off from day one. Different cameras have different importance levels.
- **Next steps:**
  1. Add `analysis_mode` field to Camera model (enum: single_frame, multi_frame, video_native)
  2. Update camera settings UI with mode selector
  3. Add mode descriptions and cost estimates in UI
  4. Route event processing based on camera's configured mode
  5. Implement fallback logic (video_native → multi_frame if unsupported)
- **Resources needed:** Database migration, UI component for mode selection, cost estimation data

## Reflection and Follow-up

### What Worked Well

- First Principles thinking helped identify the core truth: single frames cannot capture action or narrative
- Question Storming surfaced 39 unknowns across 9 categories before designing solutions
- SCAMPER systematically generated 36 concrete ideas across substitution, combination, adaptation, modification, new uses, elimination, and reversal
- The progression from "why video matters" → "what we don't know" → "concrete features" felt logical

### Areas for Further Exploration

- AI provider video capabilities and pricing (GPT-4o vs Gemini vs Claude)
- uiprotect library clip download specifics and limitations
- Optimal frame count and selection algorithms for different scenarios
- Audio processing for doorbell events
- Cross-camera correlation algorithms

### Recommended Follow-up Techniques

- **Technical spike** on uiprotect clip download API
- **Competitive analysis** of how other security systems handle video AI
- **User interviews** to validate priority assumptions

### Questions That Emerged

1. How to handle audio from doorbell events? Can AI transcribe conversations?
2. Can we leverage Protect's face detection for "known person" context?
3. What's the right confidence threshold for flagging uncertain descriptions?
4. How do we measure description quality improvement objectively?
5. What's the cost/benefit of video_native vs multi_frame in practice?

### Next Session Planning

- **Suggested topics:** Technical deep-dive on uiprotect clip API, or AI provider video capability research
- **Recommended timeframe:** After initial spike on clip download
- **Preparation needed:** Document uiprotect findings, gather AI provider pricing/limits

---

_Session facilitated using the BMAD CIS brainstorming framework_
