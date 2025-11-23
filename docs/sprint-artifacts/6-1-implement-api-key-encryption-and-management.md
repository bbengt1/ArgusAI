# Story 6.1: Implement API Key Encryption and Management

Status: ready-for-dev

## Story

As a **developer**,
I want **sensitive data (API keys, passwords) encrypted at rest**,
so that **the system is secure even if the database is compromised**.

## Acceptance Criteria

1. **Fernet Encryption Implementation** - Strong symmetric encryption for sensitive data
   - Algorithm: Fernet (symmetric encryption from `cryptography` library)
   - Key: 32-byte key derived from environment variable `ENCRYPTION_KEY`
   - Key generation: `Fernet.generate_key()` on first setup
   - Stored encrypted: API keys, camera passwords, webhook auth headers
   - Decrypted: Only when needed for API calls, never logged
   - [Source: docs/epics.md#Story-6.1]

2. **Encryption Key Management** - Secure key storage and lifecycle
   - Encryption key stored in environment variable (never in code/database)
   - Docker: Pass as environment variable or Docker secret
   - First run: Generate encryption key if not present
   - Save to `.env` file or display to user for manual configuration
   - Validation: Check encryption key is valid Fernet key on startup
   - Error: Exit with clear message if key missing or invalid
   - [Source: docs/epics.md#Story-6.1, docs/architecture.md#Security-Architecture]

3. **Encryption Utility Functions** - Reusable encryption module
   - `encrypt(plaintext: str) -> str`: Returns base64-encoded ciphertext
   - `decrypt(ciphertext: str) -> str`: Returns original plaintext
   - Utility module: `/backend/app/core/encryption.py`
   - Used by: Camera service, AI service, Webhook service
   - [Source: docs/epics.md#Story-6.1]

4. **Database Storage Encryption** - Encrypted sensitive fields at rest
   - Camera passwords: Encrypted before INSERT/UPDATE
   - AI API keys: Encrypted in system_settings
   - Webhook headers: Encrypted in alert_rules actions JSON
   - Retrieved as encrypted, decrypted in memory when used
   - [Source: docs/epics.md#Story-6.1, docs/prd.md#F7.2]

5. **API Key Validation Endpoint** - Test keys before saving
   - `POST /api/v1/ai/test-key` accepts key and model provider
   - Encrypts key temporarily (not stored)
   - Sends test request to AI API
   - Returns validation result (success/failure with message)
   - No key persistence unless user saves settings
   - [Source: docs/epics.md#Story-6.1, docs/prd.md#F7.2]

6. **Security Best Practices** - Prevent credential exposure
   - Never log decrypted values (mask in logs: `key=****`)
   - Clear decrypted values from memory after use
   - No decrypted values in error messages or stack traces
   - Encryption failures → Graceful error handling with user-friendly message
   - [Source: docs/epics.md#Story-6.1, docs/architecture.md#Security-Architecture]

## Tasks / Subtasks

- [ ] Task 1: Create encryption utility module (AC: #1, #3)
  - [ ] Create `/backend/app/core/encryption.py` with Fernet implementation
  - [ ] Implement `encrypt(plaintext: str) -> str` function
  - [ ] Implement `decrypt(ciphertext: str) -> str` function
  - [ ] Add `is_encrypted(value: str) -> bool` helper to detect encrypted values
  - [ ] Add `get_encryption_key() -> bytes` to load key from environment
  - [ ] Handle InvalidToken exception with clear error message

- [ ] Task 2: Add encryption key configuration and validation (AC: #2)
  - [ ] Add `ENCRYPTION_KEY` to `/backend/app/core/config.py` Pydantic Settings
  - [ ] Create startup validation to check encryption key format
  - [ ] Implement key generation script: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
  - [ ] Update `.env.example` with `ENCRYPTION_KEY=your-32-byte-fernet-key-here`
  - [ ] Add startup error handling: Exit with clear message if key missing/invalid
  - [ ] Document key generation in README or SETUP guide

- [ ] Task 3: Integrate encryption with Camera service (AC: #4)
  - [ ] Modify camera password handling in `/backend/app/api/v1/cameras.py`
  - [ ] Encrypt camera passwords on POST/PUT before database save
  - [ ] Decrypt passwords when camera connection is established
  - [ ] Update camera response schema to mask passwords (show `****`)
  - [ ] Handle existing unencrypted passwords (migration path)

- [ ] Task 4: Integrate encryption with AI API keys in settings (AC: #4)
  - [ ] Modify `/backend/app/api/v1/settings.py` for AI key handling
  - [ ] Encrypt AI API keys before saving to system_settings
  - [ ] Decrypt keys when AI service needs them for API calls
  - [ ] Update settings response to mask API keys (show only last 4 chars)
  - [ ] Handle keys for all providers: OpenAI, Anthropic, Google

- [ ] Task 5: Integrate encryption with webhook auth headers (AC: #4)
  - [ ] Modify webhook header storage in alert_rules actions JSON
  - [ ] Encrypt Authorization headers and custom auth values
  - [ ] Decrypt when webhook is triggered and headers are sent
  - [ ] Update alert rule response to mask sensitive headers

- [ ] Task 6: Implement API key test endpoint (AC: #5)
  - [ ] Create `POST /api/v1/ai/test-key` endpoint in `/backend/app/api/v1/settings.py`
  - [ ] Accept request body: `{"provider": "openai|anthropic|google", "api_key": "sk-..."}`
  - [ ] Make lightweight test API call to validate key works
  - [ ] Return `{"valid": true, "message": "API key validated successfully"}` or error details
  - [ ] Do NOT persist key - only test and return result
  - [ ] Add rate limiting to prevent abuse (max 10 tests/minute)

- [ ] Task 7: Add logging security measures (AC: #6)
  - [ ] Create `mask_sensitive(value: str, show_chars: int = 4) -> str` utility
  - [ ] Update all logging to mask API keys and passwords
  - [ ] Audit existing log statements for credential exposure
  - [ ] Add sanitization to error handlers to prevent key leakage

- [ ] Task 8: Create database migration for existing data (AC: #4)
  - [ ] Create one-time migration script to encrypt existing plaintext values
  - [ ] Encrypt existing camera passwords in cameras table
  - [ ] Encrypt existing AI API keys in system_settings table
  - [ ] Add `encrypted_at` timestamp column to track encryption status (optional)
  - [ ] Make migration idempotent (safe to run multiple times)

- [ ] Task 9: Update frontend settings UI for key management (AC: #5)
  - [ ] Add "Test API Key" button next to each provider key input
  - [ ] Call `POST /api/v1/ai/test-key` when button clicked
  - [ ] Show loading spinner during test
  - [ ] Display success (green checkmark) or error (red X with message)
  - [ ] Only enable "Save" after successful test (optional enhancement)

- [ ] Task 10: Testing and validation (AC: #1-6)
  - [ ] Write unit tests for encryption utility functions
  - [ ] Test encrypt/decrypt round-trip with various inputs
  - [ ] Test key validation (invalid key, missing key, wrong format)
  - [ ] Test API key test endpoint with mock AI services
  - [ ] Test integration with camera, settings, and webhook services
  - [ ] Verify logs do not contain plaintext credentials
  - [ ] Run `npm run build` and `npm run lint` to verify frontend builds
  - [ ] Run pytest to verify backend tests pass

## Dev Notes

### Architecture Context

From `docs/architecture.md`:
- **API Key Encryption**: Fernet (symmetric) via cryptography lib for secure storage of AI API keys [Source: docs/architecture.md#Security-Architecture]
- **Security Architecture**: "AI API keys stored encrypted in database" using Fernet symmetric encryption [Source: docs/architecture/09-security-architecture.md]
- **Backend Encryption Module**: `/backend/app/utils/encryption.py` for Fernet encrypt/decrypt utilities [Source: docs/architecture.md#Project-Structure]

**Implementation Pattern from Architecture:**
```python
from cryptography.fernet import Fernet

# Generate key (store in environment variable)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY)

# Encrypt API key before storing
encrypted_key = fernet.encrypt(api_key.encode())
setting.value = f"encrypted:{encrypted_key.decode()}"

# Decrypt when needed
if setting.value.startswith("encrypted:"):
    encrypted_key = setting.value[10:]  # Remove "encrypted:" prefix
    api_key = fernet.decrypt(encrypted_key.encode()).decode()
```

### Learnings from Previous Story

**From Story 5.4: Build In-Dashboard Notification Center (Status: done)**

- **API Client Pattern**: Extended `api-client.ts` with new namespace - follow same pattern if frontend API calls needed
- **Backend Service Integration**: Modified `alert_engine.py` for notification creation - similar pattern for encryption integration
- **Component Exports**: Used index.ts for component barrel exports
- **No Technical Debt or Pending Issues**: Previous story completed cleanly

[Source: docs/sprint-artifacts/5-4-build-in-dashboard-notification-center.md#Dev-Agent-Record]

### Technical Implementation Notes

**Encryption Key Format:**
- Fernet key: 44-byte base64-encoded string (32 bytes decoded)
- Generated via: `Fernet.generate_key()`
- Must be stored securely in environment variable

**Existing Encryption References:**
The architecture documents and earlier stories (2.3, 3.1) mention password encryption:
- Story 2.3: "Password encrypted before storage using Fernet symmetric encryption"
- Story 3.1: "API key stored encrypted in database"

This story consolidates and implements the encryption infrastructure that was referenced but not yet built.

**Files to Create/Modify:**
- `/backend/app/core/encryption.py` (NEW) - Core encryption utilities
- `/backend/app/core/config.py` (MODIFY) - Add ENCRYPTION_KEY setting
- `/backend/app/api/v1/cameras.py` (MODIFY) - Encrypt camera passwords
- `/backend/app/api/v1/settings.py` (MODIFY) - Encrypt AI keys, add test endpoint
- `/backend/app/services/alert_engine.py` (MODIFY) - Decrypt webhook headers when needed
- `/frontend/app/settings/page.tsx` (MODIFY) - Add "Test API Key" button

### Project Structure Notes

- Alignment with unified project structure:
  - Encryption module at `/backend/app/core/encryption.py` (core utilities)
  - Settings at `/backend/app/core/config.py` (Pydantic Settings)
  - API routes following existing patterns in `/backend/app/api/v1/`
- Detected conflicts or variances: None - architecture specifies `app/utils/encryption.py` but `app/core/` is more appropriate for security utilities given existing structure

### Security Considerations

- **Never commit encryption keys** - Add to .gitignore
- **Key rotation**: Phase 2 feature - will require re-encrypting all values
- **Memory handling**: Use `del` to clear decrypted values after use where possible
- **Error messages**: Never include the key value or full encrypted string in errors
- **Logging**: All log statements must use masking utility

### References

- [PRD: F7.2 - API Key Management](../prd.md#F7-Authentication-Security)
- [Architecture: Security Architecture](../architecture.md#Security-Architecture)
- [Architecture: API Key Encryption](../architecture/09-security-architecture.md)
- [Epics: Story 6.1](../epics.md#Story-6.1)
- [Story 5.4: Notification Center](./5-4-build-in-dashboard-notification-center.md) - Previous story patterns

## Dev Agent Record

### Context Reference

- `docs/sprint-artifacts/6-1-implement-api-key-encryption-and-management.context.xml`

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Version | Description |
|------|---------|-------------|
| 2025-11-23 | 1.0 | Story drafted from epics.md, PRD F7.2, and architecture security docs |
