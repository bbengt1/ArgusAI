# Story P9-5.5: Create n8n BMAD Workflow Integration

Status: done

## Story

As a **developer**,
I want **n8n to execute BMAD method workflows**,
So that **story creation and development follow our methodology**.

## Acceptance Criteria

1. **AC5.5.1:** Given n8n receives story creation trigger, when BMAD node executes, then create-story skill is invoked

2. **AC5.5.2:** Given BMAD workflow runs, when create-story completes, then story file path is extracted from output

3. **AC5.5.3:** Given story is created, when story-context node runs, then context XML is generated

4. **AC5.5.4:** Given context is ready, when dev-story node runs, then implementation begins

5. **AC5.5.5:** Given BMAD workflow fails, when error occurs, then failure is logged and admin notified

## Tasks / Subtasks

- [x] Task 1: Create n8n workflow for BMAD story creation (AC: 5.5.1, 5.5.2)
  - [x] Create `n8n/workflows/bmad-create-story.json` workflow
  - [x] Add webhook trigger for story creation requests
  - [x] Add Execute Command node for create-story skill
  - [x] Add Code node to extract story file path from output
  - [x] Store story details in workflow data for chaining

- [x] Task 2: Create n8n workflow for story context generation (AC: 5.5.3)
  - [x] Create `n8n/workflows/bmad-story-context.json` workflow
  - [x] Add trigger from create-story workflow completion
  - [x] Add Execute Command node for story-context skill
  - [x] Parse context XML generation output
  - [x] Verify context file was created

- [x] Task 3: Create n8n workflow for story implementation (AC: 5.5.4)
  - [x] Create `n8n/workflows/bmad-dev-story.json` workflow
  - [x] Add trigger from story-context workflow completion
  - [x] Add Execute Command node for dev-story skill
  - [x] Configure extended timeout (30 minutes for complex implementations)
  - [x] Capture implementation output and file changes

- [x] Task 4: Create master orchestration workflow (AC: 5.5.1-5.5.4)
  - [x] Create `n8n/workflows/bmad-pipeline.json` master workflow
  - [x] Chain: create-story → story-context → dev-story
  - [x] Add conditional logic for workflow stage progression
  - [x] Include git status checks between stages

- [x] Task 5: Implement error handling and notifications (AC: 5.5.5)
  - [x] Add error detection in each workflow stage
  - [x] Configure failure notification (Slack/Discord/webhook)
  - [x] Add retry logic for transient failures
  - [x] Log all workflow executions with details

- [x] Task 6: Create documentation for BMAD n8n integration (AC: 5.5.1-5.5.5)
  - [x] Document workflow import process
  - [x] Document trigger configuration
  - [x] Document notification setup
  - [x] Create example: full story lifecycle

## Dev Notes

### Architecture Alignment

From tech-spec-epic-P9-5.md:

**BMAD Workflow Execution via Claude Code:**
- BMAD skills are invoked via Claude Code CLI
- Pattern: `claude --skill bmad:bmm:workflows:create-story`
- Parse output for story file path and content
- Chain workflows: create-story → story-context → dev-story
- Handle workflow failures gracefully

**Workflow Chain:**
```
GitHub Issue/Manual Trigger → create-story → story-context → dev-story → PR Creation → Approval
```

### n8n Workflow Structure (from tech spec)

```json
{
  "name": "BMAD Full Pipeline",
  "nodes": [
    {
      "name": "Story Creation Trigger",
      "type": "n8n-nodes-base.webhook"
    },
    {
      "name": "Create Story",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "claude --skill bmad:bmm:workflows:create-story"
      }
    },
    {
      "name": "Extract Story Path",
      "type": "n8n-nodes-base.code"
    },
    {
      "name": "Generate Context",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "claude --skill bmad:bmm:workflows:story-context"
      }
    },
    {
      "name": "Implement Story",
      "type": "n8n-nodes-base.executeCommand",
      "parameters": {
        "command": "claude --skill bmad:bmm:workflows:dev-story"
      }
    }
  ]
}
```

### Project Structure

```
n8n/
├── workflows/
│   ├── claude-code-basic.json       # (P9-5.4) Basic prompt execution
│   ├── claude-code-with-git.json    # (P9-5.4) With git status
│   ├── bmad-create-story.json       # Create story workflow
│   ├── bmad-story-context.json      # Generate context workflow
│   ├── bmad-dev-story.json          # Implement story workflow
│   ├── bmad-pipeline.json           # Full pipeline orchestration
│   └── README.md
├── credentials/
│   └── README.md
└── README.md
```

### Key Implementation Notes

1. **Skill Invocation:**
   - Use `claude "prompt" --no-input` for inline prompts
   - Use `claude --skill <skill-name>` for BMAD workflows
   - Example: `claude --skill bmad:bmm:workflows:create-story`

2. **Output Parsing:**
   - create-story outputs story file path
   - story-context outputs context XML path
   - dev-story outputs implementation details and file changes

3. **Timeout Configuration:**
   - create-story: 10 minutes (600000ms)
   - story-context: 5 minutes (300000ms)
   - dev-story: 30 minutes (1800000ms) - complex implementations

4. **Error Detection:**
   - Non-zero exit code
   - "Error:" in stderr
   - Missing expected output files

5. **Notification Options:**
   - Slack webhook
   - Discord webhook
   - Generic HTTP webhook

### Prerequisites

- n8n instance deployed and running (Story P9-5.3 - done)
- Claude Code CLI with BMAD workflows (Story P9-5.4 - done)
- ANTHROPIC_API_KEY environment variable set
- Notification webhook URLs configured

### Testing Strategy

**Manual Tests:**
- Import workflow into n8n
- Trigger create-story with known epic
- Verify story file created
- Verify context XML generated
- Verify implementation proceeds

**Integration Tests:**
- Full pipeline from trigger to PR
- Error handling verification
- Notification delivery

### Learnings from Previous Stories

**From Story P9-5.4 (Create n8n Claude Code Integration):**

- Execute Command node works well for Claude Code CLI
- Output parsing via Code node extracts structured data
- Git status tracking helps verify file changes
- Retry logic handles transient failures
- 10-minute timeout sufficient for most operations

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P9-5.md#P9-5.5] - Acceptance criteria and implementation details
- [Source: docs/epics-phase9.md#Story-P9-5.5] - Story definition
- [Source: docs/sprint-artifacts/tech-spec-epic-P9-5.md#n8n-Workflow-Story-Creation] - Workflow JSON example

## Dev Agent Record

### Context Reference

- [Story Context](p9-5-5-create-n8n-bmad-workflow-integration.context.xml) - Generated 2025-12-24

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created four n8n workflow templates for BMAD integration
- bmad-create-story.json executes create-story skill with output parsing
- bmad-story-context.json generates context XML from story files
- bmad-dev-story.json implements stories with git status tracking (30min timeout)
- bmad-pipeline.json orchestrates full story lifecycle with conditional logic
- Added failure notification via configurable webhook
- Updated README with comprehensive BMAD workflow documentation

### File List

- `n8n/workflows/bmad-create-story.json` - Story creation workflow
- `n8n/workflows/bmad-story-context.json` - Context generation workflow
- `n8n/workflows/bmad-dev-story.json` - Story implementation workflow
- `n8n/workflows/bmad-pipeline.json` - Full pipeline orchestration
- `n8n/workflows/README.md` - Updated with BMAD documentation

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-24 | Story drafted from Epic P9-5 and tech spec |
| 2025-12-24 | Implemented all tasks, created BMAD workflow templates |
