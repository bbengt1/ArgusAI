---
sidebar_position: 5
---

# CI/CD Pipeline

ArgusAI includes a comprehensive GitHub Actions CI/CD pipeline for automated Docker image builds and Kubernetes validation.

## Overview

The CI/CD pipeline automatically:

- **Builds** multi-architecture Docker images (amd64, arm64)
- **Pushes** images to GitHub Container Registry (ghcr.io)
- **Tags** images with semantic versions, branch names, and commit SHAs
- **Validates** Kubernetes manifests and Helm charts

## Pipeline Triggers

| Event | Actions Performed |
|-------|-------------------|
| Push to `main` | Build, push, validate (tags: `main`, `latest`, `sha-*`) |
| Pull Request to `main` | Build (no push), validate |
| Tag `v*` (e.g., `v1.2.3`) | Build, push, validate (tags: `v1.2.3`, `v1.2`, `sha-*`) |

## Image Tags

The pipeline automatically generates appropriate tags for each scenario:

| Trigger | Example Tags |
|---------|--------------|
| Push to main | `main`, `latest`, `abc1234` |
| Tag v1.2.3 | `v1.2.3`, `v1.2`, `abc1234` |
| PR #123 | `pr-123` (build only, not pushed) |

## Pipeline Jobs

The workflow runs three parallel jobs for maximum efficiency:

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                       │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  build-backend  │  build-frontend │       validate-k8s          │
│                 │                 │                             │
│  • QEMU setup   │  • QEMU setup   │  • kubectl dry-run          │
│  • Buildx       │  • Buildx       │  • helm lint                │
│  • Multi-arch   │  • Multi-arch   │  • helm template            │
│  • Push to      │  • Push to      │                             │
│    ghcr.io      │    ghcr.io      │                             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### build-backend

Builds and pushes the backend FastAPI image:

- **Image**: `ghcr.io/{owner}/argusai-backend`
- **Platforms**: `linux/amd64`, `linux/arm64`
- **Context**: `./backend`
- **Caching**: GitHub Actions cache for faster builds

### build-frontend

Builds and pushes the frontend Next.js image:

- **Image**: `ghcr.io/{owner}/argusai-frontend`
- **Platforms**: `linux/amd64`, `linux/arm64`
- **Context**: `./frontend`
- **Build Args**: `NEXT_PUBLIC_API_URL=http://localhost:8000`

### validate-k8s

Validates Kubernetes manifests and Helm charts:

- **kubectl dry-run**: Validates all manifests in `k8s/` directory
- **helm lint**: Lints the Helm chart for best practices
- **helm template**: Validates chart renders correctly

## Using the Images

After the pipeline pushes images, you can use them in your deployments:

### Docker Compose

```yaml
services:
  backend:
    image: ghcr.io/bbengt1/argusai-backend:latest
  frontend:
    image: ghcr.io/bbengt1/argusai-frontend:latest
```

### Kubernetes

```yaml
spec:
  containers:
    - name: backend
      image: ghcr.io/bbengt1/argusai-backend:v1.2.3
```

### Helm

```bash
helm install argusai ./charts/argusai \
  --set backend.image.tag=v1.2.3 \
  --set frontend.image.tag=v1.2.3
```

## Workflow Configuration

The workflow is defined in `.github/workflows/docker.yml`:

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  BACKEND_IMAGE: ghcr.io/${{ github.repository_owner }}/argusai-backend
  FRONTEND_IMAGE: ghcr.io/${{ github.repository_owner }}/argusai-frontend
```

## Creating a Release

To create a new release with proper versioning:

```bash
# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# The pipeline will automatically:
# 1. Build multi-arch images
# 2. Tag images with v1.0.0, v1.0, and commit SHA
# 3. Push to ghcr.io
```

## Viewing Pipeline Status

### GitHub Actions UI

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. Select the **Docker Build and Push** workflow
4. View job logs and status

### Check Image Availability

```bash
# List available tags
docker manifest inspect ghcr.io/bbengt1/argusai-backend:latest

# Pull and verify
docker pull ghcr.io/bbengt1/argusai-backend:latest
docker inspect ghcr.io/bbengt1/argusai-backend:latest
```

## GitHub Actions Used

The pipeline uses these official actions:

| Action | Version | Purpose |
|--------|---------|---------|
| `actions/checkout` | v4 | Repository checkout |
| `docker/setup-qemu-action` | v3 | Multi-architecture emulation |
| `docker/setup-buildx-action` | v3 | Docker Buildx for multi-arch builds |
| `docker/login-action` | v3 | GitHub Container Registry login |
| `docker/metadata-action` | v5 | Automatic image tagging |
| `docker/build-push-action` | v5 | Build and push images |
| `azure/setup-kubectl` | v4 | kubectl CLI installation |
| `azure/setup-helm` | v4 | Helm CLI installation |

## Authentication

The pipeline uses `GITHUB_TOKEN` for authentication, which is automatically provided by GitHub Actions:

```yaml
- name: Log in to Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

No additional secrets configuration is required.

## Package Visibility

By default, packages are private. To make them public:

1. Go to **Settings** > **Packages** in your repository
2. Select the package (argusai-backend or argusai-frontend)
3. Click **Package settings**
4. Change visibility to **Public**

## Customizing the Pipeline

### Change Target Platforms

Edit the `platforms` line in the workflow:

```yaml
- name: Build and push backend image
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64  # Remove arm64 for faster builds
```

### Add Additional Tags

Modify the metadata action configuration:

```yaml
- name: Extract metadata for Docker
  uses: docker/metadata-action@v5
  with:
    images: ${{ env.BACKEND_IMAGE }}
    tags: |
      type=ref,event=branch
      type=semver,pattern={{version}}
      type=raw,value=stable,enable=${{ github.ref == 'refs/heads/main' }}
```

### Add Build Arguments

For the frontend, additional build arguments can be added:

```yaml
- name: Build and push frontend image
  uses: docker/build-push-action@v5
  with:
    build-args: |
      NEXT_PUBLIC_API_URL=https://api.example.com
      NEXT_PUBLIC_ANALYTICS_ID=UA-12345
```

## Troubleshooting

### Build Fails

```bash
# Check workflow logs in GitHub Actions UI
# Common issues:
# - Dockerfile syntax errors
# - Missing dependencies
# - Authentication failures
```

### Image Push Fails

```bash
# Ensure repository has packages:write permission
# Check if GITHUB_TOKEN has correct scopes
# Verify package visibility settings
```

### Validation Fails

```bash
# Run locally to debug
helm lint ./charts/argusai
helm template argusai ./charts/argusai \
  --set secrets.encryptionKey=test \
  --set secrets.jwtSecretKey=test

# Validate K8s manifests
kubectl apply --dry-run=client -f k8s/
```

### Multi-arch Build Slow

Multi-architecture builds using QEMU can be slow. Options:

1. **Use native runners**: Self-hosted runners for each architecture
2. **Reduce platforms**: Build only `linux/amd64` for development
3. **Cache optimization**: Ensure cache-from/cache-to are configured

## Extending the Pipeline

### Add Testing Job

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/
```

### Add Deployment Job

```yaml
jobs:
  deploy:
    needs: [build-backend, build-frontend, validate-k8s]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          helm upgrade --install argusai ./charts/argusai \
            --set backend.image.tag=${{ github.sha }} \
            --set frontend.image.tag=${{ github.sha }}
```

## Next Steps

- [Docker Deployment](./docker-deployment) - Deploy with Docker Compose
- [Kubernetes Deployment](./kubernetes-deployment) - Deploy with raw manifests
- [Helm Deployment](./helm-deployment) - Deploy with Helm charts
