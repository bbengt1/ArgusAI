# Epic Technical Specification: n8n Development Pipeline

**Epic ID:** P13-5
**Phase:** 13 - Platform Maturity & External Integration
**Priority:** P2
**Generated:** 2025-12-28
**PRD Reference:** docs/PRD-phase13.md
**Epic Reference:** docs/epics-phase13.md

---

## Executive Summary

This epic implements an n8n-based development automation pipeline for ArgusAI. n8n is a workflow automation platform that will orchestrate BMAD workflows (create-story, dev-story, code-review), integrate with GitHub webhooks, and send notifications to Slack/Discord. This accelerates AI-assisted development by automating repetitive pipeline steps.

**Functional Requirements Coverage:** FR33-FR40 (8 requirements)
**Backlog Reference:** FF-027

---

## Architecture Overview

### High-Level Design

```
                             GitHub                    n8n                    Claude Code
                               │                         │                          │
                               │  Webhook: push/PR/issue │                          │
                               │─────────────────────────►                          │
                               │                         │                          │
                               │                 ┌───────▼───────┐                  │
                               │                 │ Webhook Node   │                  │
                               │                 │ Parse payload   │                  │
                               │                 └───────┬───────┘                  │
                               │                         │                          │
                               │                 ┌───────▼───────┐                  │
                               │                 │ Route by Event │                  │
                               │                 └───────┬───────┘                  │
                               │                         │                          │
                    ┌──────────┴──────────┬──────────────┴──────────────┐          │
                    │                     │                              │          │
            ┌───────▼───────┐     ┌───────▼───────┐              ┌───────▼───────┐  │
            │ Issue Created  │     │ PR Created    │              │ Push to Main  │  │
            │ → Create Story │     │ → Code Review │              │ → Deploy Docs │  │
            └───────┬───────┘     └───────┬───────┘              └───────┬───────┘  │
                    │                     │                              │          │
            ┌───────▼───────┐     ┌───────▼───────┐              ┌───────▼───────┐  │
            │ Execute Node   │     │ Execute Node  │              │ GitHub Action │  │
            │ claude-code    │     │ claude-code   │              │ Trigger       │  │
            │ /create-story  │     │ /code-review  │              └───────────────┘  │
            └───────┬───────┘     └───────┬───────┘                                 │
                    │                     │                                         │
            ┌───────▼───────┐     ┌───────▼───────┐                                 │
            │ Human Approval │     │ Post Review   │                                 │
            │ Gate           │     │ Comment to PR │                                 │
            └───────┬───────┘     └───────────────┘                                 │
                    │                                                               │
            ┌───────▼───────┐                                                       │
            │ Notify Slack   │                                                       │
            │ Story Ready    │                                                       │
            └───────────────┘                                                       │
```

### Component Architecture

```
n8n-config/
├── docker-compose.yml          # n8n + PostgreSQL deployment
├── .env.example                 # Environment template
├── workflows/
│   ├── github-webhook.json     # Main webhook receiver
│   ├── create-story.json       # BMAD create-story automation
│   ├── code-review.json        # BMAD code-review automation
│   ├── slack-notify.json       # Notification workflow
│   └── deploy-docs.json        # Docs deployment trigger
└── credentials/
    └── README.md               # Credential setup instructions
```

---

## Story Specifications

### Story P13-5.1: Create n8n Docker Compose Configuration

**Acceptance Criteria:**
- AC-5.1.1: Given Docker Compose file, when `docker-compose up` runs, then n8n starts with persistent storage
- AC-5.1.2: Given n8n is running, when accessing the UI, then authentication is required
- AC-5.1.3: Given PostgreSQL is configured, when workflows are created, then data persists across restarts

**Technical Specification:**

```yaml
# n8n-config/docker-compose.yml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: argusai-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      # Database
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=n8n-postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${N8N_DB_NAME:-n8n}
      - DB_POSTGRESDB_USER=${N8N_DB_USER:-n8n}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD}

      # Authentication
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_AUTH_USER:-admin}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_AUTH_PASSWORD}

      # Configuration
      - N8N_HOST=${N8N_HOST:-localhost}
      - N8N_PORT=5678
      - N8N_PROTOCOL=${N8N_PROTOCOL:-http}
      - WEBHOOK_URL=${N8N_WEBHOOK_URL:-http://localhost:5678}

      # Execution
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - GENERIC_TIMEZONE=${TZ:-America/Los_Angeles}

      # Claude Code integration
      - CLAUDE_CODE_PATH=${CLAUDE_CODE_PATH:-/usr/local/bin/claude}
      - ARGUSAI_PROJECT_PATH=${ARGUSAI_PROJECT_PATH:-/home/node/argusai}

    volumes:
      - n8n-data:/home/node/.n8n
      - ${ARGUSAI_PROJECT_PATH:-./..}:/home/node/argusai:ro

    depends_on:
      - n8n-postgres

    networks:
      - argusai-network

  n8n-postgres:
    image: postgres:15-alpine
    container_name: argusai-n8n-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=${N8N_DB_NAME:-n8n}
      - POSTGRES_USER=${N8N_DB_USER:-n8n}
      - POSTGRES_PASSWORD=${N8N_DB_PASSWORD}
    volumes:
      - n8n-postgres-data:/var/lib/postgresql/data
    networks:
      - argusai-network

volumes:
  n8n-data:
  n8n-postgres-data:

networks:
  argusai-network:
    driver: bridge
```

```bash
# n8n-config/.env.example
# n8n Database
N8N_DB_NAME=n8n
N8N_DB_USER=n8n
N8N_DB_PASSWORD=your-secure-password-here

# n8n Authentication
N8N_AUTH_USER=admin
N8N_AUTH_PASSWORD=your-admin-password-here

# n8n Configuration
N8N_HOST=localhost
N8N_PROTOCOL=http
N8N_WEBHOOK_URL=http://localhost:5678

# Timezone
TZ=America/Los_Angeles

# Claude Code Integration
CLAUDE_CODE_PATH=/usr/local/bin/claude
ARGUSAI_PROJECT_PATH=/path/to/argusai

# GitHub Integration
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Slack Integration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz
```

**Files to Create:**
- `n8n-config/docker-compose.yml` (NEW)
- `n8n-config/.env.example` (NEW)
- `n8n-config/README.md` (NEW)

---

### Story P13-5.2: Create GitHub Webhook Integration Workflow

**Acceptance Criteria:**
- AC-5.2.1: Given GitHub webhook is configured, when a push event occurs, then n8n receives and logs the event
- AC-5.2.2: Given a PR is created, when webhook fires, then event is routed to code-review workflow
- AC-5.2.3: Given an issue is labeled 'story', when webhook fires, then event is routed to create-story workflow

**Technical Specification:**

```json
// n8n-config/workflows/github-webhook.json
{
  "name": "GitHub Webhook Handler",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "webhookId": "github-webhook",
      "parameters": {
        "path": "github",
        "httpMethod": "POST",
        "responseMode": "onReceived",
        "responseData": "firstEntryJson"
      }
    },
    {
      "name": "Verify Signature",
      "type": "n8n-nodes-base.function",
      "position": [450, 300],
      "parameters": {
        "functionCode": "// Verify GitHub webhook signature\nconst crypto = require('crypto');\nconst signature = $input.item.headers['x-hub-signature-256'];\nconst body = JSON.stringify($input.item.body);\nconst secret = process.env.GITHUB_WEBHOOK_SECRET;\n\nconst expected = 'sha256=' + crypto\n  .createHmac('sha256', secret)\n  .update(body)\n  .digest('hex');\n\nif (signature !== expected) {\n  throw new Error('Invalid webhook signature');\n}\n\nreturn $input.item;"
      }
    },
    {
      "name": "Route by Event",
      "type": "n8n-nodes-base.switch",
      "position": [650, 300],
      "parameters": {
        "dataPropertyName": "body.action",
        "rules": {
          "rules": [
            {
              "value": "opened",
              "output": 0
            },
            {
              "value": "labeled",
              "output": 1
            },
            {
              "value": "synchronize",
              "output": 2
            }
          ]
        }
      }
    },
    {
      "name": "Check PR",
      "type": "n8n-nodes-base.if",
      "position": [850, 200],
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{ !!$json.body.pull_request }}",
              "value2": true
            }
          ]
        }
      }
    },
    {
      "name": "Trigger Code Review",
      "type": "n8n-nodes-base.executeWorkflow",
      "position": [1050, 200],
      "parameters": {
        "workflowId": "code-review-workflow-id",
        "inputData": {
          "pr_number": "={{ $json.body.pull_request.number }}",
          "pr_title": "={{ $json.body.pull_request.title }}",
          "pr_url": "={{ $json.body.pull_request.html_url }}",
          "repository": "={{ $json.body.repository.full_name }}"
        }
      }
    },
    {
      "name": "Check Story Label",
      "type": "n8n-nodes-base.if",
      "position": [850, 400],
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{ $json.body.label?.name === 'story' }}",
              "value2": true
            }
          ]
        }
      }
    },
    {
      "name": "Trigger Create Story",
      "type": "n8n-nodes-base.executeWorkflow",
      "position": [1050, 400],
      "parameters": {
        "workflowId": "create-story-workflow-id",
        "inputData": {
          "issue_number": "={{ $json.body.issue.number }}",
          "issue_title": "={{ $json.body.issue.title }}",
          "issue_body": "={{ $json.body.issue.body }}",
          "repository": "={{ $json.body.repository.full_name }}"
        }
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [{"node": "Verify Signature", "type": "main", "index": 0}]
      ]
    },
    "Verify Signature": {
      "main": [
        [{"node": "Route by Event", "type": "main", "index": 0}]
      ]
    },
    "Route by Event": {
      "main": [
        [{"node": "Check PR", "type": "main", "index": 0}],
        [{"node": "Check Story Label", "type": "main", "index": 0}],
        [{"node": "Check PR", "type": "main", "index": 0}]
      ]
    },
    "Check PR": {
      "main": [
        [{"node": "Trigger Code Review", "type": "main", "index": 0}]
      ]
    },
    "Check Story Label": {
      "main": [
        [{"node": "Trigger Create Story", "type": "main", "index": 0}]
      ]
    }
  }
}
```

**Files to Create:**
- `n8n-config/workflows/github-webhook.json` (NEW)

---

### Story P13-5.3: Create BMAD Workflow Integration

**Acceptance Criteria:**
- AC-5.3.1: Given the create-story workflow, when triggered, then Claude Code `/bmad:bmm:workflows:create-story` is executed
- AC-5.3.2: Given the dev-story workflow, when triggered, then Claude Code `/bmad:bmm:workflows:dev-story` is executed
- AC-5.3.3: Given the code-review workflow, when triggered, then Claude Code `/bmad:bmm:workflows:code-review` is executed

**Technical Specification:**

```json
// n8n-config/workflows/create-story.json
{
  "name": "BMAD Create Story",
  "nodes": [
    {
      "name": "Start",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [250, 300]
    },
    {
      "name": "Execute Claude Code",
      "type": "n8n-nodes-base.executeCommand",
      "position": [450, 300],
      "parameters": {
        "command": "cd {{ $env.ARGUSAI_PROJECT_PATH }} && claude-code --yes '/bmad:bmm:workflows:create-story' 2>&1",
        "timeout": 300000
      }
    },
    {
      "name": "Parse Output",
      "type": "n8n-nodes-base.function",
      "position": [650, 300],
      "parameters": {
        "functionCode": "// Extract story file path from Claude Code output\nconst output = $input.item.json.stdout;\nconst storyMatch = output.match(/Created story: (.+\\.md)/);\n\nreturn {\n  json: {\n    success: !output.includes('Error'),\n    storyPath: storyMatch ? storyMatch[1] : null,\n    output: output.slice(-2000)  // Last 2000 chars\n  }\n};"
      }
    },
    {
      "name": "Human Approval",
      "type": "n8n-nodes-base.wait",
      "position": [850, 300],
      "parameters": {
        "resume": "webhook",
        "options": {
          "webhookSuffix": "/approve-story"
        }
      }
    },
    {
      "name": "Notify Story Ready",
      "type": "n8n-nodes-base.executeWorkflow",
      "position": [1050, 300],
      "parameters": {
        "workflowId": "slack-notify-workflow-id",
        "inputData": {
          "message": "Story created: {{ $json.storyPath }}",
          "channel": "argusai-dev",
          "approval_url": "{{ $node['Human Approval'].json.webhookUrl }}"
        }
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [[{"node": "Execute Claude Code", "type": "main", "index": 0}]]
    },
    "Execute Claude Code": {
      "main": [[{"node": "Parse Output", "type": "main", "index": 0}]]
    },
    "Parse Output": {
      "main": [[{"node": "Human Approval", "type": "main", "index": 0}]]
    },
    "Human Approval": {
      "main": [[{"node": "Notify Story Ready", "type": "main", "index": 0}]]
    }
  }
}
```

```json
// n8n-config/workflows/code-review.json
{
  "name": "BMAD Code Review",
  "nodes": [
    {
      "name": "Start",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [250, 300]
    },
    {
      "name": "Checkout PR Branch",
      "type": "n8n-nodes-base.executeCommand",
      "position": [450, 300],
      "parameters": {
        "command": "cd {{ $env.ARGUSAI_PROJECT_PATH }} && git fetch origin pull/{{ $json.pr_number }}/head:pr-{{ $json.pr_number }} && git checkout pr-{{ $json.pr_number }}"
      }
    },
    {
      "name": "Execute Code Review",
      "type": "n8n-nodes-base.executeCommand",
      "position": [650, 300],
      "parameters": {
        "command": "cd {{ $env.ARGUSAI_PROJECT_PATH }} && claude-code --yes '/bmad:bmm:workflows:code-review' 2>&1",
        "timeout": 600000
      }
    },
    {
      "name": "Parse Review",
      "type": "n8n-nodes-base.function",
      "position": [850, 300],
      "parameters": {
        "functionCode": "// Extract review notes from output\nconst output = $input.item.json.stdout;\nconst reviewSection = output.match(/## Review Notes[\\s\\S]+/)?.[0] || 'Review completed.';\n\nreturn {\n  json: {\n    review: reviewSection.slice(0, 65000),  // GitHub comment limit\n    passed: !output.includes('BLOCKED') && !output.includes('CRITICAL')\n  }\n};"
      }
    },
    {
      "name": "Post Review Comment",
      "type": "n8n-nodes-base.httpRequest",
      "position": [1050, 300],
      "parameters": {
        "method": "POST",
        "url": "https://api.github.com/repos/{{ $input.item.repository }}/issues/{{ $input.item.pr_number }}/comments",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {"name": "Accept", "value": "application/vnd.github.v3+json"}
          ]
        },
        "bodyParameters": {
          "parameters": [
            {"name": "body", "value": "## AI Code Review\n\n{{ $json.review }}"}
          ]
        }
      }
    },
    {
      "name": "Cleanup Branch",
      "type": "n8n-nodes-base.executeCommand",
      "position": [1250, 300],
      "parameters": {
        "command": "cd {{ $env.ARGUSAI_PROJECT_PATH }} && git checkout main && git branch -D pr-{{ $input.first().json.pr_number }}"
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [[{"node": "Checkout PR Branch", "type": "main", "index": 0}]]
    },
    "Checkout PR Branch": {
      "main": [[{"node": "Execute Code Review", "type": "main", "index": 0}]]
    },
    "Execute Code Review": {
      "main": [[{"node": "Parse Review", "type": "main", "index": 0}]]
    },
    "Parse Review": {
      "main": [[{"node": "Post Review Comment", "type": "main", "index": 0}]]
    },
    "Post Review Comment": {
      "main": [[{"node": "Cleanup Branch", "type": "main", "index": 0}]]
    }
  }
}
```

**Files to Create:**
- `n8n-config/workflows/create-story.json` (NEW)
- `n8n-config/workflows/code-review.json` (NEW)
- `n8n-config/workflows/dev-story.json` (NEW)

---

### Story P13-5.4: Create Notification Workflow

**Acceptance Criteria:**
- AC-5.4.1: Given a notification is triggered, when Slack webhook is configured, then message is posted to channel
- AC-5.4.2: Given a notification is triggered, when Discord webhook is configured, then message is posted to channel
- AC-5.4.3: Given human approval is needed, when notification sends, then approval link is included

**Technical Specification:**

```json
// n8n-config/workflows/slack-notify.json
{
  "name": "Slack Notification",
  "nodes": [
    {
      "name": "Start",
      "type": "n8n-nodes-base.manualTrigger",
      "position": [250, 300]
    },
    {
      "name": "Build Message",
      "type": "n8n-nodes-base.function",
      "position": [450, 300],
      "parameters": {
        "functionCode": "const message = $input.item.json.message;\nconst channel = $input.item.json.channel || 'argusai-dev';\nconst approvalUrl = $input.item.json.approval_url;\n\nconst blocks = [\n  {\n    type: 'section',\n    text: {\n      type: 'mrkdwn',\n      text: `*ArgusAI Pipeline*\\n${message}`\n    }\n  }\n];\n\nif (approvalUrl) {\n  blocks.push({\n    type: 'actions',\n    elements: [\n      {\n        type: 'button',\n        text: { type: 'plain_text', text: 'Approve' },\n        url: approvalUrl + '?approved=true',\n        style: 'primary'\n      },\n      {\n        type: 'button',\n        text: { type: 'plain_text', text: 'Reject' },\n        url: approvalUrl + '?approved=false',\n        style: 'danger'\n      }\n    ]\n  });\n}\n\nreturn {\n  json: {\n    channel,\n    blocks\n  }\n};"
      }
    },
    {
      "name": "Send to Slack",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "method": "POST",
        "url": "={{ $env.SLACK_WEBHOOK_URL }}",
        "bodyParametersJson": "={{ JSON.stringify($json) }}"
      }
    }
  ],
  "connections": {
    "Start": {
      "main": [[{"node": "Build Message", "type": "main", "index": 0}]]
    },
    "Build Message": {
      "main": [[{"node": "Send to Slack", "type": "main", "index": 0}]]
    }
  }
}
```

**Files to Create:**
- `n8n-config/workflows/slack-notify.json` (NEW)
- `n8n-config/workflows/discord-notify.json` (NEW - similar structure)

---

### Story P13-5.5: Create Pipeline Dashboard View

**Acceptance Criteria:**
- AC-5.5.1: Given n8n is running, when accessing dashboard, then recent workflow executions are visible
- AC-5.5.2: Given workflows have metrics, when dashboard loads, then success/failure rates are displayed
- AC-5.5.3: Given human approval gates exist, when viewing dashboard, then pending approvals are highlighted

**Technical Specification:**

n8n provides a built-in dashboard. This story focuses on:
1. Configuring the dashboard for ArgusAI workflows
2. Creating a custom dashboard page in the docs site with n8n embed

```typescript
// docs-site/src/pages/pipeline-status.tsx (Docusaurus page)
import React, { useEffect, useState } from 'react';
import Layout from '@theme/Layout';

interface WorkflowExecution {
  id: string;
  workflowName: string;
  status: 'running' | 'success' | 'error' | 'waiting';
  startedAt: string;
  stoppedAt?: string;
}

export default function PipelineStatus(): JSX.Element {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);

  useEffect(() => {
    // Fetch from n8n API (requires credentials)
    async function fetchExecutions() {
      try {
        const res = await fetch('/api/n8n-proxy/executions?limit=20');
        const data = await res.json();
        setExecutions(data.data || []);
      } catch (e) {
        console.error('Failed to fetch executions:', e);
      }
    }

    fetchExecutions();
    const interval = setInterval(fetchExecutions, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Layout title="Pipeline Status">
      <div className="container margin-vert--lg">
        <h1>ArgusAI Development Pipeline</h1>

        <div className="row">
          <div className="col col--4">
            <div className="card">
              <div className="card__header">
                <h3>Recent Executions</h3>
              </div>
              <div className="card__body">
                <ul>
                  {executions.map(exec => (
                    <li key={exec.id}>
                      <span className={`badge badge--${exec.status === 'success' ? 'success' : exec.status === 'error' ? 'danger' : 'warning'}`}>
                        {exec.status}
                      </span>
                      {' '}{exec.workflowName}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="col col--8">
            <div className="card">
              <div className="card__header">
                <h3>Pending Approvals</h3>
              </div>
              <div className="card__body">
                {executions
                  .filter(e => e.status === 'waiting')
                  .map(exec => (
                    <div key={exec.id} className="alert alert--warning">
                      <strong>{exec.workflowName}</strong> awaiting approval
                      <a href={`https://n8n.argusai.local/execution/${exec.id}`}
                         className="button button--sm button--primary margin-left--md">
                        Review
                      </a>
                    </div>
                  ))
                }
                {executions.filter(e => e.status === 'waiting').length === 0 && (
                  <p>No pending approvals</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
```

**Files to Create:**
- `docs-site/src/pages/pipeline-status.tsx` (NEW)
- `n8n-config/README.md` (UPDATE with dashboard instructions)

---

## API Contracts

### n8n Webhook Endpoints

| Path | Method | Description |
|------|--------|-------------|
| `/webhook/github` | POST | Receive GitHub webhooks |
| `/webhook/approve-story` | GET | Human approval for stories |
| `/webhook/approve-review` | GET | Human approval for reviews |

### n8n API (Internal)

| Path | Method | Description |
|------|--------|-------------|
| `/api/v1/executions` | GET | List workflow executions |
| `/api/v1/workflows` | GET | List workflows |
| `/api/v1/workflows/{id}/execute` | POST | Manually trigger workflow |

---

## Security Considerations

1. **GitHub Webhook Signature**: Always verify `X-Hub-Signature-256` header
2. **n8n Authentication**: Use basic auth or SSO for dashboard access
3. **Credential Storage**: Store tokens in n8n's encrypted credential store
4. **Network Isolation**: Run n8n on internal network, expose only webhook endpoint

---

## NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR12 | Story creation <30s | Claude Code with timeout |
| NFR17 | Claude Code CLI integration | Execute command node |
| NFR18 | GitHub Actions integration | Webhook triggers |

---

## Dependencies

### External Services
- GitHub (webhooks, API)
- Slack or Discord (notifications)
- PostgreSQL (n8n data)

### Software
- Docker & Docker Compose
- Claude Code CLI (installed on host)
- Git (for branch operations)

---

## Testing Strategy

### Integration Tests
- Webhook signature verification
- Workflow execution end-to-end
- GitHub API posting

### Manual Tests
- Trigger each workflow type
- Verify notifications arrive
- Test human approval gates
- Dashboard display accuracy

---

## Deployment Notes

1. Deploy n8n with `docker-compose up -d`
2. Access n8n UI at `http://localhost:5678`
3. Import workflows from JSON files
4. Configure credentials (GitHub, Slack)
5. Add GitHub webhook pointing to n8n
6. Test with a sample issue/PR
