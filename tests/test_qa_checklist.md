# Test Strategy — Telegram Automation Bot

**Version:** 1.0  
**Date:** 2026-04-22  
**Author:** Goksu (QA Engineer)  

---

## 1. Overview

This document describes the test strategy for the Telegram Automation Bot project, covering unit tests, integration tests, and validation against the QA Checklist.

---

## 2. Test Pyramid

```
         ┌───────────────┐
         │  Integration  │  ← IT-* tests (workflows, webhooks, broadcast)
         │     Tests     │
         ├───────────────┤
         │    Unit       │  ← UT-* tests (handlers, models, alert engine)
         │    Tests      │
         ├───────────────┤
         │   Static      │  ← Code quality, linting
         └───────────────┘
```

- **Unit Tests (UT):** Fast, isolated, test single modules
- **Integration Tests (IT):** Test full workflows, real DB, mock external services
- **Target Coverage:** 80%+ on core modules (handlers, alert_engine, models, api)

---

## 3. Happy Path Tests

### 3.1 Bot Commands

| Test ID | Scenario | Steps | Expected |
|---------|----------|-------|----------|
| HP-001 | User runs `/start` | Send `/start` to bot | New user in DB, welcome message |
| HP-002 | Admin runs `/broadcast` | Admin sends `/broadcast Hello` | All active users receive "Hello" |
| HP-003 | GitHub push webhook | POST to `/webhook/github` with valid signature | Alert triggered if rule matches |
| HP-004 | Alert manual trigger | POST to `/webhook/alert` with valid ID | Alert sent, log updated |

### 3.2 Data Flow

```
User sends /start
    → handlers.py:start_handler()
    → database.py:create_or_update_user()
    → User record created/updated
    → bot.send_message() with welcome
    → AlertLog not needed for /start (registration only)

Admin sends /broadcast "Hello"
    → handlers.py:broadcast_handler()
    → database.py:get_active_users()
    → For each user: bot.send_message()
    → Handle any 429 with backoff
    → AlertLog entries created for each send
```

---

## 4. Error Handling Tests

### 4.1 Telegram API Errors

| Test ID | Scenario | How to Simulate | Expected |
|---------|----------|-----------------|----------|
| EH-001 | 429 Rate Limit | Mock `send_message` to return 429 | Exponential backoff, message queued |
| EH-002 | 403 Forbidden | Mock `send_message` to return 403 | Log error, continue to next user |
| EH-003 | 500 Telegram Server Error | Mock `send_message` to return 500 | Retry up to 3 times, then log failure |
| EH-004 | Network timeout | Mock `send_message` to timeout | Retry with backoff |

### 4.2 Webhook Errors

| Test ID | Scenario | How to Simulate | Expected |
|---------|----------|-----------------|----------|
| EH-005 | Invalid HMAC signature | Send webhook with wrong `X-Hub-Signature-256` | 401 Unauthorized returned |
| EH-006 | Malformed JSON | POST invalid JSON to webhook | 400 Bad Request returned |
| EH-007 | Missing required fields | POST payload missing `alert_id` | 400 Bad Request returned |

### 4.3 Database Errors

| Test ID | Scenario | How to Simulate | Expected |
|---------|----------|-----------------|----------|
| EH-008 | DB connection failure | Mock DB to raise `OperationalError` | Error logged, user sees friendly message |
| EH-009 | Constraint violation | Create user with duplicate username | Error caught, handled gracefully |
| EH-010 | Transaction rollback | Mock DB to fail mid-transaction | No partial data committed |

---

## 5. Concurrency Tests (Multiple Alerts)

### 5.1 Concurrent Alert Handling

| Test ID | Scenario | Steps | Expected |
|---------|----------|-------|----------|
| CT-001 | Two alerts same event | Send webhook that matches 2 rules | Both alerts sent, both logged |
| CT-002 | Broadcast + alert concurrent | Broadcast running + new alert triggered | Both complete, no data corruption |
| CT-003 | Rapid webhook bursts | Send 10 webhooks rapidly | All processed, no dropped alerts |

### 5.2 Database Concurrency

| Test ID | Scenario | Steps | Expected |
|---------|----------|-------|----------|
| CT-004 | Concurrent user registrations | 5 users send `/start` simultaneously | All 5 created, no duplicates |
| CT-005 | Concurrent alert log writes | Multiple alerts writing logs | All written, no lost data |

**Implementation Note:** Use `threading` or `asyncio` to simulate concurrency. For SQLite, ensure proper transaction handling.

---

## 6. Database Migration Tests

### 6.1 Schema Migrations

| Test ID | Scenario | Steps | Expected |
|---------|----------|-------|----------|
| DM-001 | Fresh database init | Delete test DB, run migrations | All tables created with correct schema |
| DM-002 | No migration needed | DB already at latest version | No changes, startup succeeds |
| DM-003 | Future column addition | Add new column (e.g., `priority`) | Data preserved, new column has default |

### 6.2 Migration Validation

```sql
-- Verify tables exist
SELECT name FROM sqlite_master WHERE type='table';

-- Verify expected columns
PRAGMA table_info(users);
PRAGMA table_info(alert_rules);
PRAGMA table_info(alert_logs);
```

### 6.3 Data Preservation

| Test ID | Scenario | Steps | Expected |
|---------|----------|-------|----------|
| DM-004 | Migrate DB with existing data | Add column, run migration | Existing data intact, new col has default |
| DM-005 | Rollback simulation | Revert migration | Data restored to pre-migration state |

---

## 7. Test Fixtures (conftest.py)

### 7.1 Fixtures Required

```python
@pytest.fixture
def mock_telegram_bot():
    """Mock telegram.Bot with controlled responses"""
    ...

@pytest.fixture
def test_db():
    """Fresh test database, cleaned after each test"""
    ...

@pytest.fixture
def sample_user():
    """Sample user for testing"""
    ...

@pytest.fixture
def sample_alert_rule():
    """Sample alert rule for testing"""
    ...

@pytest.fixture
def mock_github_webhook():
    """Mock GitHub webhook payload"""
    ...

@pytest.fixture
def mock_rate_limit():
    """Simulate Telegram 429 response"""
    ...
```

### 7.2 Mock Strategy

- **Telegram Bot:** Mock `send_message`, `edit_message_text` with controlled responses
- **GitHub Webhooks:** Use `requests_mock` for HTTP mock
- **Database:** Use in-memory SQLite (`sqlite:///:memory:`) with `aiosqlite`
- **Time:** Use `freezegun` or `time-machine` for latency/timeout tests

---

## 8. CI Integration

### 8.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml (conceptual)
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt pytest pytest-cov pytest-mock
      - name: Run unit tests
        run: pytest tests/ -v --cov=src --cov-report=term-missing
      - name: Run integration tests
        run: pytest tests/ -v -k integration
```

### 8.2 Quality Gates

| Gate | Threshold | Action on Failure |
|------|-----------|-------------------|
| Test pass rate | 100% | Block merge |
| Code coverage | ≥80% on core modules | Block merge |
| Linting | No errors (flake8/black) | Warning, block merge |

---

## 9. Test Execution Schedule

| Phase | When | Tests Run |
|-------|------|-----------|
| Pre-commit | Before each commit | Unit tests only |
| PR check | On pull request | Unit + Integration |
| Main branch | On merge to main | Full suite + Docker build |
| Manual QA | Before release | QA checklist validation (TASK-012) |

---

## 10. Known Limitations

1. **Telegram API mocking:** Full bot behavior hard to mock; focus on handler logic
2. **Webhook replay:** Cannot replay real GitHub webhooks; use realistic mocks
3. **SQLite concurrency:** SQLite has limited concurrent write support; tests use sequential writes
4. **Time-based tests:** Latency tests may be flaky on CI; allow ±50ms tolerance

---

## 11. References

- SPEC.md — Architecture, API, database schema
- TASKS.md — Task definitions and acceptance criteria
- QA_CHECKLIST.md — Complete test case inventory

---

**Document Version:** 1.0  
**Created:** 2026-04-22  
**Last Updated:** 2026-04-22  
**Author:** Goksu (QA Engineer)
