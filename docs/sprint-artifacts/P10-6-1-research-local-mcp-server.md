# Story P10-6.1: Research Local MCP Server

Status: done

## Story

As a **developer planning AI enhancements for ArgusAI**,
I want **comprehensive research on implementing a local MCP (Model Context Protocol) server**,
So that **future implementation can leverage rich local context (user feedback, known entities, camera patterns) to improve AI event descriptions**.

## Acceptance Criteria

1. **AC-6.1.1:** Given I read the research document, when I understand MCP server patterns, then I know implementation options for ArgusAI (sidecar, embedded, standalone)

2. **AC-6.1.2:** Given the research evaluates hosting options, when I review sidecar vs embedded vs standalone approaches, then trade-offs are clearly documented with recommendations

3. **AC-6.1.3:** Given the research defines context data schema, when I see what data to expose, then I understand entity corrections, feedback history, camera context, and time-of-day pattern structures

4. **AC-6.1.4:** Given the research assesses performance impact, when I review latency estimates, then I know if MCP adds acceptable overhead (<100ms target)

5. **AC-6.1.5:** Given future development begins, when implementation starts, then this research document guides design decisions and answers key architectural questions

## Tasks / Subtasks

- [x] Task 1: Research MCP Specification and SDK (AC: 1, 2)
  - [x] Subtask 1.1: Review Model Context Protocol specification from Anthropic
  - [x] Subtask 1.2: Evaluate mcp-python SDK capabilities and requirements
  - [x] Subtask 1.3: Document core MCP concepts (tools, resources, prompts, context)
  - [x] Subtask 1.4: Identify how MCP integrates with AI providers (Claude, OpenAI, etc.)

- [x] Task 2: Evaluate Hosting Options (AC: 1, 2)
  - [x] Subtask 2.1: Document sidecar approach (separate process, IPC communication)
  - [x] Subtask 2.2: Document embedded approach (within FastAPI backend process)
  - [x] Subtask 2.3: Document standalone approach (independent service)
  - [x] Subtask 2.4: Compare trade-offs: latency, resource usage, deployment complexity
  - [x] Subtask 2.5: Recommend approach for ArgusAI with rationale

- [x] Task 3: Define Context Data Schema (AC: 3)
  - [x] Subtask 3.1: Define user feedback history schema (positive/negative feedback, corrections)
  - [x] Subtask 3.2: Define known entities schema (people, vehicles with attributes)
  - [x] Subtask 3.3: Define entity corrections schema (original vs corrected descriptions)
  - [x] Subtask 3.4: Define camera context schema (location, typical activity patterns)
  - [x] Subtask 3.5: Define time-of-day patterns schema (activity levels by hour)
  - [x] Subtask 3.6: Document how context would enhance AI prompts

- [x] Task 4: Assess Performance Implications (AC: 4)
  - [x] Subtask 4.1: Estimate context lookup latency (target <100ms)
  - [x] Subtask 4.2: Evaluate memory footprint for cached context
  - [x] Subtask 4.3: Consider async vs sync context retrieval
  - [x] Subtask 4.4: Document impact on overall event processing pipeline

- [x] Task 5: Document Implementation Roadmap (AC: 5)
  - [x] Subtask 5.1: Outline phased implementation approach
  - [x] Subtask 5.2: Identify dependencies on existing services
  - [x] Subtask 5.3: Define MVP vs full implementation scope
  - [x] Subtask 5.4: List open questions for future resolution

- [x] Task 6: Compile Research Document
  - [x] Subtask 6.1: Create docs/research/mcp-server-research.md
  - [x] Subtask 6.2: Include architecture diagrams (Mermaid)
  - [x] Subtask 6.3: Add code examples where applicable
  - [x] Subtask 6.4: Review against all acceptance criteria

## Dev Notes

### Architecture Context

This story is **research-only** - no implementation is required. The deliverable is a comprehensive research document that will guide future MCP server implementation.

**Current AI Pipeline Components to Consider:**
- `backend/app/services/ai_service.py` - Multi-provider AI service with fallback chain (OpenAI -> xAI Grok -> Claude -> Gemini)
- `backend/app/services/temporal_context_service.py` - Already generates CLIP embeddings for similarity search
- `backend/app/services/event_processor.py` - Event queue pipeline with <5s p95 latency target
- `backend/app/models/event.py` - Event model with AI description, feedback
- `backend/app/models/feedback.py` - User feedback storage (thumbs up/down, corrections)
- `backend/app/models/entity.py` - Known entities (people, vehicles)

**Key Constraints:**
- MCP server must integrate with existing asyncio-based backend
- Context lookup must not significantly impact event processing latency (<100ms overhead)
- Should work with multiple AI providers, not just Anthropic
- Must fail gracefully - MCP unavailability should not block event processing

### MCP Background

Model Context Protocol (MCP) is Anthropic's protocol for providing structured context to AI models. Key concepts:
- **Tools**: Functions the AI can call to gather information
- **Resources**: Data sources the AI can access
- **Prompts**: Templates for context injection
- **Context**: Structured data that enhances AI understanding

### Potential Context Data Sources

1. **Feedback History**: Recent feedback on similar events (e.g., "User marked 'delivery person' as inaccurate when it was actually a neighbor")
2. **Known Entities**: Registered people and vehicles with attributes (e.g., "John - gray sedan owner, usually arrives 6pm")
3. **Entity Corrections**: Past corrections to entity identification (e.g., "White SUV previously misidentified as van")
4. **Camera Context**: Camera-specific hints (e.g., "Driveway camera - mostly sees vehicles and deliveries")
5. **Time Patterns**: Activity expectations by time of day (e.g., "Weekend mornings typically quiet")

### Project Structure Notes

- Research document should be placed in `docs/research/` directory
- Use Mermaid diagrams for architecture visualization
- Reference existing service implementations for integration points

### Learnings from Previous Story

**From Story P10-5-2 (Status: done)**

- **Documentation Pattern**: Used Mermaid sequence diagrams extensively for visualizing flows - should apply same approach to MCP architecture
- **Swift Code Examples**: Previous story included code examples in documentation - research doc should include Python examples for MCP integration
- **Cross-Referencing**: Successfully referenced OpenAPI spec; MCP research should reference existing AI service implementation
- **Comprehensive Sections**: Good structure with separate sections for each major topic (auth flow, device registration, push tokens, biometrics) - apply similar structure

[Source: docs/sprint-artifacts/P10-5-2-document-mobile-authentication-flow.md#Dev-Agent-Record]

### References

- [Source: docs/PRD-phase10.md#AI-Enhancements]
- [Source: docs/epics-phase10.md#Story-P10-6.1]
- [Source: docs/sprint-artifacts/tech-spec-epic-P10-6.md#Story-P10-6.1]
- [Anthropic MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- Backlog: IMP-016

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/P10-6-1-research-local-mcp-server.context.xml

### Agent Model Used

Claude Opus 4.5

### Debug Log References

- Reviewed MCP specification and Python SDK via web search and documentation fetch
- Analyzed existing ArgusAI services: ai_service.py, context_prompt_service.py, embedding_service.py
- Evaluated hosting options based on latency requirements (<100ms) and existing async architecture
- Designed context schema based on existing models: EventFeedback, RecognizedEntity, EntityEvent

### Completion Notes List

- Created comprehensive MCP server research document at `docs/research/mcp-server-research.md`
- Documented three hosting options (sidecar, embedded, standalone) with trade-off comparison
- **Recommended embedded approach** for ArgusAI due to lowest latency (20-50ms) and simplest deployment
- Defined complete context data schema with Python dataclass examples:
  - FeedbackHistoryContext: Recent feedback, camera accuracy, common corrections
  - KnownEntitiesContext: Matched entity, similar entities, vehicle entities
  - CameraContextInfo: Location hints, typical activity, false positive patterns
  - TimePatternContext: Activity levels, unusual timing detection
- Included performance analysis with latency budget showing <50ms total context gathering
- Provided implementation roadmap with 3 phases:
  - Phase 1 (MVP): MCPContextProvider with feedback and entity context
  - Phase 2: Full context with camera and time patterns
  - Phase 3: Full MCP protocol compliance with mcp package
- Included Python code examples for:
  - MCP server structure using FastMCP
  - MCPContextProvider class with parallel async queries
  - Integration with existing EventProcessor
- Documented open questions for future resolution (caching, conflicting corrections, embedding dimensions)
- All 5 acceptance criteria satisfied in the research document

### File List

**NEW:**
- docs/research/mcp-server-research.md - Comprehensive MCP server research document

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-25 | Story drafted from Epic P10-6 and tech spec |
| 2025-12-25 | Story completed - research document created at docs/research/mcp-server-research.md |
