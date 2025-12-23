# Story P9-5.2: Add Certificate Generation to Install Script

Status: done

## Story

As a **system administrator**,
I want **the install script to offer SSL certificate generation options**,
so that **I can easily set up HTTPS for secure connections without manual certificate management**.

## Acceptance Criteria

1. **Given** I run the install script, **When** prompted for SSL, **Then** I see options: Let's Encrypt, Self-signed, Skip.

2. **Given** I choose Let's Encrypt, **When** I provide my domain and email, **Then** certbot obtains certificates and stores them in data/certs/.

3. **Given** Let's Encrypt succeeds, **When** setup completes, **Then** auto-renewal is configured via cron/systemd timer.

4. **Given** I choose Self-signed, **When** generation runs, **Then** a self-signed certificate is created in data/certs/ with 2048-bit RSA.

5. **Given** I choose Self-signed, **When** setup completes, **Then** I'm warned about browser security warnings.

6. **Given** I choose Skip, **When** setup completes, **Then** ArgusAI runs on HTTP only with no certificate files.

## Tasks / Subtasks

- [x] Task 1: Add SSL setup prompt function to install.sh (AC: #1)
  - [x] Create `prompt_ssl_setup()` function with three options
  - [x] Add --ssl-only flag for standalone SSL setup
  - [x] Display clear descriptions for each option

- [x] Task 2: Implement Let's Encrypt certificate generation (AC: #2, #3)
  - [x] Check for certbot installation, offer to install if missing
  - [x] Prompt for domain name and email
  - [x] Run certbot in standalone mode
  - [x] Copy certificates to data/certs/ with appropriate permissions
  - [x] Create symlinks to Let's Encrypt live directory

- [x] Task 3: Configure Let's Encrypt auto-renewal (AC: #3)
  - [x] Create systemd timer for Linux systems
  - [x] Create launchd plist for macOS systems
  - [x] Set up post-renewal hook to restart services
  - [x] Verify renewal configuration with dry-run

- [x] Task 4: Implement self-signed certificate generation (AC: #4)
  - [x] Create `generate_self_signed_cert()` function
  - [x] Use openssl to generate 2048-bit RSA key
  - [x] Create certificate valid for 365 days
  - [x] Set proper file permissions (600 for key, 644 for cert)

- [x] Task 5: Add browser warning for self-signed certs (AC: #5)
  - [x] Display prominent warning after generation
  - [x] Explain how to add certificate exception in browsers
  - [x] Document alternative: add to system trust store

- [x] Task 6: Implement skip option (AC: #6)
  - [x] Handle skip gracefully with no certificate operations
  - [x] Log that SSL is not configured
  - [x] Remind user about HTTPS requirement for push notifications

- [x] Task 7: Update .env with SSL configuration (All ACs)
  - [x] Set SSL_ENABLED based on certificate availability
  - [x] Set SSL_CERT_FILE and SSL_KEY_FILE paths
  - [x] Preserve existing .env settings when possible

- [x] Task 8: Integrate SSL setup into main install flow (All ACs)
  - [x] Call `prompt_ssl_setup()` after server hostname prompt
  - [x] Update CORS origins for HTTPS if SSL enabled
  - [x] Update summary to show SSL configuration status

## Dev Notes

### Relevant Architecture Patterns and Constraints

- **Script Location:** `install.sh` in project root
- **Certificate Storage:** `data/certs/` directory (matches backend config)
- **Environment:** Must work on both macOS (launchd) and Linux (systemd)
- **Dependencies:** certbot for Let's Encrypt, openssl for self-signed

### Source Tree Components to Touch

| File | Change Type | Description |
|------|-------------|-------------|
| `install.sh` | MODIFY | Add SSL setup functions and prompts |
| `services/` | CREATE | Add renewal timer/plist files |

### Testing Strategy

- Test on macOS: Self-signed generation, Skip option
- Test on Linux VM: All options including Let's Encrypt (requires domain)
- Verify file permissions (600 for private key)
- Test renewal timer configuration

### References

- [Source: docs/sprint-artifacts/tech-spec-epic-P9-5.md#Certificate-Generation-Commands]
- [Source: docs/PRD-phase9.md#Infrastructure-DevOps] - FR34, FR35
- [Source: docs/epics-phase9.md#Story-P9-5.2] - Acceptance criteria

### Technical Implementation Notes

From the tech spec, the certificate generation commands:

```bash
# Let's Encrypt (certbot)
certbot certonly --standalone \
  -d yourdomain.com \
  --email your@email.com \
  --agree-tos \
  --non-interactive \
  --cert-path /path/to/argusai/data/certs/

# Self-signed certificate
openssl req -x509 \
  -newkey rsa:2048 \
  -keyout data/certs/key.pem \
  -out data/certs/cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"
```

### Security Considerations

- Private keys should have 600 permissions (owner read/write only)
- Certificate files should have 644 permissions
- Never log or display private key contents
- Certbot requires port 80 to be available for HTTP-01 challenge

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/p9-5-2-add-certificate-generation-to-install-script.context.xml

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Added SSL certificate generation options to install.sh with three choices: Let's Encrypt, Self-signed, Skip
- Implemented `prompt_ssl_setup()` function displaying clear menu options
- Added `--ssl-only` flag for standalone SSL configuration on existing installations
- Implemented `setup_letsencrypt()` with certbot installation detection, domain/email prompts, and symlink creation
- Implemented `configure_cert_renewal()` creating systemd timer (Linux) and launchd plist (macOS)
- Implemented `generate_self_signed_cert()` using openssl with 2048-bit RSA key, 365-day validity, proper permissions
- Added `display_self_signed_warning()` with browser-specific instructions and trust store guidance
- Implemented `handle_ssl_skip()` with push notification HTTPS warning
- Added `update_env_ssl_config()` to update .env with SSL settings and HTTPS CORS origins
- Integrated SSL setup into main install flow after hostname prompt
- Updated `print_summary()` to show SSL configuration status

### File List

| File | Change |
|------|--------|
| install.sh | MODIFIED - Added SSL setup functions and prompts (~450 lines added) |
| docs/sprint-artifacts/p9-5-2-add-certificate-generation-to-install-script.md | CREATED - Story file |
| docs/sprint-artifacts/p9-5-2-add-certificate-generation-to-install-script.context.xml | CREATED - Story context |

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-23 | Story drafted from epics-phase9.md and tech-spec-epic-P9-5.md | Claude (YOLO workflow) |
| 2025-12-23 | Implementation complete - All 8 tasks completed | Claude (YOLO workflow) |
