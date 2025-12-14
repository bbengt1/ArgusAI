# Data Architecture

## Database Schema

**cameras** table:
```sql
CREATE TABLE cameras (
    id TEXT PRIMARY KEY,                    -- UUID
    name TEXT NOT NULL,                     -- User-friendly name
    type TEXT NOT NULL,                     -- 'rtsp' or 'usb'
    rtsp_url TEXT,                          -- RTSP URL (nullable for USB)
    username TEXT,                          -- RTSP auth username
    password TEXT,                          -- RTSP auth password (encrypted)
    device_index INTEGER,                   -- USB device index (nullable for RTSP)
    frame_rate INTEGER DEFAULT 5,           -- Capture FPS
    is_enabled BOOLEAN DEFAULT TRUE,        -- Active/inactive
    motion_sensitivity TEXT DEFAULT 'medium', -- 'low', 'medium', 'high'
    motion_cooldown INTEGER DEFAULT 60,     -- Seconds between motion triggers
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**events** table:
```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,                    -- UUID
    camera_id TEXT NOT NULL,                -- FK to cameras.id
    timestamp TIMESTAMP NOT NULL,           -- When motion detected
    description TEXT NOT NULL,              -- AI-generated description
    confidence INTEGER,                     -- 0-100 confidence score
    objects_detected TEXT,                  -- JSON array: ["person", "package"]
    thumbnail_path TEXT,                    -- Relative path to thumbnail image
    alert_triggered BOOLEAN DEFAULT FALSE,  -- Was any alert triggered?
    alert_rule_ids TEXT,                    -- JSON array of triggered rule IDs
    user_feedback TEXT,                     -- Optional user rating/feedback
    is_manual BOOLEAN DEFAULT FALSE,        -- Manual analysis vs motion-triggered
    processing_time_ms INTEGER,             -- Time to process (performance metric)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (camera_id) REFERENCES cameras(id) ON DELETE CASCADE
);

CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_camera_id ON events(camera_id);
CREATE INDEX idx_events_alert_triggered ON events(alert_triggered);
```

**alert_rules** table:
```sql
CREATE TABLE alert_rules (
    id TEXT PRIMARY KEY,                    -- UUID
    name TEXT NOT NULL,                     -- Rule name
    is_enabled BOOLEAN DEFAULT TRUE,        -- Active/inactive
    conditions TEXT NOT NULL,               -- JSON object with rule logic
    actions TEXT NOT NULL,                  -- JSON object with action config
    cooldown_minutes INTEGER DEFAULT 30,    -- Cooldown between alerts
    last_triggered_at TIMESTAMP,            -- Last time rule matched
    trigger_count INTEGER DEFAULT 0,        -- How many times triggered
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Conditions JSON structure:**
```json
{
  "object_types": ["person", "package"],      // OR logic
  "confidence_min": 70,                       // Minimum confidence threshold
  "time_range": {
    "start": "09:00",                         // Start time (HH:MM)
    "end": "18:00"                            // End time (HH:MM)
  },
  "days_of_week": [1, 2, 3, 4, 5],           // Mon=1, Sun=7
  "cameras": ["camera-uuid-1"],               // Specific cameras or empty for all
  "keywords": ["delivery", "package"]         // Description must contain (optional)
}
```

**Actions JSON structure:**
```json
{
  "dashboard_notification": true,             // Show in notification bell
  "webhook_url": "https://example.com/hook",  // HTTP POST target
  "webhook_headers": {                        // Custom headers for webhook
    "Authorization": "Bearer token123"
  }
}
```

**users** table (Phase 1.5):
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,                    -- UUID
    username TEXT UNIQUE NOT NULL,          -- Login username
    email TEXT UNIQUE,                      -- Email (optional for MVP)
    hashed_password TEXT NOT NULL,          -- bcrypt hash
    is_active BOOLEAN DEFAULT TRUE,         -- Account enabled/disabled
    is_admin BOOLEAN DEFAULT FALSE,         -- Admin privileges
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**system_settings** table:
```sql
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,                   -- Setting name (unique)
    value TEXT NOT NULL,                    -- JSON-encoded value
    description TEXT,                       -- Human-readable description
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Example settings:**
- `ai_model_primary`: `"openai"`
- `ai_api_key_openai`: `"encrypted:..."` (Fernet encrypted)
- `data_retention_days`: `"30"`
- `timezone`: `"America/New_York"`

## Data Relationships

```
cameras (1) ──────< events (many)
                    │
                    └───> alert_rules (many-to-many via alert_rule_ids JSON array)
                    
users (1) ──────< events (many) [Phase 2: multi-user]
```

---
