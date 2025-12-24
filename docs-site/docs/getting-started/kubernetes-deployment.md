---
sidebar_position: 3
---

# Kubernetes Deployment

Deploy ArgusAI to a Kubernetes cluster using raw manifests for fine-grained control.

:::tip Alternative Options
- For the simplest setup, use [Docker Compose](./docker-deployment)
- For template-based deployments, use [Helm Chart](./helm-deployment)
:::

## Prerequisites

- **Kubernetes cluster 1.25+** (local: minikube, kind, Docker Desktop; cloud: EKS, GKE, AKS)
- **kubectl** configured with cluster access
- **Container registry access** to ghcr.io (or your own registry)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/bbengt1/ArgusAI.git
cd ArgusAI

# Create namespace
kubectl create namespace argusai

# Generate and apply secrets
kubectl create secret generic argusai-secrets \
  --namespace argusai \
  --from-literal=ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") \
  --from-literal=JWT_SECRET_KEY=$(openssl rand -hex 32)

# Apply all manifests
kubectl apply -f k8s/ -n argusai

# Watch pods come up
kubectl get pods -n argusai -w
```

## Manifest Overview

ArgusAI provides the following Kubernetes manifests in the `k8s/` directory:

| Manifest | Purpose |
|----------|---------|
| `backend-deployment.yaml` | Backend FastAPI application |
| `frontend-deployment.yaml` | Frontend Next.js application |
| `backend-service.yaml` | ClusterIP service for backend |
| `frontend-service.yaml` | ClusterIP service for frontend |
| `configmap.yaml` | Non-sensitive configuration |
| `secret.yaml` | Template for sensitive values |
| `pvc.yaml` | Persistent storage for data |
| `ingress.yaml` | Optional ingress for external access |

## Architecture

```
                  ┌─────────────────────────────────────┐
                  │            Ingress                  │
                  │   (nginx-ingress or cloud LB)       │
                  └──────────────┬──────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      │
┌─────────────────┐    ┌─────────────────┐             │
│ frontend-svc    │    │ backend-svc     │             │
│ ClusterIP:3000  │    │ ClusterIP:8000  │             │
└────────┬────────┘    └────────┬────────┘             │
         │                      │                      │
         ▼                      ▼                      │
┌─────────────────┐    ┌─────────────────┐             │
│ Frontend Pod    │    │ Backend Pod     │             │
│ Next.js         │    │ FastAPI         │             │
└─────────────────┘    └────────┬────────┘             │
                                │                      │
                                ▼                      │
                       ┌─────────────────┐             │
                       │ PVC: argusai-   │             │
                       │ data (10Gi)     │             │
                       └─────────────────┘             │
```

## Configuration

### ConfigMap

The ConfigMap contains non-sensitive configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argusai-config
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  CORS_ORIGINS: "http://localhost:3000"
  DATABASE_URL: "sqlite:///data/app.db"
```

Customize these values by editing `k8s/configmap.yaml` before applying.

### Secrets

Secrets contain sensitive configuration. **Never commit actual secrets to git.**

```bash
# Create secrets imperatively (recommended)
kubectl create secret generic argusai-secrets \
  --namespace argusai \
  --from-literal=ENCRYPTION_KEY=your-fernet-key \
  --from-literal=JWT_SECRET_KEY=your-jwt-secret

# Or from files
kubectl create secret generic argusai-secrets \
  --namespace argusai \
  --from-file=ENCRYPTION_KEY=./encryption.key \
  --from-file=JWT_SECRET_KEY=./jwt.key
```

#### Generate Required Keys

```bash
# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT secret key
openssl rand -hex 32
```

### Persistent Volume

The PVC provides persistent storage for:
- SQLite database
- Event thumbnails
- Video frames
- SSL certificates

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: argusai-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

:::caution Storage Class
The default manifest uses the cluster's default StorageClass. For production, specify an appropriate StorageClass:

```yaml
spec:
  storageClassName: "fast-ssd"  # Your storage class
```
:::

## Scaling

### Horizontal Scaling

```bash
# Scale frontend (stateless)
kubectl scale deployment argusai-frontend --replicas=3 -n argusai

# Note: Backend requires careful scaling due to SQLite
# For multi-replica backend, use PostgreSQL
```

### Resource Limits

Default resource configuration:

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| Backend | 250m | 1000m | 512Mi | 1Gi |
| Frontend | 100m | 500m | 256Mi | 512Mi |

Adjust in deployment manifests based on your workload:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

## Ingress Configuration

The included ingress manifest works with nginx-ingress controller:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argusai-ingress
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  ingressClassName: nginx
  rules:
    - host: argusai.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: argusai-backend
                port:
                  number: 8000
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argusai-frontend
                port:
                  number: 3000
```

### Enable TLS

```yaml
spec:
  tls:
    - hosts:
        - argusai.example.com
      secretName: argusai-tls
  rules:
    # ... your rules
```

Create the TLS secret:

```bash
kubectl create secret tls argusai-tls \
  --namespace argusai \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem
```

Or use cert-manager for automatic certificate management:

```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

## Using PostgreSQL

For production deployments, use PostgreSQL instead of SQLite:

### Deploy PostgreSQL

```bash
# Using Bitnami Helm chart (recommended)
helm install postgres bitnami/postgresql \
  --namespace argusai \
  --set auth.database=argusai \
  --set auth.username=argusai \
  --set auth.password=your-secure-password
```

### Update ConfigMap

```yaml
data:
  DATABASE_URL: "postgresql://argusai:your-password@postgres-postgresql:5432/argusai"
```

## Health Checks

Both deployments include liveness and readiness probes:

```yaml
# Backend
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5

# Frontend
livenessProbe:
  httpGet:
    path: /
    port: 3000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /
    port: 3000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## Security

### Non-Root Containers

All pods run as non-root user (UID 1000):

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
```

### Network Policies (Optional)

Restrict pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: argusai-backend-policy
  namespace: argusai
spec:
  podSelector:
    matchLabels:
      app: argusai
      component: backend
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: argusai
              component: frontend
      ports:
        - port: 8000
```

## Monitoring

### View Logs

```bash
# Backend logs
kubectl logs -l app=argusai,component=backend -n argusai -f

# Frontend logs
kubectl logs -l app=argusai,component=frontend -n argusai -f

# All ArgusAI logs
kubectl logs -l app=argusai -n argusai -f
```

### Check Pod Status

```bash
# Pod status
kubectl get pods -n argusai

# Detailed pod info
kubectl describe pod -l app=argusai -n argusai

# Events
kubectl get events -n argusai --sort-by='.lastTimestamp'
```

### Prometheus Metrics

The backend exposes Prometheus metrics at `/metrics`:

```yaml
# Example ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argusai-backend
  namespace: argusai
spec:
  selector:
    matchLabels:
      app: argusai
      component: backend
  endpoints:
    - port: http
      path: /metrics
```

## Troubleshooting

### Pod Won't Start

```bash
# Check pod events
kubectl describe pod <pod-name> -n argusai

# Common issues:
# - ImagePullBackOff: Check registry access
# - CrashLoopBackOff: Check logs and secrets
# - Pending: Check resource availability
```

### Database Issues

```bash
# Exec into backend pod
kubectl exec -it deployment/argusai-backend -n argusai -- /bin/sh

# Check database file
ls -la /app/data/

# Run migrations manually
alembic upgrade head
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n argusai

# Describe PVC
kubectl describe pvc argusai-data -n argusai
```

## Uninstalling

```bash
# Remove all resources (keeps PVC)
kubectl delete -f k8s/ -n argusai

# Remove namespace and everything
kubectl delete namespace argusai

# Note: PVC deletion requires explicit deletion
kubectl delete pvc argusai-data -n argusai
```

## Next Steps

- [Helm Deployment](./helm-deployment) - Template-based deployment with customizable values
- [CI/CD Pipeline](./ci-cd) - Automated builds and deployments
- [Configuration](./configuration) - Configure AI providers and cameras
