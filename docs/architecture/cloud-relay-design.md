# Cloud Relay Architecture Design

**Document Version:** 1.0
**Date:** 2025-12-24
**Author:** ArgusAI Development Team
**Epic:** P8-4 (Native Apple Apps Foundation)
**Story:** P8-4.2 (Design Cloud Relay Architecture)

---

## Executive Summary

This document defines the cloud relay architecture for ArgusAI mobile apps, enabling secure remote access to local ArgusAI instances without port forwarding. The design prioritizes user-friendliness, security, and cost-effectiveness.

**Primary Recommendation:** Cloudflare Tunnel (Zero Trust)
**Fallback Option:** Tailscale (for advanced users)

**Key Design Decisions:**
- Device pairing via 6-digit codes (5-minute expiry)
- JWT-based authentication (1-hour access, 30-day refresh)
- TLS 1.3 end-to-end encryption
- Automatic local network fallback for LAN users

---

## Connection Requirements

### Core Requirements

| Requirement | Description | Priority |
|-------------|-------------|----------|
| No Port Forwarding | Users should not need to configure routers | Critical |
| NAT Traversal | Works behind any NAT/firewall configuration | Critical |
| End-to-End Encryption | All traffic encrypted with TLS 1.3 | Critical |
| Zero Configuration | Setup should be minimal for end users | High |
| Local Network Fallback | Use direct connection when on same LAN | High |
| Low Latency | Push notifications < 5 seconds | Medium |

### Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        REMOTE ACCESS                             │
│                                                                   │
│  ┌─────────────┐         ┌─────────────────┐       ┌───────────┐ │
│  │   iOS App   │◄───────►│  Cloud Relay    │◄─────►│  ArgusAI  │ │
│  │  (Mobile)   │  HTTPS  │  (CF/Tailscale) │ Tunnel│  (Local)  │ │
│  └─────────────┘         └─────────────────┘       └───────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        LOCAL ACCESS                              │
│                                                                   │
│  ┌─────────────┐                               ┌───────────────┐ │
│  │   iOS App   │◄─────────────────────────────►│    ArgusAI    │ │
│  │  (Mobile)   │        Bonjour/mDNS           │    (Local)    │ │
│  └─────────────┘                               └───────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Provider Comparison

### Overview

| Provider | Type | Free Tier | Setup Complexity | NAT Traversal | Best For |
|----------|------|-----------|------------------|---------------|----------|
| Cloudflare Tunnel | HTTP Tunnel | Yes | Low | Excellent | Default choice |
| Tailscale | Mesh VPN | Yes (3 users) | Medium | Excellent | Advanced users |
| AWS API Gateway | HTTP Proxy | No | High | Via EC2 | Enterprise |
| Self-Hosted | Custom | N/A | Very High | Varies | Full control |

### Cloudflare Tunnel (Recommended)

**Overview:**
Cloudflare Tunnel (formerly Argo Tunnel) creates an encrypted tunnel from your origin server to Cloudflare's edge without opening inbound ports.

**Pros:**
- Free tier available (unlimited tunnels)
- No inbound ports required (outbound-only connections)
- Automatic TLS certificates
- Built-in DDoS protection
- Global CDN edge locations (low latency)
- Simple `cloudflared` daemon setup
- Zero Trust access policies available
- Supports WebSocket for real-time updates

**Cons:**
- Requires Cloudflare account
- Traffic routes through Cloudflare (privacy consideration)
- Requires domain name (can use workers.dev subdomain)
- Free tier may have rate limits for heavy usage

**Setup Steps:**
1. Create Cloudflare account (free)
2. Add domain or use workers.dev subdomain
3. Install `cloudflared` daemon on ArgusAI server
4. Create tunnel: `cloudflared tunnel create argusai`
5. Configure tunnel to route to local ArgusAI port
6. Run daemon: `cloudflared tunnel run argusai`

**Free Tier Limits:**
- Unlimited tunnels
- Unlimited bandwidth (fair use)
- No guaranteed SLA
- Community support only

### Tailscale (Fallback)

**Overview:**
Tailscale is a mesh VPN built on WireGuard that creates secure point-to-point connections between devices.

**Pros:**
- End-to-end encrypted (no relay sees plaintext)
- WireGuard-based (fast, modern protocol)
- Mesh topology (direct device-to-device when possible)
- Works with NAT-to-NAT scenarios
- MagicDNS for easy device discovery
- Exit node capability
- Native mobile apps available

**Cons:**
- Free tier limited to 3 users
- Requires Tailscale client on both ends
- More complex conceptually for non-technical users
- iOS app must be part of tailnet
- Not suitable for general public access

**Setup Steps:**
1. Create Tailscale account
2. Install Tailscale on ArgusAI server
3. Authenticate: `tailscale up`
4. Install Tailscale app on iOS device
5. Join same tailnet
6. Access ArgusAI via tailnet IP or MagicDNS name

**Free Tier Limits:**
- 3 users maximum
- 100 devices
- No SSO/SAML
- Community support

### AWS API Gateway

**Overview:**
AWS API Gateway can proxy requests to a backend running on EC2 or via VPN connection.

**Pros:**
- Enterprise-grade reliability
- Advanced authentication (Cognito, IAM)
- Usage plans and throttling
- Detailed metrics and logging
- WebSocket API support

**Cons:**
- Complex setup
- Pay-per-request pricing
- Requires AWS expertise
- Needs EC2/Lambda for backend integration
- Overkill for home users

**Cost Estimate:**
- API Gateway: $3.50 per million requests
- Data transfer: $0.09/GB
- Estimated monthly: $5-20 for typical home use

### Self-Hosted Relay

**Overview:**
Run your own relay server (e.g., TURN/STUN, custom WebSocket relay) on a VPS.

**Pros:**
- Full control over infrastructure
- No third-party dependencies
- Customizable to specific needs
- Can be made very secure

**Cons:**
- Requires VPS hosting ($5-20/month)
- Significant setup and maintenance
- Security responsibility on operator
- Need to handle DDoS protection
- TLS certificate management required

**Not recommended for typical users.**

---

## Cost Estimates

| Provider | Monthly Cost | Annual Cost | Notes |
|----------|--------------|-------------|-------|
| Cloudflare Tunnel | $0 | $0 | Free tier sufficient for home use |
| Tailscale | $0 | $0 | Free tier (3 users) |
| Tailscale Team | $6/user | $72/user | If more than 3 users needed |
| AWS API Gateway | $5-20 | $60-240 | Varies with usage |
| Self-Hosted VPS | $5-20 | $60-240 | DigitalOcean, Linode, etc. |

**Recommendation:** Start with Cloudflare Tunnel (free), offer Tailscale as documented alternative for advanced users who prefer mesh VPN approach.

---

## Authentication Flow

### Device Pairing Mechanism

The pairing flow uses a time-limited one-time code generated from the ArgusAI web UI and entered in the mobile app.

**Pairing Code Properties:**
- Format: 6 numeric digits (e.g., "847291")
- Expiry: 5 minutes from generation
- Single use: Deleted after successful verification
- Rate limited: Max 5 active codes per minute

### Token Structure

**Access Token (JWT):**
```json
{
  "typ": "access",
  "sub": "device_id",
  "device_name": "iPhone 15 Pro",
  "iat": 1703419200,
  "exp": 1703422800
}
```
- Expiry: 1 hour
- Used for API authentication

**Refresh Token (JWT):**
```json
{
  "typ": "refresh",
  "sub": "device_id",
  "jti": "unique_token_id",
  "iat": 1703419200,
  "exp": 1706011200
}
```
- Expiry: 30 days
- Rotated on each use
- Stored hashed in database

### Certificate Pinning

Mobile apps should implement certificate pinning to prevent MITM attacks:
- Pin Cloudflare's intermediate CA certificate
- Pin backup certificates for rotation
- Implement pinning bypass for development builds only

---

## Security Considerations

### Encryption

| Layer | Protocol | Details |
|-------|----------|---------|
| Transport | TLS 1.3 | Minimum version, modern cipher suites |
| Tunnel | Cloudflare/WireGuard | Provider-specific encryption |
| Payload | HTTPS | All API traffic over HTTPS |

### Rate Limiting

| Endpoint | Limit | Window | Action |
|----------|-------|--------|--------|
| POST /mobile/auth/pair | 5 | 1 minute | Block IP |
| POST /mobile/auth/verify | 10 | 1 minute | Block IP |
| POST /mobile/auth/refresh | 20 | 1 minute | Block device |
| GET /mobile/events | 100 | 1 minute | Throttle |

### Abuse Prevention

1. **Pairing Code Brute Force:**
   - 6-digit codes = 1,000,000 combinations
   - 10 attempts/minute = 100,000 minutes to brute force
   - Lock out after 5 failed attempts per IP

2. **Token Replay:**
   - Tokens bound to device_id
   - Refresh tokens invalidated on rotation
   - Maintain token blacklist for revoked devices

3. **DDoS Protection:**
   - Cloudflare provides automatic DDoS mitigation
   - Local rate limiting as secondary defense

### Token Security Best Practices

1. **Single-Use Pairing Codes:**
   - Code deleted immediately after successful verification
   - Cannot be reused even if intercepted

2. **Token Rotation:**
   - Refresh tokens rotated on every use
   - Old refresh token invalidated immediately

3. **Device Binding:**
   - Tokens include device_id claim
   - Server validates device_id matches on all requests

4. **Secure Storage:**
   - iOS Keychain for token storage
   - Encrypted at rest by iOS
   - Biometric protection optional

---

## Sequence Diagrams

### Pairing Flow

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│  ArgusAI    │     │  ArgusAI        │     │  iOS App    │
│  Web UI     │     │  Backend        │     │             │
└──────┬──────┘     └────────┬────────┘     └──────┬──────┘
       │                     │                     │
       │ 1. Click "Pair      │                     │
       │    New Device"      │                     │
       │────────────────────>│                     │
       │                     │                     │
       │ 2. Generate code    │                     │
       │    (847291, 5min)   │                     │
       │<────────────────────│                     │
       │                     │                     │
       │ 3. Display code     │                     │
       │    to user          │                     │
       │                     │                     │
       │                     │ 4. User enters      │
       │                     │    "847291" in app  │
       │                     │<────────────────────│
       │                     │                     │
       │                     │ 5. Verify code      │
       │                     │    Create device    │
       │                     │    Generate tokens  │
       │                     │────────────────────>│
       │                     │                     │
       │                     │ 6. Store tokens     │
       │                     │    in Keychain      │
       │                     │                     │
       │                     │ 7. Show Events      │
       │                     │                     │
```

### Remote Access Flow

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│  iOS App    │     │  Cloudflare     │     │  ArgusAI    │
│             │     │  Tunnel         │     │  Backend    │
└──────┬──────┘     └────────┬────────┘     └──────┬──────┘
       │                     │                     │
       │ 1. GET /mobile/     │                     │
       │    events           │                     │
       │    + Bearer token   │                     │
       │────────────────────>│                     │
       │                     │                     │
       │                     │ 2. Forward request  │
       │                     │    to origin        │
       │                     │────────────────────>│
       │                     │                     │
       │                     │ 3. Validate token   │
       │                     │    Query events     │
       │                     │<────────────────────│
       │                     │                     │
       │ 4. Return events    │                     │
       │    with thumbnails  │                     │
       │<────────────────────│                     │
       │                     │                     │
       │ 5. Display events   │                     │
       │                     │                     │
```

### Token Refresh Flow

```
┌─────────────┐                              ┌─────────────┐
│  iOS App    │                              │  ArgusAI    │
│             │                              │  Backend    │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │ 1. Access token                            │
       │    expires (< 5min)                        │
       │                                            │
       │ 2. POST /mobile/auth/refresh               │
       │    + refresh_token                         │
       │    + device_id                             │
       │───────────────────────────────────────────>│
       │                                            │
       │                              3. Validate   │
       │                                 refresh    │
       │                                 token      │
       │                                            │
       │                              4. Rotate     │
       │                                 refresh    │
       │                                 token      │
       │                                            │
       │ 5. Return new                              │
       │    access_token +                          │
       │    refresh_token                           │
       │<───────────────────────────────────────────│
       │                                            │
       │ 6. Store new tokens                        │
       │    in Keychain                             │
       │                                            │
```

### Local Network Fallback Flow

```
┌─────────────┐                              ┌─────────────┐
│  iOS App    │                              │  ArgusAI    │
│             │                              │  Backend    │
└──────┬──────┘                              └──────┬──────┘
       │                                            │
       │ 1. App launch or                           │
       │    network change                          │
       │                                            │
       │ 2. Bonjour/mDNS                            │
       │    discovery query                         │
       │    _argusai._tcp.local                     │
       │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─>│
       │                                            │
       │ 3. Respond with                            │
       │    local IP + port                         │
       │<─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
       │                                            │
       │ 4. Switch to                               │
       │    direct local                            │
       │    connection                              │
       │───────────────────────────────────────────>│
       │                                            │
       │ 5. API requests                            │
       │    bypass cloud                            │
       │    relay                                   │
       │                                            │
```

---

## Implementation Recommendations

### Phase 1: Cloudflare Tunnel Setup

1. **Backend Changes:**
   - Add `cloudflared` installation to setup script
   - Create tunnel configuration template
   - Document tunnel creation process

2. **Configuration:**
   ```yaml
   # cloudflared config.yml
   tunnel: argusai
   credentials-file: /etc/cloudflared/credentials.json
   ingress:
     - hostname: argusai.example.com
       service: http://localhost:8000
     - service: http_status:404
   ```

3. **Mobile App:**
   - Configure API base URL to tunnel hostname
   - Implement certificate pinning

### Phase 2: Local Network Discovery

1. **Backend:**
   - Advertise `_argusai._tcp.local` via mDNS
   - Include TXT record with version info

2. **Mobile App:**
   - Use Network framework for Bonjour discovery
   - Prefer local connection when available
   - Seamless fallback to cloud relay

### Phase 3: Tailscale Documentation

1. **Document alternative setup for advanced users**
2. **Provide installation guide**
3. **Note limitations (3-user free tier)**

---

## Appendix: Cloudflare Tunnel Quick Start

### Installation (Linux/macOS)

```bash
# Download cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Authenticate with Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create argusai

# Configure tunnel
cat > ~/.cloudflared/config.yml << EOF
tunnel: argusai
credentials-file: ~/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: argusai.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
EOF

# Create DNS record
cloudflared tunnel route dns argusai argusai.yourdomain.com

# Run tunnel
cloudflared tunnel run argusai
```

### Running as Service

```bash
# Install as systemd service
sudo cloudflared service install

# Enable and start
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

## Appendix: Tailscale Quick Start

### Installation

```bash
# Linux
curl -fsSL https://tailscale.com/install.sh | sh

# macOS
brew install tailscale

# Authenticate
sudo tailscale up
```

### Mobile Access

1. Install Tailscale app on iOS
2. Sign in with same account
3. Access ArgusAI via tailnet hostname: `argusai.tailnet-name.ts.net`

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-24 | 1.0 | Initial cloud relay architecture design |

---

*Generated as part of Story P8-4.2: Design Cloud Relay Architecture*
