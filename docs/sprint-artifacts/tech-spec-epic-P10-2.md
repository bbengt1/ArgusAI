# Epic Technical Specification: Docker Containerization

Date: 2025-12-24
Author: Brent
Epic ID: P10-2
Status: Draft

---

## Overview

Epic P10-2 delivers Docker containerization for ArgusAI, enabling consistent deployment across development, staging, and production environments. This includes multi-stage Dockerfiles for both backend and frontend services, docker-compose orchestration with optional PostgreSQL and nginx services, and comprehensive volume/environment configuration.

The epic transforms ArgusAI from a locally-deployed application requiring manual setup into a containerized platform that can be started with a single `docker-compose up` command.

## Objectives and Scope

### In Scope

1. **Backend Dockerfile** - Python 3.11 multi-stage build with all dependencies (ffmpeg, OpenCV, etc.)
2. **Frontend Dockerfile** - Node 20 multi-stage build with Next.js standalone output
3. **Volume Configuration** - Persistent storage for database, thumbnails, frames, certificates
4. **Environment Configuration** - All runtime settings via environment variables
5. **docker-compose.yml** - Single-command deployment orchestration
6. **PostgreSQL Service** - Optional production database via compose profiles
7. **nginx Reverse Proxy** - Optional SSL termination via compose profiles

### Out of Scope

- Kubernetes manifests and Helm charts (Epic P10-3)
- CI/CD pipeline for container builds (Epic P10-3)
- Container registry publishing (Epic P10-3)
- Swarm mode or multi-node deployment
- GPU/CUDA support for AI inference

## System Architecture Alignment

### Current Deployment Architecture

From `docs/architecture/deployment-architecture.md`:
- Backend: FastAPI on uvicorn, port 8000
- Frontend: Next.js, port 3000
- Database: SQLite (data/app.db) or PostgreSQL
- Storage: data/thumbnails, data/frames, data/certs

### Containerized Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Host                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   docker-compose                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │   │
│  │  │   nginx     │  │  frontend   │  │      backend        │   │   │
│  │  │  (profile:  │  │  :3000      │  │      :8000          │   │   │
│  │  │   ssl)      │  │             │  │                     │   │   │
│  │  │  :443/:80   │  └─────────────┘  │  - FastAPI          │   │   │
│  │  │             │         │         │  - OpenCV           │   │   │
│  │  │  ┌────────┐ │         │         │  - ffmpeg           │   │   │
│  │  │  │ certs  │ │         └─────────│  - PyAV             │   │   │
│  │  │  │ volume │ │                   │                     │   │   │
│  │  │  └────────┘ │                   │  ┌───────────────┐  │   │   │
│  │  └─────────────┘                   │  │ data volume   │  │   │   │
│  │                                    │  │ - app.db      │  │   │   │
│  │                                    │  │ - thumbnails/ │  │   │   │
│  │  ┌─────────────────────┐          │  │ - frames/     │  │   │   │
│  │  │    postgres         │          │  │ - certs/      │  │   │   │
│  │  │   (profile: postgres)│          │  └───────────────┘  │   │   │
│  │  │    :5432            │──────────│                     │   │   │
│  │  │  ┌────────────────┐ │          └─────────────────────┘   │   │
│  │  │  │ pgdata volume  │ │                                    │   │
│  │  │  └────────────────┘ │                                    │   │
│  │  └─────────────────────┘                                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Design

### Services and Modules

#### Story P10-2.1: Backend Dockerfile

**File:** `backend/Dockerfile`

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libopencv-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set environment defaults
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/system/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Considerations:**
- Multi-stage build reduces final image size (~300MB vs ~800MB)
- Non-root user for security
- System dependencies: ffmpeg (video), libopencv (CV), libgl1 (OpenGL)
- Health check endpoint for container orchestration

#### Story P10-2.2: Frontend Dockerfile

**File:** `frontend/Dockerfile`

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --only=production

# Stage 2: Builder
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Set build-time environment variable
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build with standalone output
RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone build
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

EXPOSE 3000

CMD ["node", "server.js"]
```

**Key Considerations:**
- Three-stage build for minimal image (~150MB)
- Standalone output mode for self-contained deployment
- Build-time API URL injection via ARG
- Alpine base for smallest size

**Required next.config.js change:**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // ... existing config
}
```

#### Story P10-2.3: Volumes and Environment

**Volume Mappings:**

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./data` | `/app/data` | SQLite database, thumbnails, frames |
| `./data/certs` | `/app/data/certs` | SSL certificates |
| `/dev/video0` | `/dev/video0` | USB camera access (optional) |

**Environment Variables:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///data/app.db` | Database connection string |
| `ENCRYPTION_KEY` | **Yes** | - | Fernet key for API key encryption |
| `JWT_SECRET_KEY` | **Yes** | - | JWT signing key |
| `DEBUG` | No | `False` | Debug mode |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed CORS origins |
| `SSL_ENABLED` | No | `false` | Enable SSL |
| `SSL_CERT_FILE` | No | `data/certs/cert.pem` | SSL certificate path |
| `SSL_KEY_FILE` | No | `data/certs/key.pem` | SSL key path |
| `OPENAI_API_KEY` | No | - | OpenAI API key |
| `XAI_API_KEY` | No | - | xAI Grok API key |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key |
| `GOOGLE_AI_API_KEY` | No | - | Google AI API key |
| `VAPID_PRIVATE_KEY` | No | - | Push notification key |
| `VAPID_PUBLIC_KEY` | No | - | Push notification public key |

**File: `.env.example`**
```bash
# Required - Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-fernet-key-here

# Required - Generate with: openssl rand -hex 32
JWT_SECRET_KEY=your-jwt-secret-here

# Database (SQLite default, or use PostgreSQL)
DATABASE_URL=sqlite:///data/app.db
# DATABASE_URL=postgresql://argusai:password@postgres:5432/argusai

# Frontend API URL (internal docker network)
NEXT_PUBLIC_API_URL=http://backend:8000

# Optional: AI Providers
OPENAI_API_KEY=
XAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_AI_API_KEY=

# Optional: Push Notifications
VAPID_PRIVATE_KEY=
VAPID_PUBLIC_KEY=

# Optional: SSL
SSL_ENABLED=false
```

#### Story P10-2.4: docker-compose.yml

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: ghcr.io/bbengt1/argusai-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL:-sqlite:///data/app.db}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DEBUG=${DEBUG:-false}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - XAI_API_KEY=${XAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY:-}
      - VAPID_PRIVATE_KEY=${VAPID_PRIVATE_KEY:-}
      - VAPID_PUBLIC_KEY=${VAPID_PUBLIC_KEY:-}
      - SSL_ENABLED=${SSL_ENABLED:-false}
    volumes:
      - argusai-data:/app/data
      - /dev/video0:/dev/video0:rw  # Optional: USB camera
    devices:
      - /dev/video0:/dev/video0  # Optional: USB camera
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/system/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - argusai-net

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: http://backend:8000
    image: ghcr.io/bbengt1/argusai-frontend:latest
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_WS_URL=ws://backend:8000
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    networks:
      - argusai-net

volumes:
  argusai-data:
    driver: local

networks:
  argusai-net:
    driver: bridge
```

#### Story P10-2.5: PostgreSQL Service

**Added to docker-compose.yml:**

```yaml
services:
  # ... existing services ...

  postgres:
    image: postgres:16-alpine
    profiles:
      - postgres
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-argusai}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-argusai}
      - POSTGRES_DB=${POSTGRES_DB:-argusai}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-argusai}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - argusai-net

volumes:
  # ... existing volumes ...
  pgdata:
    driver: local
```

**Usage:**
```bash
# Start with PostgreSQL
docker-compose --profile postgres up -d

# Backend DATABASE_URL should be:
DATABASE_URL=postgresql://argusai:argusai@postgres:5432/argusai
```

#### Story P10-2.6: nginx Reverse Proxy with SSL

**File:** `nginx/nginx.conf`

```nginx
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Upstreams
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        ssl_certificate /etc/nginx/certs/cert.pem;
        ssl_certificate_key /etc/nginx/certs/key.pem;

        # API routes
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }

        # OpenAPI docs
        location /docs {
            proxy_pass http://backend;
        }

        location /openapi.json {
            proxy_pass http://backend;
        }

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

**Added to docker-compose.yml:**

```yaml
services:
  # ... existing services ...

  nginx:
    image: nginx:alpine
    profiles:
      - ssl
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./data/certs:/etc/nginx/certs:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - argusai-net
```

**Usage:**
```bash
# Start with SSL reverse proxy
docker-compose --profile ssl up -d

# Or with PostgreSQL and SSL
docker-compose --profile postgres --profile ssl up -d
```

### Data Models and Contracts

No new data models required. Existing models work unchanged in containers.

### APIs and Interfaces

**Health Check Endpoints** (existing, verified for container use):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/system/health` | GET | Backend health check |
| `/` | GET | Frontend health check (Next.js) |

### Workflows and Sequencing

**Deployment Workflow:**

```mermaid
sequenceDiagram
    participant User
    participant Compose as docker-compose
    participant Backend
    participant Frontend
    participant Postgres as PostgreSQL (optional)
    participant Nginx as nginx (optional)

    User->>Compose: docker-compose up -d
    Compose->>Backend: Start container
    Backend->>Backend: Run health check
    Compose->>Frontend: Start container (waits for backend)
    Frontend->>Backend: Connect to API
    Frontend->>Frontend: Run health check

    alt --profile postgres
        Compose->>Postgres: Start PostgreSQL
        Backend->>Postgres: Connect database
    end

    alt --profile ssl
        Compose->>Nginx: Start nginx
        Nginx->>Backend: Proxy API requests
        Nginx->>Frontend: Proxy frontend requests
    end

    User->>Frontend: Access application
```

## Non-Functional Requirements

### Performance

- **NFR1:** Container startup < 30 seconds (backend + frontend)
- **NFR2:** Backend image size < 500MB
- **NFR3:** Frontend image size < 200MB
- **NFR4:** Memory usage: Backend < 1GB, Frontend < 512MB
- **NFR5:** Health check response < 100ms

### Security

- **NFR6:** Non-root user in containers
- **NFR7:** No secrets baked into images
- **NFR8:** TLS 1.2+ only for SSL profile
- **NFR9:** Read-only nginx config volume
- **NFR10:** Named volumes for data persistence (not bind mounts in production)

### Reliability/Availability

- **NFR11:** `restart: unless-stopped` policy on all services
- **NFR12:** Health checks with proper start periods
- **NFR13:** Graceful shutdown handling (SIGTERM)
- **NFR14:** Data persistence survives container restarts

### Observability

- **NFR15:** Structured JSON logging from backend
- **NFR16:** Container health status visible via `docker ps`
- **NFR17:** nginx access/error logs available
- **NFR18:** Prometheus metrics endpoint still accessible at `/metrics`

## Dependencies and Integrations

### External Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Docker Engine | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Orchestration |
| Python | 3.11 | Backend runtime |
| Node.js | 20 | Frontend runtime |
| PostgreSQL | 16 | Optional database |
| nginx | alpine | Optional reverse proxy |

### Internal Dependencies

- UniFi Protect connections work via Docker networking
- RTSP camera access works if network is accessible
- USB camera requires device mounting (Linux only)

## Acceptance Criteria (Authoritative)

### P10-2.1: Backend Dockerfile

| AC ID | Acceptance Criteria |
|-------|---------------------|
| AC-2.1.1 | Given the Dockerfile is built, when the container starts, then the FastAPI backend runs successfully and all Python dependencies are installed |
| AC-2.1.2 | Given the container is running, when I access the health endpoint, then it returns a healthy status |
| AC-2.1.3 | Given I want to use PostgreSQL instead of SQLite, when I set the DATABASE_URL environment variable, then the backend connects to PostgreSQL and all features work correctly |

### P10-2.2: Frontend Dockerfile

| AC ID | Acceptance Criteria |
|-------|---------------------|
| AC-2.2.1 | Given the Dockerfile is built, when the container starts, then the Next.js production build is served and the frontend is accessible on port 3000 |
| AC-2.2.2 | Given I need to configure the API URL, when I set NEXT_PUBLIC_API_URL environment variable, then the frontend connects to the specified backend |

### P10-2.3: Docker Volumes and Environment

| AC ID | Acceptance Criteria |
|-------|---------------------|
| AC-2.3.1 | Given the backend container is running with volumes, when the container is stopped and restarted, then all database data, thumbnails, frames, and certificates persist |
| AC-2.3.2 | Given I configure environment variables, when the container starts, then all settings are applied from environment and no secrets are baked into the image |

### P10-2.4: docker-compose.yml

| AC ID | Acceptance Criteria |
|-------|---------------------|
| AC-2.4.1 | Given I have Docker and docker-compose installed, when I run `docker-compose up -d`, then both backend and frontend containers start and the application is accessible at localhost with data persisted in named volumes |
| AC-2.4.2 | Given the containers are running, when I run `docker-compose down` then `docker-compose up`, then containers stop gracefully, volumes are preserved, and previous state is restored |

### P10-2.5: PostgreSQL Service

| AC ID | Acceptance Criteria |
|-------|---------------------|
| AC-2.5.1 | Given I want to use PostgreSQL, when I run `docker-compose --profile postgres up`, then PostgreSQL container starts alongside the app and backend connects to PostgreSQL with migrations applied automatically |
| AC-2.5.2 | Given PostgreSQL is running, when I check the database, then all tables are created correctly and data is persisted in a named volume |

### P10-2.6: nginx Reverse Proxy with SSL

| AC ID | Acceptance Criteria |
|-------|---------------------|
| AC-2.6.1 | Given I want SSL/HTTPS, when I run `docker-compose --profile ssl up`, then nginx container starts as reverse proxy with HTTPS on port 443 and HTTP redirects to HTTPS |
| AC-2.6.2 | Given I have certificates in data/certs, when nginx starts, then it uses my SSL certificates and connections are properly secured |
| AC-2.6.3 | Given I use compose profiles, when I run without `--profile ssl`, then nginx is not started and I can access backend/frontend directly |

## Traceability Mapping

| Story | PRD FRs | Backlog Items |
|-------|---------|---------------|
| P10-2.1 | FR12, FR14, FR17, FR18 | FF-032 |
| P10-2.2 | FR13, FR14 | FF-032 |
| P10-2.3 | FR15, FR16 | FF-032 |
| P10-2.4 | FR19 | FF-032 |
| P10-2.5 | FR18, FR20, FR22 | FF-032 |
| P10-2.6 | FR21, FR22 | FF-032 |

## Risks, Assumptions, Open Questions

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| USB camera mounting fails on non-Linux | Medium | Low | Document as Linux-only feature, test in VM |
| Large image sizes slow CI | Medium | Medium | Multi-stage builds, layer caching |
| ffmpeg/OpenCV compatibility issues | Low | High | Pin specific versions, test on multiple architectures |
| Database migrations fail in container | Low | High | Run migrations on startup, add health check delay |

### Assumptions

1. Users have Docker Engine 24.0+ and Docker Compose 2.20+
2. Linux hosts are used for USB camera access
3. Users provide valid SSL certificates for ssl profile
4. Network allows access to UniFi Protect controllers

### Open Questions

1. **Multi-architecture builds** - Should we support arm64 in addition to amd64? (Recommend: Yes, for Raspberry Pi deployments)
2. **GPU acceleration** - Should we support NVIDIA GPU for AI inference? (Recommend: Defer to future phase)
3. **Secrets management** - Should we support Docker secrets instead of env vars? (Recommend: Document as option for Swarm deployments)

## Test Strategy Summary

### Unit Tests

- Dockerfile syntax validation (hadolint)
- Environment variable handling in startup scripts

### Integration Tests

| Test | Description |
|------|-------------|
| Backend container starts | Build and run backend, verify health endpoint |
| Frontend container starts | Build and run frontend, verify home page loads |
| Backend-Frontend communication | Both containers up, verify API calls work |
| PostgreSQL connection | Profile postgres, verify database operations |
| nginx proxy | Profile ssl, verify HTTPS and routing |
| Volume persistence | Stop/start containers, verify data persists |

### Manual Testing Checklist

- [ ] `docker-compose up -d` starts all services
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend accessible at http://localhost:8000
- [ ] API calls from frontend succeed
- [ ] WebSocket connection works
- [ ] Data persists after container restart
- [ ] `--profile postgres` starts PostgreSQL
- [ ] `--profile ssl` starts nginx with HTTPS
- [ ] Health checks pass in `docker ps`
