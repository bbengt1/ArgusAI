# OpenAPI Specification Guide

ArgusAI uses FastAPI which automatically generates OpenAPI 3.0 specifications. This guide explains how to access, export, and use the API specification.

---

## Interactive Documentation

FastAPI provides two built-in documentation interfaces:

### Swagger UI

**URL:** `http://localhost:8000/docs`

Features:
- Interactive API explorer
- Try endpoints directly in browser
- View request/response schemas
- Test authentication

### ReDoc

**URL:** `http://localhost:8000/redoc`

Features:
- Clean, readable documentation
- Better for reference/printing
- Expandable schema details
- Search functionality

---

## Exporting OpenAPI Specification

### JSON Format

```bash
# Download OpenAPI spec as JSON
curl http://localhost:8000/openapi.json > openapi.json

# Pretty-print
curl http://localhost:8000/openapi.json | python -m json.tool > openapi.json
```

### YAML Format

Convert JSON to YAML using various tools:

```bash
# Using yq (install: brew install yq)
curl http://localhost:8000/openapi.json | yq -P > openapi.yaml

# Using Python
curl http://localhost:8000/openapi.json | python -c "
import sys, json, yaml
print(yaml.dump(json.load(sys.stdin), default_flow_style=False))
" > openapi.yaml
```

---

## Using the OpenAPI Spec

### Generate Client SDKs

Use OpenAPI Generator to create client libraries:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate TypeScript client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-fetch \
  -o ./generated/typescript-client

# Generate Python client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./generated/python-client

# Generate Go client
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g go \
  -o ./generated/go-client
```

**Available generators:** typescript-fetch, typescript-axios, python, go, java, swift5, kotlin, rust, and many more.

### Import into Postman

1. Open Postman
2. Click **Import**
3. Select **Link** tab
4. Enter: `http://localhost:8000/openapi.json`
5. Click **Import**

All endpoints will be organized into a collection with example requests.

### Import into Insomnia

1. Open Insomnia
2. Click **Create** > **Import from URL**
3. Enter: `http://localhost:8000/openapi.json`
4. Click **Fetch and Import**

### Use with Bruno

1. Open Bruno
2. Click **Import Collection**
3. Select **OpenAPI v3**
4. Provide the URL or downloaded file

---

## OpenAPI Spec Structure

The ArgusAI OpenAPI spec includes:

```yaml
openapi: "3.0.2"
info:
  title: "ArgusAI API"
  version: "1.0.0"
  description: "AI-powered security event detection"

servers:
  - url: "http://localhost:8000"
    description: "Development server"

paths:
  /api/v1/cameras:
    get: ...
    post: ...
  /api/v1/events:
    get: ...
  # ... all endpoints

components:
  schemas:
    Camera: ...
    Event: ...
    # ... all models
```

### Key Sections

| Section | Description |
|---------|-------------|
| `info` | API title, version, description |
| `servers` | Available server URLs |
| `paths` | All API endpoints with operations |
| `components/schemas` | Request/response data models |
| `tags` | Endpoint groupings (cameras, events, etc.) |

---

## Customizing the Spec

### Adding Server URLs

For production deployments, add your server URL:

```python
# In main.py
app = FastAPI(
    title="ArgusAI API",
    version="1.0.0",
    servers=[
        {"url": "http://localhost:8000", "description": "Development"},
        {"url": "https://api.yourdomain.com", "description": "Production"},
    ]
)
```

### Adding API Descriptions

Endpoint descriptions come from docstrings:

```python
@router.get("/cameras")
async def list_cameras():
    """
    List all cameras.

    Returns a list of all configured cameras with their
    current status and configuration details.

    - **is_enabled**: Filter by enabled status
    """
    pass
```

---

## Validation Tools

### Validate OpenAPI Spec

```bash
# Using Spectral (install: npm install -g @stoplight/spectral-cli)
spectral lint http://localhost:8000/openapi.json

# Using swagger-cli (install: npm install -g swagger-cli)
swagger-cli validate http://localhost:8000/openapi.json
```

### Check for Breaking Changes

```bash
# Using oasdiff (install: go install github.com/tufin/oasdiff@latest)
oasdiff breaking old-openapi.json new-openapi.json
```

---

## API Versioning

ArgusAI uses URL path versioning:

- **Current:** `/api/v1/...`
- **Future:** `/api/v2/...` (when breaking changes needed)

The OpenAPI spec reflects the current version in the `info.version` field.

---

## Rate Limiting Headers

Rate-limited endpoints return these headers:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1705312800
```

---

## Authentication (Future)

When authentication is fully enabled, the spec will include:

```yaml
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    BearerAuth:
      type: http
      scheme: bearer

security:
  - ApiKeyAuth: []
  - BearerAuth: []
```

---

## Webhooks Schema

ArgusAI webhooks follow this schema (for external integrations):

```yaml
webhooks:
  eventCreated:
    post:
      summary: Event created notification
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WebhookEventPayload'
```

See [Webhook Integration Guide](webhook-integration.md) for details.

---

## Resources

- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)
- [FastAPI OpenAPI Docs](https://fastapi.tiangolo.com/tutorial/metadata/)
- [OpenAPI Generator](https://openapi-generator.tech/)
- [Swagger Editor](https://editor.swagger.io/)

---

*Last updated: December 2025*
