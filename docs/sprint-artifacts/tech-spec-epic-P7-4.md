# Epic Technical Specification: Entities Page & Alert Stub

Date: 2025-12-17
Author: Brent
Epic ID: P7-4
Status: Draft

---

## Overview

Epic P7-4 creates the foundation for entity-based alerting by designing the data model for tracking recognized entities (people, vehicles), building a UI to view and manage entities, and stubbing out the alert configuration interface. This is a preparatory epic that establishes the infrastructure for future face recognition and vehicle identification features. The actual recognition algorithms are out of scope; this epic focuses on the data model, API structure, and UI foundation.

This epic introduces new database tables and frontend pages that will be extended in future phases when recognition capabilities are added.

## Objectives and Scope

### In Scope
- Create Entity model: id, type (person/vehicle), name, thumbnail, first_seen, last_seen, occurrence_count
- Create EntitySighting model: entity_id, event_id, confidence, timestamp
- Add database migration for new tables
- Define API endpoints structure for entities
- Build entities list page with grid of entity cards
- Display entity name (editable), type, last seen, occurrence count
- Support search/filter by name, type
- Create placeholder "Add Alert" button (not functional yet)
- Show empty state when no entities exist
- Create non-functional UI for entity-based alerts ("Coming Soon")

### Out of Scope
- Face recognition/embedding generation
- Vehicle recognition algorithms
- Automatic entity matching from events
- Entity clustering or deduplication
- Alert rule evaluation based on entities
- Training or learning from user feedback

## System Architecture Alignment

This epic introduces new architectural components:

**New Components:**
- `backend/app/models/entity.py` - Entity and EntitySighting models
- `backend/app/api/v1/entities.py` - Entity CRUD endpoints
- `frontend/app/entities/page.tsx` - Entities list page
- `frontend/components/entities/` - Entity UI components

**Architecture Constraints:**
- Entity recognition will be added in future phases
- Current implementation is CRUD-only, no automatic population
- Embedding storage prepared but not used until recognition added
- Alert stub is UI-only, no backend implementation

**Future Integration Points:**
- Event processor will create EntitySighting records
- Face embedding service will populate embedding column
- Alert engine will evaluate entity-based rules

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs |
|----------------|----------------|--------|---------|
| `EntityService` | Entity CRUD operations | Entity data | Entity records |
| `entities.py` API | REST endpoints for entities | HTTP requests | JSON responses |
| `EntitiesPage` | Display entity grid | API response | Rendered page |
| `EntityCard` | Display single entity | Entity data | Rendered card |
| `EntityAlertModal` | Stub alert configuration | User input | "Coming Soon" message |

### Data Models and Contracts

**Entity model:**
```python
class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    type = Column(String(32), nullable=False)  # 'person', 'vehicle'
    name = Column(String(128), nullable=True)  # User-assigned name
    thumbnail_path = Column(String(512), nullable=True)  # Path to thumbnail image
    embedding = Column(LargeBinary, nullable=True)  # For future face/vehicle recognition
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    is_known = Column(Boolean, default=False)  # User has identified this entity
    notes = Column(Text, nullable=True)  # User notes about this entity
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sightings = relationship("EntitySighting", back_populates="entity")
```

**EntitySighting model:**
```python
class EntitySighting(Base):
    __tablename__ = "entity_sightings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(UUID, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    camera_id = Column(String(36), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    confidence = Column(Float, nullable=True)  # 0.0 - 1.0, for future use
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    thumbnail_path = Column(String(512), nullable=True)  # Snapshot at time of sighting

    entity = relationship("Entity", back_populates="sightings")
    event = relationship("Event")
```

**EntityType enum:**
```python
class EntityType(str, Enum):
    PERSON = "person"
    VEHICLE = "vehicle"
```

**Pydantic schemas:**
```python
class EntityCreate(BaseModel):
    type: EntityType
    name: Optional[str] = None
    notes: Optional[str] = None

class EntityUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    is_known: Optional[bool] = None

class EntityResponse(BaseModel):
    id: UUID
    type: EntityType
    name: Optional[str]
    thumbnail_url: Optional[str]
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int
    is_known: bool
    notes: Optional[str]

class EntityListResponse(BaseModel):
    entities: List[EntityResponse]
    total: int
    page: int
    page_size: int
```

### APIs and Interfaces

**GET /api/v1/entities**

List entities with filtering and pagination:

```
GET /api/v1/entities?type=person&search=John&page=1&page_size=20

Response 200:
{
  "entities": [
    {
      "id": "abc-123-def",
      "type": "person",
      "name": "John (neighbor)",
      "thumbnail_url": "/api/v1/entities/abc-123-def/thumbnail",
      "first_seen": "2025-12-10T08:00:00Z",
      "last_seen": "2025-12-17T14:30:00Z",
      "occurrence_count": 15,
      "is_known": true,
      "notes": "Lives next door, usually walks dog in morning"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**GET /api/v1/entities/{entity_id}**

Get single entity with sighting history:

```
GET /api/v1/entities/abc-123-def

Response 200:
{
  "id": "abc-123-def",
  "type": "person",
  "name": "John (neighbor)",
  "thumbnail_url": "/api/v1/entities/abc-123-def/thumbnail",
  "first_seen": "2025-12-10T08:00:00Z",
  "last_seen": "2025-12-17T14:30:00Z",
  "occurrence_count": 15,
  "is_known": true,
  "notes": "Lives next door",
  "recent_sightings": [
    {
      "id": 1,
      "event_id": 456,
      "camera_name": "Front Door",
      "timestamp": "2025-12-17T14:30:00Z",
      "confidence": null
    }
  ]
}
```

**POST /api/v1/entities**

Create entity manually (for testing/setup):

```
POST /api/v1/entities
{
  "type": "person",
  "name": "Family Member",
  "notes": "Do not alert"
}

Response 201:
{
  "id": "new-entity-id",
  "type": "person",
  "name": "Family Member",
  ...
}
```

**PUT /api/v1/entities/{entity_id}**

Update entity (name, notes, is_known):

```
PUT /api/v1/entities/abc-123-def
{
  "name": "John Smith (neighbor)",
  "is_known": true
}

Response 200:
{
  "id": "abc-123-def",
  "name": "John Smith (neighbor)",
  "is_known": true,
  ...
}
```

**DELETE /api/v1/entities/{entity_id}**

Delete entity and all sightings:

```
DELETE /api/v1/entities/abc-123-def

Response 204 (No Content)
```

**GET /api/v1/entities/{entity_id}/thumbnail**

Get entity thumbnail image:

```
GET /api/v1/entities/abc-123-def/thumbnail

Response 200:
Content-Type: image/jpeg
[JPEG bytes]
```

### Workflows and Sequencing

**Entity Creation (Manual - Current Phase):**
```
1. User navigates to Entities page
      ↓
2. Clicks "Add Entity" button
      ↓
3. Fills form: type, name, optional notes
      ↓
4. POST /api/v1/entities creates record
      ↓
5. Entity appears in grid
```

**Entity Creation (Automatic - Future Phase):**
```
1. Event processed with person/vehicle detection
      ↓
2. Face/vehicle embedding generated
      ↓
3. Embedding compared to existing entities
      ↓
4. If match (confidence > threshold):
   - Create EntitySighting record
   - Update entity last_seen, occurrence_count
      ↓
5. If no match:
   - Create new Entity with embedding
   - Create first EntitySighting
      ↓
6. User can name entity later via UI
```

**Alert Stub Flow (Non-Functional):**
```
1. User clicks "Create Alert" on entity card
      ↓
2. Modal opens with alert options:
   - Notify when seen
   - Notify when NOT seen for X hours
   - Time range/schedule
      ↓
3. User clicks "Save"
      ↓
4. Modal shows "Coming Soon" message
      ↓
5. Link to existing alert rules page
```

## Non-Functional Requirements

### Performance

- Entity list query: < 200ms for 1000 entities
- Thumbnail loading: < 100ms (cached)
- Search: < 300ms with full-text index

### Security

- Entity data is user-specific (no cross-user access)
- Thumbnail paths validated to prevent directory traversal
- Embedding data encrypted at rest (for future use)

### Reliability/Availability

- Entity deletion cascades to sightings
- Orphan sighting cleanup on event deletion
- Thumbnail files cleaned up on entity deletion

### Observability

- Log entity CRUD operations
- Prometheus metrics: `argusai_entities_total{type="person"}`
- Track entity page views for analytics

## Dependencies and Integrations

| Dependency | Version | Purpose |
|------------|---------|---------|
| SQLAlchemy | 2.0+ | ORM for entity models |
| Alembic | - | Database migrations |
| Pillow | 10.0+ | Thumbnail processing |

**Integration Points:**
- Event model (existing) - foreign key from EntitySighting
- Camera model (existing) - foreign key from EntitySighting
- Thumbnail storage (existing patterns) - file management

## Acceptance Criteria (Authoritative)

### Story P7-4.1: Design Entities Data Model
1. Entity model created with id, type, name, thumbnail, first_seen, last_seen, occurrence_count
2. EntitySighting model created with entity_id, event_id, confidence, timestamp
3. Database migration created and tested
4. API endpoints structure defined

### Story P7-4.2: Create Entities List Page
1. Grid of entity cards with thumbnail displayed
2. Entity name (editable), type, last seen, occurrence count shown
3. Search by name supported
4. Filter by type (person/vehicle) supported
5. Placeholder "Add Alert" button present (not functional)
6. Empty state shown when no entities exist

### Story P7-4.3: Stub Entity Alert Configuration UI
1. "Create Alert" modal opens from entity card
2. Options shown: notify when seen, notify when NOT seen for X hours
3. Time range configuration displayed
4. "Coming Soon" message shown when save attempted
5. Link to alert rules page provided

## Traceability Mapping

| AC# | Spec Section | Component/API | Test Idea |
|-----|--------------|---------------|-----------|
| P7-4.1-1 | Data Models / Entity | entity.py | Migration: verify table created |
| P7-4.1-2 | Data Models / EntitySighting | entity.py | Migration: verify table with FK |
| P7-4.1-3 | Data Models | alembic migration | Apply migration, verify schema |
| P7-4.1-4 | APIs | entities.py | Unit: verify endpoint structure |
| P7-4.2-1 | Detailed Design / EntityCard | EntityCard.tsx | E2E: render card, verify thumbnail |
| P7-4.2-2 | Detailed Design / EntityCard | EntityCard.tsx | E2E: verify all fields displayed |
| P7-4.2-3 | APIs / GET entities | search param | Integration: search by name |
| P7-4.2-4 | APIs / GET entities | type param | Integration: filter by type |
| P7-4.2-5 | Workflows / Alert Stub | EntityCard.tsx | E2E: button exists, opens modal |
| P7-4.2-6 | Detailed Design / EntitiesPage | EntitiesPage.tsx | E2E: empty state when no entities |
| P7-4.3-1 | Workflows / Alert Stub | EntityAlertModal.tsx | E2E: modal opens |
| P7-4.3-2 | Workflows / Alert Stub | EntityAlertModal.tsx | E2E: options displayed |
| P7-4.3-3 | Workflows / Alert Stub | EntityAlertModal.tsx | E2E: time config shown |
| P7-4.3-4 | Workflows / Alert Stub | EntityAlertModal.tsx | E2E: "Coming Soon" on save |
| P7-4.3-5 | Workflows / Alert Stub | EntityAlertModal.tsx | E2E: link to rules page |

## Risks, Assumptions, Open Questions

### Risks
- **R1:** Data model may need changes when recognition is implemented
  - *Mitigation:* Design with flexibility, embedding column prepared
- **R2:** Users may expect recognition to work immediately
  - *Mitigation:* Clear "Coming Soon" messaging, explain future plans
- **R3:** Large number of unidentified entities may clutter UI
  - *Mitigation:* Add pagination, allow bulk delete, filtering

### Assumptions
- **A1:** Entity recognition will be added in future phase
- **A2:** Users will manually name/identify entities initially
- **A3:** Thumbnail storage follows existing patterns in project

### Open Questions
- **Q1:** Should entities be shareable between cameras?
  - *Recommendation:* Yes, entity spans all cameras (same person at different cameras)
- **Q2:** How to handle entity merging (same person detected as different entities)?
  - *Recommendation:* Defer to future epic with recognition; add merge UI then
- **Q3:** Should we pre-populate with events that have person/vehicle detection?
  - *Recommendation:* No, wait for proper recognition; manual creation for now

## Test Strategy Summary

### Unit Tests
- Entity model validation (required fields, types)
- EntitySighting cascade delete behavior
- API endpoint parameter validation
- Thumbnail path security validation

### Integration Tests
- POST /api/v1/entities creates entity
- GET /api/v1/entities returns filtered list
- PUT /api/v1/entities/{id} updates entity
- DELETE /api/v1/entities/{id} removes entity and sightings
- GET /api/v1/entities/{id}/thumbnail returns image

### E2E Tests
- Navigate to Entities page, see empty state
- Create entity via UI, see in grid
- Edit entity name inline
- Search for entity by name
- Filter entities by type
- Click "Create Alert", see Coming Soon message
- Delete entity, confirm removed

### Tools
- pytest for backend tests
- Vitest + React Testing Library for frontend
- Playwright for E2E tests
- Test fixtures for entity data
