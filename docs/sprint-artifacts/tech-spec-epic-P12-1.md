# Epic Technical Specification: Entity-Based Alert Rules

Date: 2025-12-26
Author: Brent
Epic ID: P12-1
Status: Draft

---

## Overview

Epic P12-1 enhances the alert rule system with streamlined entity-based filtering, enabling users to create personalized alerts that trigger for specific recognized entities (people/vehicles) or for unknown strangers. This builds upon the existing P4-8.4 entity matching foundation but provides a more intuitive single-entity selection UX and adds "stranger detection" mode.

**Key Enhancement:** While P4-8.4 introduced `entity_ids` (list) and `entity_names` (pattern matching), P12-1 adds a simplified approach with single `entity_id` selection and `entity_match_mode` for clearer user intent:
- **specific**: Trigger only for the selected entity
- **unknown**: Trigger for any unrecognized person/vehicle (stranger detection)
- **any**: No entity filter (default, existing behavior)

**PRD Reference:** docs/PRD-phase12.md (FRs 1-8, 46-47)

## Objectives and Scope

**In Scope:**
- Add `entity_id` (single FK) and `entity_match_mode` to AlertRule model
- Extend AlertRuleEngine with entity_match_mode evaluation logic
- Build EntityRuleSelector UI component for alert rule forms
- Include entity name in push notifications and webhook payloads
- Add endpoint to list alert rules for a specific entity
- Display entity-associated rules on entity detail page

**Out of Scope:**
- Multiple entity selection (use existing entity_ids for complex rules)
- Entity name pattern matching (use existing entity_names for wildcards)
- Push notification delivery changes (handled by existing infrastructure)
- Entity recognition improvements (Phase 4 scope)

## System Architecture Alignment

**Components Affected:**
- `backend/app/models/alert_rule.py` - Add entity_id, entity_match_mode columns
- `backend/app/services/alert_engine.py` - Extend evaluate_rule() with entity mode logic
- `backend/app/api/v1/alert_rules.py` - Update schemas for entity fields
- `backend/app/api/v1/context.py` - Add entity alert rules endpoint
- `frontend/components/rules/EntityRuleSelector.tsx` - New component
- `frontend/components/rules/AlertRuleForm.tsx` - Integrate entity selector

**Architecture Constraints:**
- Must maintain backward compatibility with existing alert rules
- Entity lookup must add <10ms overhead per rule evaluation
- Must fail-open (deliver alert if entity lookup fails)

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs |
|--------|----------------|--------|---------|
| AlertRule Model | Store entity filter config | - | entity_id, entity_match_mode |
| AlertEngine | Evaluate entity conditions | Event, Rule | Boolean match |
| AlertRuleService | CRUD with entity support | AlertRuleCreate/Update | AlertRule |
| ContextService | Query rules by entity | entity_id | List[AlertRule] |
| EntityRuleSelector | UI for entity selection | entities list | entity_id, mode |

### Data Models and Contracts

**AlertRule Model Extension:**

```python
# backend/app/models/alert_rule.py

class AlertRule(Base):
    # ... existing fields ...

    # P12-1: Simplified entity-based filtering
    entity_id = Column(String(36), ForeignKey("recognized_entities.id", ondelete="SET NULL"), nullable=True)
    entity_match_mode = Column(String(20), nullable=False, default='any')
    # entity_match_mode values:
    #   'any' - No entity filter (default, existing behavior)
    #   'specific' - Trigger only for rule.entity_id match
    #   'unknown' - Trigger only for events with NO matched entity (stranger detection)

    # Relationship for eager loading
    entity = relationship("RecognizedEntity", foreign_keys=[entity_id], lazy="joined")
```

**Migration:**

```python
# alembic/versions/xxxx_add_entity_alert_fields.py

def upgrade():
    op.add_column('alert_rules', sa.Column('entity_id', sa.String(36), nullable=True))
    op.add_column('alert_rules', sa.Column('entity_match_mode', sa.String(20), nullable=False, server_default='any'))
    op.create_foreign_key(
        'fk_alert_rules_entity_id',
        'alert_rules', 'recognized_entities',
        ['entity_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_alert_rules_entity_id', 'alert_rules', ['entity_id'])

def downgrade():
    op.drop_index('idx_alert_rules_entity_id', 'alert_rules')
    op.drop_constraint('fk_alert_rules_entity_id', 'alert_rules', type_='foreignkey')
    op.drop_column('alert_rules', 'entity_match_mode')
    op.drop_column('alert_rules', 'entity_id')
```

**Pydantic Schemas:**

```python
# backend/app/schemas/alert_rule.py

class AlertRuleBase(BaseModel):
    name: str
    is_enabled: bool = True
    conditions: dict = {}
    actions: dict = {}
    cooldown_minutes: int = 5
    # P12-1 additions
    entity_id: Optional[str] = None
    entity_match_mode: Literal['any', 'specific', 'unknown'] = 'any'

class AlertRuleResponse(AlertRuleBase):
    id: str
    trigger_count: int
    last_triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # P12-1: Include entity name for display
    entity_name: Optional[str] = None

    class Config:
        from_attributes = True

    @validator('entity_name', pre=True, always=True)
    def get_entity_name(cls, v, values):
        # Populated from entity relationship if entity_id exists
        return v
```

### APIs and Interfaces

**Updated Alert Rule Endpoints:**

```yaml
PUT /api/v1/alert-rules/{id}:
  requestBody:
    content:
      application/json:
        schema:
          type: object
          properties:
            entity_id:
              type: string
              format: uuid
              nullable: true
            entity_match_mode:
              type: string
              enum: [any, specific, unknown]
              default: any
  responses:
    200:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/AlertRule'
            properties:
              entity_name:
                type: string
                description: Name of linked entity (for display)
```

**New Entity Alert Rules Endpoint:**

```yaml
GET /api/v1/context/entities/{entity_id}/alert-rules:
  summary: List alert rules targeting a specific entity
  parameters:
    - name: entity_id
      in: path
      required: true
      schema:
        type: string
        format: uuid
  responses:
    200:
      content:
        application/json:
          schema:
            type: object
            properties:
              rules:
                type: array
                items:
                  $ref: '#/components/schemas/AlertRule'
              total:
                type: integer
    404:
      description: Entity not found
```

**Implementation:**

```python
# backend/app/api/v1/context.py

@router.get("/entities/{entity_id}/alert-rules")
async def get_entity_alert_rules(
    entity_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """List alert rules that target a specific entity."""
    # Verify entity exists
    entity = db.query(RecognizedEntity).filter(RecognizedEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Query rules targeting this entity
    rules = db.query(AlertRule).filter(
        AlertRule.entity_id == entity_id,
        AlertRule.entity_match_mode == 'specific'
    ).all()

    return {
        "rules": [AlertRuleResponse.from_orm(r) for r in rules],
        "total": len(rules)
    }
```

### Workflows and Sequencing

**Entity Alert Evaluation Flow:**

```
Event Created
    │
    ▼
AlertEngine.evaluate_rule(rule, event)
    │
    ├─► Check cooldown
    │
    ├─► Parse conditions
    │
    ├─► Check object_types, cameras, time, etc. (existing)
    │
    └─► Check entity_match_mode (P12-1 NEW)
        │
        ├─► mode='any': PASS (no entity filter)
        │
        ├─► mode='specific':
        │       │
        │       ├─► Get event's matched entity ID
        │       │
        │       └─► Compare with rule.entity_id
        │               │
        │               ├─► Match: PASS
        │               └─► No match: FAIL
        │
        └─► mode='unknown':
                │
                └─► Check if event has NO matched entity
                        │
                        ├─► No entity (stranger): PASS
                        └─► Has entity: FAIL
```

**Entity Evaluation Implementation:**

```python
# backend/app/services/alert_engine.py

def _check_entity_match_mode(
    self,
    event: Event,
    rule: AlertRule
) -> bool:
    """
    Check if event matches rule's entity filter mode (P12-1).

    Args:
        event: Event being evaluated
        rule: AlertRule with entity_id and entity_match_mode

    Returns:
        True if entity condition is satisfied
    """
    mode = rule.entity_match_mode or 'any'

    # 'any' mode: no entity filter (default/legacy behavior)
    if mode == 'any':
        return True

    # Get event's matched entity
    event_entity_ids = []
    if event.matched_entity_ids:
        try:
            event_entity_ids = json.loads(event.matched_entity_ids)
        except json.JSONDecodeError:
            pass

    # 'specific' mode: must match rule.entity_id
    if mode == 'specific':
        if not rule.entity_id:
            # Misconfigured rule - fail open
            logger.warning(f"Rule {rule.id} has mode='specific' but no entity_id")
            return True

        return rule.entity_id in event_entity_ids

    # 'unknown' mode: event must have NO matched entity (stranger detection)
    if mode == 'unknown':
        return len(event_entity_ids) == 0

    # Unknown mode - fail open
    logger.warning(f"Unknown entity_match_mode: {mode}")
    return True
```

**Notification Enhancement:**

```python
# backend/app/services/alert_engine.py

async def _execute_dashboard_notification(
    self,
    event: Event,
    rule: AlertRule
) -> bool:
    """Execute dashboard notification with entity context."""

    # Build notification title with entity context (P12-1)
    if rule.entity_match_mode == 'specific' and rule.entity:
        title = f"{rule.entity.name} detected"
        notification_body = f"{rule.entity.name}: {event.description[:150]}"
    elif rule.entity_match_mode == 'unknown':
        title = "Unknown person detected"
        notification_body = event.description[:200]
    else:
        title = rule.name
        notification_body = event.description[:200]

    # Create notification with entity context
    notification = Notification(
        event_id=event.id,
        rule_id=rule.id,
        rule_name=title,  # Use entity-aware title
        event_description=notification_body,
        # ... rest unchanged
    )
    # ...
```

**Webhook Payload Enhancement:**

```python
def _build_webhook_payload(
    self,
    event: Event,
    rule: AlertRule
) -> dict:
    """Build webhook payload with entity context (P12-1)."""

    payload = {
        "event_id": event.id,
        "rule_id": rule.id,
        "rule_name": rule.name,
        "description": event.description,
        "timestamp": event.timestamp.isoformat(),
        "camera_id": event.camera_id,
        # ... existing fields
    }

    # P12-1: Add entity context
    if rule.entity_match_mode == 'specific' and rule.entity:
        payload["entity"] = {
            "id": rule.entity.id,
            "name": rule.entity.name,
            "type": rule.entity.entity_type,
            "match_mode": "specific"
        }
    elif rule.entity_match_mode == 'unknown':
        payload["entity"] = {
            "id": None,
            "name": "Unknown",
            "type": "unknown",
            "match_mode": "unknown"
        }
    else:
        payload["entity"] = None

    return payload
```

## Non-Functional Requirements

### Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Entity lookup | <5ms | Database query with FK index |
| Entity mode evaluation | <10ms | Additional overhead per rule |
| Total rule evaluation | <500ms | 20 rules with entity filters |

### Security

- Entity ID validated against recognized_entities table before save
- Entity name sanitized before display in notifications
- No entity data exposed in public endpoints without auth

### Reliability/Availability

- **Fail-open policy:** If entity lookup fails, deliver alert anyway
- FK constraint uses ON DELETE SET NULL to prevent orphaned rules
- Entity mode evaluation wrapped in try/catch with fallback to 'any' mode

### Observability

- Log entity mode evaluation results with rule_id, event_id, entity_id
- Metric: `alert_rules_entity_mode_matches_total{mode}` counter
- Alert on high failure rate for entity lookups

## Dependencies and Integrations

**Backend Dependencies (existing):**
```
sqlalchemy>=2.0.0
pydantic>=2.0.0
```

**Frontend Dependencies (existing):**
```
@tanstack/react-query
react-hook-form
zod
```

**No new dependencies required.**

**Integration Points:**
- RecognizedEntity model (Phase 4)
- AlertEngine service (Epic 5)
- PushDispatchService (Phase 11)
- WebhookService (Epic 5)
- EntityDetailPage (Phase 7)

## Acceptance Criteria (Authoritative)

1. **AC1:** Users can create an alert rule with `entity_match_mode='specific'` and select a single entity from a dropdown
2. **AC2:** Alert rules with `entity_match_mode='specific'` only trigger when the selected entity is detected
3. **AC3:** Users can create an alert rule with `entity_match_mode='unknown'` for stranger detection
4. **AC4:** Alert rules with `entity_match_mode='unknown'` only trigger when NO recognized entity is matched
5. **AC5:** Existing alert rules continue to work with default `entity_match_mode='any'`
6. **AC6:** Push notifications show entity name when alert is entity-based (e.g., "John detected")
7. **AC7:** Webhook payloads include entity object with id, name, type, and match_mode
8. **AC8:** Entity detail page shows associated alert rules with quick enable/disable toggle
9. **AC9:** GET `/api/v1/context/entities/{id}/alert-rules` returns rules targeting that entity
10. **AC10:** Entity evaluation adds <10ms overhead to rule evaluation

## Traceability Mapping

| AC | Spec Section | Component/API | Test Idea |
|----|--------------|---------------|-----------|
| AC1 | Data Models, APIs | AlertRuleForm, EntityRuleSelector | Create rule with entity, verify saved |
| AC2 | Workflows | AlertEngine._check_entity_match_mode | Unit test: specific mode matching |
| AC3 | APIs, Workflows | AlertRuleForm, AlertEngine | Create unknown rule, verify UI |
| AC4 | Workflows | AlertEngine._check_entity_match_mode | Unit test: unknown mode with/without entity |
| AC5 | Data Models | AlertRule migration | Migration test: existing rules unchanged |
| AC6 | Workflows | AlertEngine._execute_dashboard_notification | Integration: entity name in notification |
| AC7 | Workflows | AlertEngine._build_webhook_payload | Unit test: webhook payload structure |
| AC8 | APIs | EntityDetailPage, GET /entities/{id}/alert-rules | E2E: view rules on entity page |
| AC9 | APIs | GET /context/entities/{id}/alert-rules | API test: correct rules returned |
| AC10 | Performance | AlertEngine.evaluate_rule | Performance test: measure overhead |

## Risks, Assumptions, Open Questions

**Risks:**
- **R1:** Entity lookup latency could impact rule evaluation at scale
  - *Mitigation:* Use eager loading via relationship, add index on entity_id
- **R2:** Orphaned rules if entity deleted
  - *Mitigation:* ON DELETE SET NULL keeps rule but clears entity_id

**Assumptions:**
- **A1:** Entity recognition (Phase 4) correctly populates event.matched_entity_ids
- **A2:** Push notification infrastructure (Phase 11) handles entity-enhanced titles
- **A3:** Frontend entities dropdown uses existing TanStack Query cache

**Open Questions:**
- **Q1:** Should deleting an entity notify user of affected alert rules? (Suggested: Yes, show toast)
- **Q2:** Should entity selector show entity thumbnails? (Suggested: Yes for better UX)

## Test Strategy Summary

**Unit Tests:**
- `test_check_entity_match_mode_specific_match` - Entity ID matches
- `test_check_entity_match_mode_specific_no_match` - Entity ID differs
- `test_check_entity_match_mode_unknown_no_entity` - Stranger detected
- `test_check_entity_match_mode_unknown_has_entity` - Known entity, no match
- `test_check_entity_match_mode_any` - Default behavior unchanged
- `test_build_webhook_payload_with_entity` - Entity in payload

**Integration Tests:**
- `test_create_alert_rule_with_entity` - API CRUD with entity fields
- `test_entity_alert_triggers_notification` - End-to-end alert flow
- `test_get_entity_alert_rules` - Query rules by entity

**Frontend Tests:**
- `EntityRuleSelector.test.tsx` - Component renders, dropdown works
- `AlertRuleForm.test.tsx` - Entity fields integrate correctly

**Performance Tests:**
- Measure rule evaluation with 20 entity-based rules
- Verify <500ms total, <10ms entity overhead per rule

---

**Created:** 2025-12-26
**Stories:** P12-1.1, P12-1.2, P12-1.3, P12-1.4, P12-1.5
