# Telegram Automation Bot — TASKS

**Version:** 1.0  
**Date:** 2026-04-22  
**Assignee:** Team  

---

## Agent Assignments

| Agent | Role | Tasks |
|-------|------|-------|
| Thomas | Backend Developer | TASK-001 → TASK-008 |
| Goksu | QA Engineer | TASK-009 → TASK-012 |
| Elisa | PO + Coordinator | TASK-013 → TASK-015 |
| Piotr | DevOps + Docker | TASK-016 → TASK-018 |

---

## TASK-001: Setup Python Project
**Assignee:** Thomas  
**Priority:** HIGH  
**Description:**
- Initialize Python project with `python-telegram-bot` v20+
- Setup virtual environment
- Install dependencies: `python-telegram-bot`, `fastapi`, `uvicorn`, `sqlalchemy`, `aiosqlite`
- Create project structure:
  ```
  src/
    __init__.py
    bot.py           # Main bot entry point
    handlers.py      # Command handlers
    models.py        # SQLAlchemy models
    database.py      # DB connection + session
    api.py           # FastAPI webhooks
  tests/
    test_handlers.py
    test_models.py
  config.py          # Environment variables
  Dockerfile
  docker-compose.yml
  requirements.txt
  ```
- Create `.env.example` with all environment variables

**Acceptance Criteria:**
- `python -c "import telegram; print(telegram.__version__)"` works
- `uvicorn src.api:app --reload` starts without errors

---

## TASK-002: Implement Bot Core (Dispatcher + Handlers)
**Assignee:** Thomas  
**Priority:** HIGH  
**Dependencies:** TASK-001  
**Description:**
- Setup `Application` from python-telegram-bot
- Add dispatcher with command handlers
- Setup logging
- Add error handler for unexpected errors

**Acceptance Criteria:**
- Bot starts without errors
- `/ping` responds with latency info
- Unknown commands return "Command not found"

---

## TASK-003: Command Handlers (/start, /help, /status, /ping)
**Assignee:** Thomas  
**Priority:** HIGH  
**Dependencies:** TASK-002  
**Description:**
Implementare tutti i comandi base:

- `/start` — Registra utente, mostra welcome message
- `/help` — Lista comandi disponibili  
- `/status` — Mostra stato bot + statistiche (uptime, active rules, sent notifications)
- `/ping` — Risponde "pong" + calcola latenza

**Acceptance Criteria:**
- `/start` crea record in User DB se non esiste
- `/help`elenco formattato con comandi e descrizioni
- `/status` mostra dati reali dal DB
- `/ping` calcola latenza round-trip

---

## TASK-004: AlertRule Entity + CRUD
**Assignee:** Thomas  
**Priority:** HIGH  
**Dependencies:** TASK-002  
**Description:**
- SQLAlchemy model per AlertRule
- CRUD operations: create, read, update, delete
- `/alert add` — crea nuova regola con validazione trigger_config
- `/alert list` — mostra tutte le regole attive
- `/alert delete <id>` — elimina regola (soft delete)
- `/alert enable/disable` — toggle stato

**Acceptance Criteria:**
- `/alert list` mostra tutte le regole con stato (enabled/disabled)
- `/alert add` valida trigger_type e trigger_config
- `/alert delete` conferma eliminazione

---

## TASK-005: AlertLog Entity + Logging
**Assignee:** Thomas  
**Priority:** MEDIUM  
**Dependencies:** TASK-004  
**Description:**
- SQLAlchemy model per AlertLog
- Log every trigger event: triggered_at, sent_at, status
- On success: status="sent"
- On failure: status="failed", error_msg populated

**Acceptance Criteria:**
- AlertLog table exists with correct schema
- Each alert creates a log entry
- Logs queryable by rule_id, date range, status

---

## TASK-006: User Entity + Registration
**Assignee:** Thomas  
**Priority:** MEDIUM  
**Dependencies:** TASK-002  
**Description:**
- SQLAlchemy model per User
- Registration flow: user starts bot → record created with is_active=true
- Track registered_at timestamp
- Support is_admin flag for broadcast authorization

**Acceptance Criteria:**
- First `/start` creates User record
- Subsequent `/start` updates registered_at
- User can exist with is_active=false (deactivated, not deleted)

---

## TASK-007: Broadcast Command + Logic
**Assignee:** Thomas  
**Priority:** HIGH  
**Dependencies:** TASK-006  
**Description:**
- `/broadcast <message>` — admin-only
- Fetch all users with is_active=true
- Send message to each user
- Handle Telegram rate limit (429) with exponential backoff
- Queue messages that fail due to rate limit
- Log broadcast in AlertLog

**Acceptance Criteria:**
- Non-admin user gets "Unauthorized" message
- Empty user list → graceful "No active users" message
- Rate limited messages queued and retried
- All successful sends logged

**Edge Cases:**
- Rate limit (429): exponential backoff (1s, 2s, 4s, 8s, max 60s)
- User not started bot: skip, don't error
- Empty message: reject with error

---

## TASK-008: Webhook Setup for GitHub Events
**Assignee:** Thomas  
**Priority:** HIGH  
**Dependencies:** TASK-004, TASK-005  
**Description:**
- FastAPI endpoint `POST /webhook/github`
- Validate GitHub signature with GITHUB_WEBHOOK_SECRET
- Parse event type (push, pull_request, issues)
- Match event to AlertRule with trigger_type="event"
- Trigger matching AlertRule
- Return 200 on success, 401 on invalid signature

**Event Types Supported:**
- `push` — GitHub push event
- `pull_request` — PR opened/merged/closed
- `issues` — Issue assigned/created/closed

**Acceptance Criteria:**
- Valid GitHub signature passes
- Invalid signature returns 401
- Event parsed correctly
- Matching AlertRule triggered
- Non-matching events acknowledged but not acted on

---

## TASK-009: Write Unit Tests per Handler
**Assignee:** Goksu  
**Priority:** HIGH  
**Dependencies:** TASK-003  
**Description:**
- Test `/start`: user created in DB
- Test `/help`: returns command list
- Test `/status`: returns bot stats
- Test `/ping`: returns pong + latency
- Test `/alert add`: creates AlertRule
- Test `/alert list`: returns rules
- Test `/broadcast`: sends to all users
- Test unauthorized broadcast: rejected

**Tools:** pytest + pytest-mock

**Acceptance Criteria:**
- All tests pass
- 80%+ code coverage on handlers
- Tests isolated (no real DB)

---

## TASK-010: Integration Tests
**Assignee:** Goksu  
**Priority:** HIGH  
**Dependencies:** TASK-009  
**Description:**
- Test bot startup and shutdown
- Test webhook endpoint with mock GitHub payload
- Test cron trigger (manual trigger test)
- Test broadcast with multiple users
- Test rate limit handling
- Test database migration

**Acceptance Criteria:**
- All integration tests pass
- No test leaves DB in dirty state
- Webhook mock sends realistic payload

---

## TASK-011: Test CI/CD Pipeline
**Assignee:** Goksu  
**Priority:** MEDIUM  
**Dependencies:** TASK-016 (CI/CD setup)  
**Description:**
- Verify GitHub Actions workflow runs on push
- Verify tests run in CI environment
- Verify Docker image builds successfully
- Verify image pushed to registry

**Acceptance Criteria:**
- CI pipeline green on main branch
- Docker build succeeds
- No flaky tests

---

## TASK-012: QA Checklist Validation
**Assignee:** Goksu  
**Priority:** HIGH  
**Dependencies:** TASK-010  
**Description:**
Execute QA checklist from kickoff doc:
- [ ] Bot responds to `/start` without crash
- [ ] `/help` shows correct command list
- [ ] `/status` reports bot state (online/offline)
- [ ] CI fail → notification arrives within X min
- [ ] Broadcast reaches all registered users
- [ ] Handle Telegram rate limit (420 error)
- [ ] Handle bot restart during message sending

**Edge cases:**
- Bot offline during event → retry logic
- Rate limit Telegram → exponential backoff + queue
- Broadcast with empty list → handle gracefully

**Acceptance Criteria:**
- All QA checklist items pass
- Report any failures with steps to reproduce

---

## TASK-013: GitHub Repository Setup
**Assignee:** Elisa  
**Priority:** HIGH  
**Description:**
- Create GitHub repo if not exists: `niccolocoppo88/telegram-automation-bot`
- Push all files from workspace
- Setup GitHub Projects for task tracking
- Add team members with appropriate permissions

**Files to push:**
- BRIEF.md
- TASKS.md
- SPEC.md
- src/ (after TASK-001)
- tests/ (after TASK-009)
- Dockerfile, docker-compose.yml (after TASK-016)

**Acceptance Criteria:**
- Repo exists on GitHub
- All team members have access
- Files visible on GitHub

---

## TASK-014: Coordinate Implementation
**Assignee:** Elisa  
**Priority:** HIGH  
**Description:**
- Monitor progress of all agents
- Update TASKS.md with status
- Identify blockers and escalate
- Ensure 15-minute updates to Nico
- Plan standups if needed

**Acceptance Criteria:**
- Nico never surprised by status
- Blockers identified within 1 hour
- Updates delivered on schedule

---

## TASK-015: Brief Document
**Assignee:** Elisa  
**Priority:** HIGH  
**Status:** ✅ DONE  
**Description:**
- BRIEF.md created with all features detailed
- Includes user flows, API endpoints, data model
- Edge cases documented
- Acceptance criteria defined

---

## TASK-016: Dockerfile
**Assignee:** Piotr  
**Priority:** HIGH  
**Dependencies:** TASK-001  
**Description:**
- Create Dockerfile for bot
- Base image: `python:3.11-slim`
- Install dependencies from requirements.txt
- Expose ports: 8000 (FastAPI), 8080 (webhook)
- Volume for SQLite DB: `/app/data`
- Set environment variables
- Run bot with proper CMD/ENTRYPOINT

**Acceptance Criteria:**
- `docker build -t telegram-bot .` succeeds
- Container starts without errors
- Bot connects to Telegram API
- Webhook endpoint accessible

---

## TASK-017: docker-compose.yml
**Assignee:** Piotr  
**Priority:** HIGH  
**Dependencies:** TASK-016  
**Description:**
- Create docker-compose.yml with:
  - bot service
  - Optional: PostgreSQL service (default SQLite)
  - Network configuration
- Volume mounts for persistence
- Health check for bot

**Acceptance Criteria:**
- `docker-compose up` starts all services
- Bot service healthy
- Data persists across restarts

---

## TASK-018: GitHub Actions CI/CD
**Assignee:** Piotr  
**Priority:** HIGH  
**Dependencies:** TASK-017  
**Description:**
- Setup GitHub Actions workflow on push to main
- Steps:
  1. Checkout code
  2. Setup Python 3.11
  3. Install dependencies
  4. Run tests (pytest)
  5. Build Docker image
  6. Push to GitHub Container Registry (or Docker Hub)
- Trigger on: push to main, PR to main

**Acceptance Criteria:**
- CI runs on every push
- Tests must pass for deploy
- Docker image tagged with commit SHA
- Image pushed on successful merge to main

---

## Task Status Summary

| Task | Status | Assignee |
|-----|--------|----------|
| TASK-001 | ✅ DONE | Thomas |
| TASK-002 | ✅ DONE | Thomas |
| TASK-003 | ✅ DONE | Thomas |
| TASK-004 | ✅ DONE | Thomas |
| TASK-005 | ⬜ TODO | Thomas |
| TASK-006 | ✅ DONE | Thomas |
| TASK-007 | ✅ DONE | Thomas |
| TASK-008 | ✅ DONE | Thomas |
| TASK-009 | ✅ DONE | Goksu |
| TASK-010 | ✅ DONE | Goksu |
| TASK-011 | ⬜ TODO | Goksu |
| TASK-012 | ⬜ TODO | Goksu |
| TASK-013 | ⬜ TODO | Elisa |
| TASK-014 | ⬜ TODO | Elisa |
| TASK-015 | ✅ DONE | Elisa |
| TASK-016 | ✅ DONE | Piotr |
| TASK-017 | ✅ DONE | Piotr |
| TASK-018 | ✅ DONE | Elisa |

---

## Notes

1. **Order of Implementation:**
   - TASK-001 (setup) first
   - TASK-002, TASK-003 (core handlers) next
   - TASK-004 → TASK-008 in sequence
   - TASK-009 → TASK-012 after handlers complete
   - TASK-016 → TASK-018 after bot is functional

2. **Blocking Issues:**
   - Escalate immediately to Elisa if blocked
   - Do not wait to report blockers

3. **Testing Requirement:**
   - No feature is "done" until tests pass
   - QA checklist must be validated
