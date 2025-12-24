---
sidebar_position: 4
---

# Helm Chart Deployment

Deploy ArgusAI using Helm for template-based, customizable Kubernetes deployments.

:::tip Why Helm?
- **Customizable**: Override any configuration via `values.yaml`
- **Upgradable**: Easy upgrades with `helm upgrade`
- **Reproducible**: Consistent deployments across environments
- **Maintainable**: Single source of truth for configuration
:::

## Prerequisites

- **Kubernetes cluster 1.25+**
- **Helm 3.10+**
- **kubectl** configured with cluster access

## Quick Start

```bash
# Clone the repository
git clone https://github.com/bbengt1/ArgusAI.git
cd ArgusAI

# Create namespace
kubectl create namespace argusai

# Install with required secrets
helm install argusai ./charts/argusai \
  --namespace argusai \
  --set secrets.encryptionKey=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())") \
  --set secrets.jwtSecretKey=$(openssl rand -hex 32)
```

## Chart Information

| Property | Value |
|----------|-------|
| Chart Name | argusai |
| Chart Version | 0.1.0 |
| App Version | 1.0.0 |
| Source | `charts/argusai/` |

## Installation Options

### Basic Installation

```bash
helm install argusai ./charts/argusai \
  --namespace argusai \
  --set secrets.encryptionKey="your-fernet-key" \
  --set secrets.jwtSecretKey="your-jwt-secret"
```

### Installation with Custom Values File

Create a `my-values.yaml`:

```yaml
# Custom values for production
backend:
  replicaCount: 2
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "2000m"

frontend:
  replicaCount: 2

config:
  debug: false
  logLevel: "WARNING"

secrets:
  encryptionKey: "your-fernet-key"
  jwtSecretKey: "your-jwt-secret"
  openaiApiKey: "sk-..."

persistence:
  size: 50Gi
  storageClass: "fast-ssd"

ingress:
  enabled: true
  hosts:
    - host: argusai.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: argusai-tls
      hosts:
        - argusai.example.com
```

Install with the custom values:

```bash
helm install argusai ./charts/argusai \
  --namespace argusai \
  -f my-values.yaml
```

### From OCI Registry (Future)

```bash
# Coming soon - pull from GitHub Container Registry
helm install argusai oci://ghcr.io/bbengt1/charts/argusai \
  --namespace argusai \
  --set secrets.encryptionKey="..." \
  --set secrets.jwtSecretKey="..."
```

## Configuration Reference

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nameOverride` | Override chart name | `""` |
| `fullnameOverride` | Override full release name | `""` |
| `imagePullSecrets` | Docker registry secrets | `[]` |

### Backend Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.replicaCount` | Number of backend replicas | `1` |
| `backend.image.repository` | Backend image repository | `ghcr.io/bbengt1/argusai-backend` |
| `backend.image.tag` | Backend image tag | `latest` |
| `backend.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `backend.resources.requests.memory` | Memory request | `512Mi` |
| `backend.resources.requests.cpu` | CPU request | `250m` |
| `backend.resources.limits.memory` | Memory limit | `1Gi` |
| `backend.resources.limits.cpu` | CPU limit | `1000m` |
| `backend.service.type` | Service type | `ClusterIP` |
| `backend.service.port` | Service port | `8000` |

### Frontend Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `frontend.replicaCount` | Number of frontend replicas | `1` |
| `frontend.image.repository` | Frontend image repository | `ghcr.io/bbengt1/argusai-frontend` |
| `frontend.image.tag` | Frontend image tag | `latest` |
| `frontend.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `frontend.resources.requests.memory` | Memory request | `256Mi` |
| `frontend.resources.requests.cpu` | CPU request | `100m` |
| `frontend.resources.limits.memory` | Memory limit | `512Mi` |
| `frontend.resources.limits.cpu` | CPU limit | `500m` |
| `frontend.service.type` | Service type | `ClusterIP` |
| `frontend.service.port` | Service port | `3000` |

### Application Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `config.debug` | Enable debug mode | `false` |
| `config.logLevel` | Log level | `INFO` |
| `config.corsOrigins` | CORS allowed origins | `http://localhost:3000` |
| `config.databaseUrl` | Database connection string | `sqlite:///data/app.db` |
| `config.sslEnabled` | Enable SSL | `false` |
| `config.maxCameras` | Maximum cameras | `10` |
| `config.eventRetentionDays` | Event retention days | `30` |

### Secrets

:::caution Required Secrets
`encryptionKey` and `jwtSecretKey` are **required** for the application to start.
:::

| Parameter | Description | Required |
|-----------|-------------|----------|
| `secrets.encryptionKey` | Fernet encryption key | **Yes** |
| `secrets.jwtSecretKey` | JWT signing secret | **Yes** |
| `secrets.openaiApiKey` | OpenAI API key | No |
| `secrets.xaiApiKey` | xAI Grok API key | No |
| `secrets.anthropicApiKey` | Anthropic Claude API key | No |
| `secrets.googleAiApiKey` | Google AI API key | No |
| `secrets.vapidPrivateKey` | VAPID private key (push notifications) | No |
| `secrets.vapidPublicKey` | VAPID public key (push notifications) | No |
| `secrets.mqttPassword` | MQTT password (Home Assistant) | No |

#### Generate Required Keys

```bash
# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT secret key
openssl rand -hex 32

# Generate VAPID keys (for push notifications)
npx web-push generate-vapid-keys
```

### Persistence

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.storageClass` | Storage class name | `""` (default) |
| `persistence.accessMode` | Access mode | `ReadWriteOnce` |
| `persistence.size` | Storage size | `10Gi` |
| `persistence.annotations` | PVC annotations | `{}` |

### Ingress

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.annotations` | Ingress annotations | `{}` |
| `ingress.hosts` | Ingress hosts configuration | See below |
| `ingress.tls` | TLS configuration | `[]` |

Default host configuration:

```yaml
ingress:
  hosts:
    - host: argusai.local
      paths:
        - path: /
          pathType: Prefix
```

### Security

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podSecurityContext.runAsNonRoot` | Run as non-root | `true` |
| `podSecurityContext.runAsUser` | Run as user ID | `1000` |
| `podSecurityContext.fsGroup` | Filesystem group | `1000` |
| `securityContext.allowPrivilegeEscalation` | Allow privilege escalation | `false` |

### Scheduling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nodeSelector` | Node selector labels | `{}` |
| `tolerations` | Pod tolerations | `[]` |
| `affinity` | Pod affinity rules | `{}` |

### Service Account

| Parameter | Description | Default |
|-----------|-------------|---------|
| `serviceAccount.create` | Create service account | `true` |
| `serviceAccount.annotations` | Service account annotations | `{}` |
| `serviceAccount.name` | Service account name | `""` (auto-generated) |

## Common Operations

### Upgrade

```bash
# Upgrade to new values
helm upgrade argusai ./charts/argusai \
  --namespace argusai \
  -f my-values.yaml

# Upgrade to new chart version
helm upgrade argusai ./charts/argusai \
  --namespace argusai \
  --reuse-values
```

### Rollback

```bash
# View history
helm history argusai -n argusai

# Rollback to previous release
helm rollback argusai -n argusai

# Rollback to specific revision
helm rollback argusai 2 -n argusai
```

### Uninstall

```bash
# Uninstall (keeps PVC by default)
helm uninstall argusai -n argusai

# Delete PVC manually if needed
kubectl delete pvc argusai-data -n argusai
```

### Validate Chart

```bash
# Lint the chart
helm lint ./charts/argusai

# Template without installing
helm template argusai ./charts/argusai \
  --namespace argusai \
  --set secrets.encryptionKey="test" \
  --set secrets.jwtSecretKey="test"

# Dry run installation
helm install argusai ./charts/argusai \
  --namespace argusai \
  --set secrets.encryptionKey="test" \
  --set secrets.jwtSecretKey="test" \
  --dry-run
```

## Advanced Configuration

### Using External Secrets

For production, use external secret management instead of Helm values:

#### With External Secrets Operator

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: argusai-secrets
  namespace: argusai
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: argusai-secrets
  data:
    - secretKey: ENCRYPTION_KEY
      remoteRef:
        key: argusai/encryption-key
    - secretKey: JWT_SECRET_KEY
      remoteRef:
        key: argusai/jwt-secret
```

Then install without secrets in values:

```bash
helm install argusai ./charts/argusai \
  --namespace argusai \
  --set secrets.encryptionKey="" \
  --set secrets.jwtSecretKey=""
```

### Using PostgreSQL

Deploy PostgreSQL and configure ArgusAI to use it:

```bash
# Install PostgreSQL
helm install postgres bitnami/postgresql \
  --namespace argusai \
  --set auth.database=argusai \
  --set auth.username=argusai \
  --set auth.password=secure-password

# Install ArgusAI with PostgreSQL
helm install argusai ./charts/argusai \
  --namespace argusai \
  --set config.databaseUrl="postgresql://argusai:secure-password@postgres-postgresql:5432/argusai" \
  --set secrets.encryptionKey="..." \
  --set secrets.jwtSecretKey="..."
```

### High Availability Setup

```yaml
# ha-values.yaml
backend:
  replicaCount: 3
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "2000m"

frontend:
  replicaCount: 3

config:
  databaseUrl: "postgresql://argusai:password@postgres:5432/argusai"

persistence:
  storageClass: "replicated-storage"

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
            - key: app.kubernetes.io/name
              operator: In
              values:
                - argusai
        topologyKey: kubernetes.io/hostname
```

### Multi-Environment Setup

```bash
# Development
helm install argusai-dev ./charts/argusai \
  -n argusai-dev \
  -f values-dev.yaml

# Staging
helm install argusai-staging ./charts/argusai \
  -n argusai-staging \
  -f values-staging.yaml

# Production
helm install argusai-prod ./charts/argusai \
  -n argusai-prod \
  -f values-prod.yaml
```

## Post-Installation Notes

After installation, Helm displays helpful notes:

```
ArgusAI has been deployed!

1. Get the application URL:
   kubectl --namespace argusai port-forward service/argusai-frontend 3000:3000
   Then open http://localhost:3000

2. Get backend API URL (for debugging):
   kubectl --namespace argusai port-forward service/argusai-backend 8000:8000
   Then open http://localhost:8000/docs

3. Check deployment status:
   kubectl --namespace argusai get pods -l app.kubernetes.io/instance=argusai

4. View logs:
   kubectl --namespace argusai logs -l app.kubernetes.io/component=backend -f
   kubectl --namespace argusai logs -l app.kubernetes.io/component=frontend -f
```

## Troubleshooting

### Chart Installation Fails

```bash
# Check helm status
helm status argusai -n argusai

# View helm notes
helm get notes argusai -n argusai

# View rendered manifests
helm get manifest argusai -n argusai
```

### Missing Secrets Warning

If you see warnings about missing secrets:

```bash
# Verify secrets are set
helm get values argusai -n argusai | grep -E "(encryption|jwt)"

# Update with secrets
helm upgrade argusai ./charts/argusai \
  --namespace argusai \
  --set secrets.encryptionKey="your-key" \
  --set secrets.jwtSecretKey="your-secret"
```

### Pod Scheduling Issues

```bash
# Check pod events
kubectl describe pod -l app.kubernetes.io/instance=argusai -n argusai

# Check node resources
kubectl top nodes

# Check for taints
kubectl describe nodes | grep -A5 Taints
```

## Next Steps

- [CI/CD Pipeline](./ci-cd) - Automated builds and deployments
- [Configuration](./configuration) - Configure AI providers and cameras
- [UniFi Protect](../features/unifi-protect) - Set up UniFi camera integration
