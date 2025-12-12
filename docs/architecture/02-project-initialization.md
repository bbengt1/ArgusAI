# Project Initialization

[← Back to Architecture Index](./README.md) | [← Previous: Executive Summary](./01-executive-summary.md) | [Next: Technology Stack →](./03-technology-stack.md)

---

## First Implementation Story

**The project initialization commands below should be the FIRST implementation story.**

This establishes the base architecture with all starter templates, dependencies, and configurations needed for development.

---

## Frontend Setup

### Step 1: Create Next.js Application

```bash
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"
```

**What this provides:**
- ✅ Next.js 15.x with App Router
- ✅ TypeScript 5.x configuration
- ✅ Tailwind CSS 3.x setup
- ✅ ESLint with Next.js rules
- ✅ Import alias `@/*` → root directory

### Step 2: Install Additional Dependencies

```bash
cd frontend

# UI Component library (shadcn/ui)
npx shadcn-ui@latest init

# Additional packages
npm install lucide-react date-fns
```

**Packages installed:**
- `lucide-react` - Icon library (consistent, lightweight)
- `date-fns` - Date formatting and manipulation

### Step 3: Install shadcn/ui Components

```bash
# Install core UI components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add form
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add select
npx shadcn-ui@latest add table
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add toast
```

**Note:** More components can be added as needed during development.

### Step 4: Configure Environment Variables

Create `.env.local`:

```bash
# Frontend environment variables
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Step 5: Verify Frontend Setup

```bash
npm run dev
```

**Expected result:**
- Development server starts at `http://localhost:3000`
- Default Next.js welcome page displays
- No TypeScript errors
- Tailwind CSS working

---

## Backend Setup

### Step 1: Create Project Structure

```bash
mkdir backend
cd backend
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Core Dependencies

```bash
# Install FastAPI with all standard dependencies
pip install "fastapi[standard]"

# Install additional packages
pip install \
  opencv-python \
  sqlalchemy \
  alembic \
  python-jose[cryptography] \
  passlib[bcrypt] \
  python-multipart \
  openai \
  google-generativeai \
  anthropic \
  cryptography \
  httpx \
  python-dotenv
```

**Key packages:**
- `fastapi[standard]` - FastAPI + Uvicorn + Pydantic + email-validator + httpx + jinja2 + python-multipart
- `opencv-python` - Camera capture and motion detection
- `sqlalchemy` - ORM for database
- `alembic` - Database migrations
- `python-jose` - JWT token handling
- `passlib` - Password hashing
- `openai`, `google-generativeai`, `anthropic` - AI model SDKs
- `cryptography` - API key encryption (Fernet)
- `httpx` - Async HTTP client for webhooks

### Step 4: Create requirements.txt

```bash
pip freeze > requirements.txt
```

**Sample requirements.txt:**
```txt
fastapi[standard]==0.115.0
uvicorn[standard]==0.30.0
opencv-python==4.10.0.84
sqlalchemy==2.0.35
alembic==1.13.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
openai==1.51.0
google-generativeai==0.8.2
anthropic==0.39.0
cryptography==43.0.1
httpx==0.27.2
python-dotenv==1.0.1
```

**Note:** Versions will be latest at time of installation. Pin after testing.

### Step 5: Initialize Alembic (Database Migrations)

```bash
# Initialize Alembic
alembic init alembic
```

**Configure `alembic.ini`:**
```ini
# Edit alembic.ini, change this line:
sqlalchemy.url = sqlite:///data/app.db
```

**Configure `alembic/env.py`:**
```python
# Add at top after imports:
from app.core.config import settings
from app.models import *  # Import all models

# Replace 'target_metadata = None' with:
from app.models.base import Base
target_metadata = Base.metadata

# Update the sqlalchemy.url line in run_migrations_offline():
config.set_main_option('sqlalchemy.url', str(settings.DATABASE_URL))
```

### Step 6: Create Initial Project Structure

```bash
# Create main directories
mkdir -p app/{api/v1,core,models,schemas,services,utils}
mkdir -p data/{thumbnails,logs}
mkdir -p tests/{test_api,test_services}

# Create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py
```

### Step 7: Configure Environment Variables

Create `.env`:

```bash
# Backend environment variables

# Application
APP_NAME=ArgusAI
DEBUG=True

# Database
DATABASE_URL=sqlite:///data/app.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ENCRYPTION_KEY=your-fernet-key-here-generate-with-cryptography
JWT_SECRET_KEY=your-jwt-secret-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# AI Providers (leave empty initially, users configure via UI)
OPENAI_API_KEY=
GOOGLE_API_KEY=
ANTHROPIC_API_KEY=

# CORS
CORS_ORIGINS=http://localhost:3000
```

**Generate encryption keys:**
```python
# Run this in Python to generate keys:
from cryptography.fernet import Fernet
import secrets

print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
print(f"ENCRYPTION_KEY={Fernet.generate_key().decode()}")
print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")
```

### Step 8: Create Basic FastAPI App

Create `main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="ArgusAI API",
    version="1.0.0",
    description="Event-driven AI-powered camera monitoring"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ArgusAI API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-11-15T10:30:00Z"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Create `app/core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "ArgusAI"
    DEBUG: bool = False
    
    DATABASE_URL: str = "sqlite:///data/app.db"
    
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440
    
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Step 9: Verify Backend Setup

```bash
# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected result:**
- Server starts at `http://localhost:8000`
- Navigate to `http://localhost:8000` → See welcome message
- Navigate to `http://localhost:8000/docs` → See Swagger UI
- Navigate to `http://localhost:8000/health` → See health check response
- No errors in console

---

## Create .gitignore Files

### Root .gitignore

Create `.gitignore` in project root:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# Node
node_modules/
.next/
out/
build/
dist/

# Environment variables
.env
.env.local
.env.*.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Data directories
backend/data/
!backend/data/.gitkeep

# Logs
*.log
logs/

# Testing
.coverage
htmlcov/
.pytest_cache/

# Temporary
*.tmp
*.temp
```

### Keep data directories

```bash
# Create .gitkeep files to preserve empty directories
touch backend/data/.gitkeep
touch backend/data/thumbnails/.gitkeep
touch backend/data/logs/.gitkeep
```

---

## Development Workflow

### Terminal Setup (Recommended)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Database/Utilities:**
```bash
cd backend
source venv/bin/activate
# Run migrations, create test data, etc.
```

### Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation (Swagger):** http://localhost:8000/docs
- **API Documentation (ReDoc):** http://localhost:8000/redoc

---

## Verification Checklist

### Frontend Verification
- [ ] Next.js development server starts without errors
- [ ] TypeScript compilation successful
- [ ] Tailwind CSS working (default styles visible)
- [ ] shadcn/ui components installed
- [ ] Environment variables loaded

### Backend Verification
- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] FastAPI server starts without errors
- [ ] Swagger UI accessible at `/docs`
- [ ] Health check endpoint returns 200 OK
- [ ] CORS configured for frontend origin

### Project Structure Verification
- [ ] Directory structure matches architecture specification
- [ ] `.gitignore` files prevent committing sensitive data
- [ ] Environment variable files exist (`.env`, `.env.local`)
- [ ] Data directories created with `.gitkeep` files

---

## Common Setup Issues

### Issue: Python version too old

**Error:** `python3: command not found` or version < 3.11

**Solution:**
```bash
# macOS (using Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# Verify
python3.11 --version
```

### Issue: OpenCV installation fails

**Error:** `Could not build wheels for opencv-python`

**Solution:**
```bash
# macOS
brew install opencv

# Ubuntu/Debian
sudo apt install libopencv-dev python3-opencv

# Try headless version if GUI not needed
pip install opencv-python-headless
```

### Issue: Node.js version too old

**Error:** `Node.js version 20.9.0 or higher is required`

**Solution:**
```bash
# Using nvm (Node Version Manager)
nvm install 20
nvm use 20

# Or download from nodejs.org
```

### Issue: Port already in use

**Error:** `OSError: [Errno 48] Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --reload --port 8001
```

---

## Next Steps After Initialization

1. **Create Database Models** - Define SQLAlchemy models for cameras, events, alert_rules
2. **Create Initial Migration** - `alembic revision --autogenerate -m "initial schema"`
3. **Run Migration** - `alembic upgrade head`
4. **Build API Endpoints** - Start with camera CRUD operations
5. **Build Frontend Pages** - Start with camera management UI

---

[← Previous: Executive Summary](./01-executive-summary.md) | [Next: Technology Stack →](./03-technology-stack.md) | [Back to Index](./README.md)
