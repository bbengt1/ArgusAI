# Story P9-5.6: Build n8n Monitoring Dashboard and Approval Gates

Status: done

## Story

As a **developer**,
I want **to monitor pipeline status and approve changes before merge**,
So that **automation doesn't proceed without human oversight when needed**.

## Acceptance Criteria

1. **AC5.6.1:** Given n8n workflows are running, when I view dashboard, then I see active workflows and status

2. **AC5.6.2:** Given dashboard is open, when I view metrics, then I see success rate and average duration

3. **AC5.6.3:** Given workflow reaches approval gate, when human review needed, then notification is sent

4. **AC5.6.4:** Given approval notification sent, when I click approve link, then workflow resumes

5. **AC5.6.5:** Given approval notification sent, when I click reject link, then workflow is cancelled

6. **AC5.6.6:** Given approval action taken, when workflow updates, then approval is logged with timestamp and approver

## Tasks / Subtasks

- [x] Task 1: Create n8n workflow with approval gate (AC: 5.6.3, 5.6.4, 5.6.5)
  - [x] Create `n8n/workflows/bmad-pipeline-with-approval.json` workflow template
  - [x] Add Wait node configured for webhook resume
  - [x] Add notification node (Slack/Discord/webhook)
  - [x] Create approve webhook endpoint
  - [x] Create reject webhook endpoint
  - [x] Test approval/rejection flow

- [x] Task 2: Integrate approval gate into BMAD pipeline (AC: 5.6.3-5.6.6)
  - [x] Create `bmad-pipeline-with-approval.json` with full approval gate
  - [x] Add PR creation before approval gate
  - [x] Configure notification with approve/reject links
  - [x] Add workflow resume logic after approval
  - [x] Add workflow cancellation on rejection

- [x] Task 3: Create monitoring dashboard workflow (AC: 5.6.1, 5.6.2)
  - [x] Create `n8n/workflows/monitoring-dashboard.json` workflow
  - [x] Add webhook trigger for on-demand metrics
  - [x] Query n8n API for execution statistics
  - [x] Calculate success rate and average duration
  - [x] Output metrics in structured format

- [x] Task 4: Implement approval logging (AC: 5.6.6)
  - [x] Add Code node to log approval actions
  - [x] Include timestamp, approver, and action type
  - [x] Store logs in workflow data
  - [x] Add audit trail output option

- [x] Task 5: Create documentation for approval gates (AC: 5.6.1-5.6.6)
  - [x] Document approval workflow setup
  - [x] Document notification configuration
  - [x] Document webhook URL patterns
  - [x] Create example: full approval flow

## Dev Notes

### Architecture Alignment

From tech-spec-epic-P9-5.md:

**Approval Gate Implementation:**
- Use n8n's built-in Wait node with webhook resume
- Approval gate pauses workflow execution
- External webhook (approve/reject) resumes workflow
- Timeout after 7 days with warning at 5 days

**Workflow Endpoints:**
```
/webhook/pr-ready       # PR created, triggers approval gate
/webhook/approve/{id}   # Human approval resumes workflow
/webhook/reject/{id}    # Human rejection cancels workflow
```

**Monitoring Dashboard:**
- Use n8n's execution monitoring APIs
- Track: active workflows, success/failure rates, queue depth
- Calculate average execution duration
- Display recent executions with status

### n8n Approval Gate Structure

```json
{
  "name": "Approval Gate",
  "nodes": [
    {
      "name": "Wait for Approval",
      "type": "n8n-nodes-base.wait",
      "parameters": {
        "resume": "webhook",
        "webhookSuffix": "={{$executionId}}"
      }
    },
    {
      "name": "Send Notification",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#dev-approvals",
        "text": "Approve: {{$env.N8N_URL}}/webhook/approve/{{$executionId}}\nReject: {{$env.N8N_URL}}/webhook/reject/{{$executionId}}"
      }
    }
  ]
}
```

### Project Structure

```
n8n/
├── workflows/
│   ├── claude-code-basic.json       # (P9-5.4)
│   ├── claude-code-with-git.json    # (P9-5.4)
│   ├── bmad-create-story.json       # (P9-5.5)
│   ├── bmad-story-context.json      # (P9-5.5)
│   ├── bmad-dev-story.json          # (P9-5.5)
│   ├── bmad-pipeline.json           # (P9-5.5) - update with approval
│   ├── bmad-pipeline-with-approval.json  # Full pipeline with approval gate
│   ├── monitoring-dashboard.json    # Metrics and monitoring
│   └── README.md
├── credentials/
│   └── README.md
└── README.md
```

### Key Implementation Notes

1. **Wait Node Configuration:**
   - `resume`: "webhook" - resumes on webhook call
   - `webhookSuffix`: execution ID for unique endpoint
   - Timeout: 7 days (604800000ms)

2. **Notification Content:**
   - PR URL/details
   - Approve link with execution ID
   - Reject link with execution ID
   - Summary of changes

3. **Approval Logging:**
   - Timestamp of action
   - Approver identifier (from webhook payload)
   - Action type (approve/reject)
   - Execution ID for traceability

4. **Monitoring Metrics:**
   - Active workflow count
   - Success rate (24h, 7d, 30d)
   - Average execution duration
   - Failed workflows list
   - Queue depth

### Prerequisites

- n8n instance deployed and running (Story P9-5.3 - done)
- BMAD workflows created (Story P9-5.5 - done)
- Notification webhook configured (Slack/Discord)

### Testing Strategy

**Manual Tests:**
- Trigger pipeline that reaches approval gate
- Verify notification sent with correct links
- Click approve link, verify workflow resumes
- Click reject link, verify workflow cancelled
- Check metrics on dashboard

**Integration Tests:**
- Full pipeline with approval flow
- Timeout handling verification
- Logging verification

### Learnings from Previous Stories

**From Story P9-5.5 (Create n8n BMAD Workflow Integration):**

- Master orchestration workflow pattern works well
- Conditional logic for stage progression
- Failure notification via webhook
- Git status tracking for change detection

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P9-5.md#P9-5.6] - Acceptance criteria and implementation details
- [Source: docs/epics-phase9.md#Story-P9-5.6] - Story definition
- [Source: docs/sprint-artifacts/tech-spec-epic-P9-5.md#Approval-Gate] - Approval gate design

## Dev Agent Record

### Context Reference

- [Story Context](p9-5-6-build-n8n-monitoring-dashboard-and-approval-gates.context.xml) - Generated 2025-12-24

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created bmad-pipeline-with-approval.json with full approval gate integration
- Implemented Wait node with 7-day timeout for human approval
- Added PR creation and merge steps to pipeline
- Created monitoring-dashboard.json for execution metrics
- Dashboard calculates success rates for 24h/7d/30d periods
- Tracks active workflows, queue depth, and failed executions
- Updated README with comprehensive approval gate documentation

### File List

- `n8n/workflows/bmad-pipeline-with-approval.json` - Full pipeline with approval gate
- `n8n/workflows/monitoring-dashboard.json` - Metrics and monitoring workflow
- `n8n/workflows/README.md` - Updated with approval gate and monitoring docs

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-24 | Story drafted from Epic P9-5 and tech spec |
| 2025-12-24 | Implemented all tasks, created approval gate and monitoring workflows |
