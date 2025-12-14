# Security Architecture

## Authentication Flow (Phase 1.5)

1. User submits username/password to `/api/v1/login`
2. Backend validates credentials (bcrypt comparison)
3. Backend generates JWT token with 24h expiration
4. Backend sets HTTP-only cookie with token
5. Frontend receives user data and stores in AuthContext
6. Subsequent requests include cookie automatically
7. Backend validates JWT on protected endpoints

**JWT Payload:**
```json
{
  "sub": "user-uuid",
  "username": "john_doe",
  "exp": 1731686400,
  "iat": 1731600000
}
```

## API Key Encryption

AI API keys stored encrypted in database:

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

## Input Validation

**Backend:**
- Pydantic schemas validate all request bodies
- Path parameters validated by type hints
- SQL injection prevented by SQLAlchemy ORM
- RTSP URL validation (format, protocol)

**Frontend:**
- React Hook Form + Zod for form validation
- API responses validated against TypeScript types
- XSS prevention: React auto-escapes by default
- CSRF protection: HTTP-only cookies + SameSite attribute

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production:** Replace with actual domain, restrict methods to needed ones.

---
