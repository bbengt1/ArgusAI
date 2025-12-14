# Project Initialization

**First implementation story should execute:**

## Frontend Setup
```bash
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --eslint \
  --app \
  --no-src-dir \
  --import-alias "@/*"

cd frontend
npm install lucide-react date-fns
npx shadcn-ui@latest init
```

## Backend Setup
```bash
mkdir backend && cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install "fastapi[standard]" \
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
  httpx

# Initialize Alembic for migrations
alembic init alembic
```

**This establishes the base architecture with:**
- TypeScript, Tailwind CSS, ESLint (frontend)
- FastAPI, SQLAlchemy, OpenCV (backend)
- Async I/O support throughout
- Type safety on both sides

---
