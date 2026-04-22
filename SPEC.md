# Telegram Automation Bot — SPEC

**Version:** 1.0  
**Date:** 2026-04-22  
**Status:** DRAFT

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │ Bot Core    │  │ Handlers    │  │ Alert Engine         ││
│  │ (python-    │  │ /start,     │  │ Trigger eval,       ││
│  │ telegram-   │  │ /broadcast, │  │ notification prep   ││
│  │ bot)        │  │ etc.        │  │                     ││
│  └─────────────┘  └─────────────┘  └─────────────────────┘│
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │      FastAPI Layer        │
              │  POST /webhook/github    │
              │  POST /webhook/alert     │
              │  GET  /health            │
              │  GET  /stats             │
              └─────────────┬─────────────┘
                            │
              ┌─────────────┴─────────────┐
              │      SQLite / SQLAlchemy    │
              │   Users, AlertRules,        │
              │   AlertLogs                │
              └───────────────────────────┘
```

---

## 2. Database Schema

### 2.1 Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 AlertRules Table
```sql
CREATE TABLE alert_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK (trigger_type IN ('cron', 'event', 'manual')),
    trigger_config JSON NOT NULL,
    message_template TEXT NOT NULL,
    target_chat_id INTEGER NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users (user_id)
);
```

### 2.3 AlertLogs Table
```sql
CREATE TABLE alert_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,
    triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME,
    status TEXT NOT NULL CHECK (status IN ('pending', 'sent', 'failed')),
    error_msg TEXT,
    payload JSON,
    FOREIGN KEY (rule_id) REFERENCES alert_rules (rule_id)
);
```

---

## 3. API Specification

### 3.1 Telegram Commands

| Command | Args | Description | Auth |
|---------|------|-------------|------|
| `/start` | — | Register user | All |
| `/help` | — | Show help | All |
| `/status` | — | Bot stats | All |
| `/ping` | — | Latency check | All |
| `/broadcast` | `<message>` | Send to all users | Admin |
| `/alert` | `add/list/delete/enable/disable` | Manage alerts | Admin |

### 3.2 Webhook Endpoints

#### POST /webhook/github
**Purpose:** Receive GitHub webhook events  
**Headers:**
- `X-Hub-Signature-256`: HMAC signature for validation
- `X-GitHub-Event`: Event type (push, pull_request, issues)

**Request Body:** GitHub webhook payload (JSON)

**Response:**
- `200 OK` — Event processed
- `401 Unauthorized` — Invalid signature
- `400 Bad Request` — Invalid payload

**Logic:**
```
1. Validate X-Hub-Signature-256 against GITHUB_WEBHOOK_SECRET
2. If invalid → return 401
3. Parse X-GitHub-Event to determine event type
4. Build alert payload from webhook body
5. Query AlertRules where trigger_type='event' AND matching config
6. For each matching rule → trigger alert
7. Return 200
```

#### POST /webhook/alert
**Purpose:** Manual alert trigger (internal API)  
**Request Body:**
```json
{
  "alert_id": 123,
  "payload": {
    "message": "Custom alert message"
  }
}
```

**Response:**
- `200 OK` — Alert triggered
- `404 Not Found` — Alert rule not found
- `400 Bad Request` — Invalid payload

#### GET /health
**Purpose:** Health check endpoint  
**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "timestamp": "2026-04-22T10:30:00Z"
}
```

#### GET /stats
**Purpose:** Bot statistics  
**Response:**
```json
{
  "total_users": 42,
  "active_users": 38,
  "total_alert_rules": 15,
  "enabled_rules": 12,
  "total_alerts_sent": 1567,
  "alerts_failed": 3
}
```

---

## 4. Sequence Diagrams

### 4.1 User Registration
```
User          Bot           Database
  │            │              │
  │──/start───▶│              │
  │            │──INSERT─────▶│
  │            │◀──user_id─────│
  │◀─welcome──│              │
  │            │              │
```

### 4.2 Alert Trigger (GitHub Webhook)
```
GitHub   FastAPI   AlertEngine   Telegram   DB
  │        │          │           │         │
  │──POST──▶│        │           │         │
  │        │──valid─▶│           │         │
  │        │        │──query────▶│         │
  │        │        │◀─rules─────│         │
  │        │        │──eval──────│         │
  │        │        │──send────▶│         │
  │        │        │            │         │
  │◀─200───│        │           │         │
  │        │        │──INSERT───▶│         │
  │        │        │            │         │
```

### 4.3 Broadcast Flow
```
Admin    Bot      DB         Queue    Telegram
  │       │        │           │         │
  │──/broadcast───▶│          │         │
  │       │──SELECT─▶│        │         │
  │       │◀──users──│        │         │
  │       │        │──push───▶│         │
  │       │        │  429?    │         │
  │       │        │◀─retry──│         │
  │       │        │          │◀─send───┼──┘
  │◀─sent───────────│          │         │
  │       │        │          │         │
```

### 4.4 Rate Limit Handling
```
Bot       Telegram API    Queue
  │           │            │
  │──send────▶│            │
  │      ◀─429────────────│
  │           │            │
  │           │──push───▶│
  │           │            │
  │──wait 1s──│            │
  │──retry──▶│            │
  │      ◀─429────────────│
  │           │            │
  │           │──update───▶│
  │           │            │
  │──wait 2s──│            │
  │──retry──▶│            │
  │      ◀─200────────────│
  │           │            │
  │           │──remove───▶│
  │           │            │
```

---

## 5. Configuration Reference

### 5.1 Environment Variables
```bash
# Required
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxyz123456789

# Optional
TELEGRAM_BOT_DEBUG=false
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
DATABASE_URL=sqlite:///./data/bot.db
LOG_LEVEL=INFO
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_PORT=8080
```

### 5.2 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config.py .

EXPOSE 8000 8080

VOLUME ["/app/data"]

CMD ["python", "src/bot.py"]
```

### 5.3 docker-compose.yml
```yaml
version: '3.8'
services:
  bot:
    build: .
    ports:
      - "8000:8000"
      - "8080:8080"
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 6. Error Codes

| Code | Meaning | Handling |
|------|---------|----------|
| 401 | Unauthorized (invalid signature) | Log attempt, return 401 |
| 429 | Telegram rate limit | Exponential backoff, queue |
| 400 | Bad request (invalid payload) | Log error, return 400 |
| 500 | Internal server error | Log full trace, alert admin |
| 503 | Service unavailable (DB down) | Retry 3x, then alert admin |

---

## 7. Security Considerations

1. **GitHub Webhook Validation:** All webhooks validated via HMAC-SHA256 signature
2. **Admin Commands:** Only users with `is_admin=True` can execute broadcast/admin commands
3. **Environment Variables:** Sensitive data (tokens, secrets) via environment, never in code
4. **Database:** SQLite file permissions restrict access to bot user only

---

## 8. Dependencies

```
python-telegram-bot>=20.0
fastapi>=0.100.0
uvicorn>=0.22.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

---

## 9. File Structure

```
telegram-automation-bot/
├── BRIEF.md
├── TASKS.md
├── SPEC.md                    ← This file
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   ├── __init__.py
│   ├── bot.py                # Main entry point
│   ├── config.py             # Environment config
│   ├── handlers.py           # Telegram command handlers
│   ├── models.py             # SQLAlchemy models
│   ├── database.py           # DB connection
│   ├── alert_engine.py       # Alert evaluation + sending
│   ├── api.py                # FastAPI webhooks
│   └── utils.py              # Helpers
└── tests/
    ├── __init__.py
    ├── test_handlers.py
    ├── test_models.py
    ├── test_alert_engine.py
    └── conftest.py
```
