# Live Object AI Classifier

AI-powered event detection and monitoring for home security. Analyzes video feeds from RTSP cameras and USB webcams, detects motion, and uses AI to generate natural language descriptions of detected events.

## Features

- **Multi-Camera Support**: RTSP IP cameras and USB/webcam support
- **Motion Detection**: Configurable sensitivity with detection zones
- **AI-Powered Descriptions**: Natural language event descriptions using Claude AI
- **Alert Rules**: Configure custom alert rules based on detected objects/events
- **Event Storage**: Persistent event storage with search and retention policies
- **Dashboard**: Real-time monitoring and event timeline
- **Webhook Integration**: Send alerts to external systems

## Camera Support

### RTSP Camera Setup

For IP cameras using RTSP protocol:

1. Navigate to "Cameras" → "Add Camera"
2. Select camera type: "RTSP Camera"
3. Enter camera details:
   - **Name**: Descriptive name (e.g., "Front Door Camera")
   - **RTSP URL**: Camera stream URL (e.g., `rtsp://192.168.1.50:554/stream1`)
   - **Username** (Optional): Camera authentication username
   - **Password** (Optional): Camera authentication password
   - **Frame Rate**: Capture rate (1-30 FPS)
4. Click "Test Connection" to verify connectivity
5. Save camera configuration

**Supported RTSP URLs:**
- `rtsp://192.168.1.50:554/stream1` (no auth)
- `rtsps://secure-camera.local:322/stream` (secure RTSP)

### USB Camera Setup

For USB webcams and built-in laptop cameras:

1. Navigate to "Cameras" → "Add Camera"
2. Select camera type: "USB Camera"
3. Enter camera details:
   - **Name**: Descriptive name (e.g., "Built-in Webcam")
   - **Device Index**: Camera device number (typically 0 for first camera, 1 for second, etc.)
   - **Frame Rate**: Capture rate (1-30 FPS)
4. Click "Test Connection" to verify camera is accessible
5. Save camera configuration

#### Device Index Selection

- **Device Index 0**: First/primary camera (typically built-in laptop camera)
- **Device Index 1**: Second camera (typically first external USB webcam)
- **Device Index 2+**: Additional cameras in order of connection

**Finding Available Devices:**

The system automatically enumerates USB cameras during detection. Common configurations:
- **MacBook with FaceTime camera**: Device 0
- **MacBook + External USB webcam**: Device 0 (FaceTime), Device 1 (USB)
- **Desktop + Multiple USB cameras**: Device 0, 1, 2, 3...

#### Troubleshooting USB Cameras

**Device Not Found**
- Verify camera is physically connected via USB
- Try a different USB port
- Check device index (try 0, 1, 2)
- Restart the application

**Permission Denied (Linux)**
```bash
# Add user to 'video' group for camera access
sudo usermod -a -G video $USER

# Log out and log back in for changes to take effect
```

**Camera Already in Use**
- Close other applications using the camera (Zoom, Skype, etc.)
- Only one application can access a USB camera at a time
- Check browser tabs with active camera access

**Platform-Specific Notes:**

**macOS:**
- Built-in FaceTime camera: Usually device index 0
- No special permissions needed
- Supports hot-plug (connect/disconnect while running)

**Linux:**
- Uses Video4Linux2 (V4L2) backend
- Device paths: `/dev/video0`, `/dev/video1`, etc.
- Requires user in 'video' group for permissions
- Some cameras require udev rules for access

**Windows:**
- Uses DirectShow backend (basic support)
- macOS and Linux are primary supported platforms

#### Tested USB Cameras

- **Built-in laptop cameras** (MacBook FaceTime, Dell/Lenovo/HP webcams)
- **Logitech C920** HD Pro Webcam
- **Logitech C270** HD Webcam
- Most UVC-compliant USB cameras should work

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL or SQLite
- OpenCV dependencies (auto-installed)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload
```

Backend runs at: `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL
cp .env.local.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Frontend runs at: `http://localhost:3000`

## Project Structure

```
live-object-ai-classifier/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # REST API endpoints
│   │   ├── models/    # Database models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # Business logic (camera, motion detection)
│   └── tests/         # Backend tests (65 tests, 100% pass rate)
├── frontend/          # Next.js frontend
│   ├── app/           # App router pages
│   ├── components/    # React components
│   └── lib/           # API client, utilities
└── docs/              # Project documentation
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test suite
pytest tests/test_services/test_camera_service.py -v
```

**Test Coverage:** 65 tests, 100% pass rate, 80%+ code coverage

### Frontend Tests

Manual testing currently required. Automated testing planned for future release.

## License

MIT
