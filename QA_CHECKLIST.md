# QA Checklist — Telegram Automation Bot

**Version:** 1.0  
**Date:** 2026-04-22  
**Status:** Ready for Review  
**Assignee:** Goksu  

---

## 1. Unit Test Cases

### 1.1 Command Handlers (`src/handlers.py`)

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| UT-001 | `/start` creates new user | User sends `/start` | User record created in DB, welcome message returned | HIGH |
| UT-002 | `/start` updates existing user | User sends `/start` again | `registered_at` updated, no duplicate | HIGH |
| UT-003 | `/start` handles DB error | DB connection fails | Graceful error message, no crash | HIGH |
| UT-004 | `/help` returns command list | User sends `/help` | Formatted list of all commands with descriptions | HIGH |
| UT-005 | `/help` includes admin commands | Admin user sends `/help` | All commands including admin-only shown | MEDIUM |
| UT-006 | `/status` returns bot stats | User sends `/status` | JSON with uptime, active users, rules, alerts | HIGH |
| UT-007 | `/status` handles empty DB | No users in DB | Stats show 0 values, no crash | MEDIUM |
| UT-008 | `/ping` returns pong + latency | User sends `/ping` | "pong" + latency in ms | HIGH |
| UT-009 | `/ping` latency calculation | Repeated calls | Latency increases/decreases based on actual response time | MEDIUM |
| UT-010 | Unknown command handler | User sends `/unknown` | "Command not found" message | LOW |

### 1.2 Alert Rule Management

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| UT-011 | `/alert add` creates rule (cron) | Admin sends `/alert add` with cron config | AlertRule created, confirmation shown | HIGH |
| UT-012 | `/alert add` creates rule (event) | Admin sends `/alert add` with event config | AlertRule created with `trigger_type='event'` | HIGH |
| UT-013 | `/alert add` validates trigger_config | Invalid JSON config | Error message, rule NOT created | HIGH |
| UT-014 | `/alert add` validates trigger_type | Invalid type | Error message, rule NOT created | HIGH |
| UT-015 | `/alert list` returns all rules | Admin sends `/alert list` | List of rules with enabled/disabled status | HIGH |
| UT-016 | `/alert list` handles empty list | No rules created | "No alert rules found" message | MEDIUM |
| UT-017 | `/alert delete` removes rule | Admin sends `/alert delete <id>` | Rule soft-deleted, confirmation shown | HIGH |
| UT-018 | `/alert delete` handles invalid ID | Non-existent rule ID | Error message, no crash | MEDIUM |
| UT-019 | `/alert enable` activates rule | Admin sends `/alert enable <id>` | Rule `is_enabled=True`, confirmation | HIGH |
| UT-020 | `/alert disable` deactivates rule | Admin sends `/alert disable <id>` | Rule `is_enabled=False`, confirmation | HIGH |
| UT-021 | `/alert enable` handles invalid ID | Non-existent rule ID | Error message, no crash | MEDIUM |
| UT-022 | Non-admin restricted commands | Non-admin sends `/alert add` | "Unauthorized" message returned | HIGH |

### 1.3 Broadcast

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| UT-023 | `/broadcast` sends to all users | Admin sends `/broadcast Hello` | Message sent to all `is_active=True` users | HIGH |
| UT-024 | `/broadcast` with empty user list | Admin sends `/broadcast` when no users | "No active users" message, no crash | HIGH |
| UT-025 | `/broadcast` unauthorized | Non-admin sends `/broadcast` | "Unauthorized" message returned | HIGH |
| UT-026 | `/broadcast` empty message | Admin sends `/broadcast ` (empty) | Error message, message NOT sent | MEDIUM |
| UT-027 | `/broadcast` rate limited (mock) | Simulate 429 response | Message queued with retry | HIGH |
| UT-028 | `/broadcast` logs each send | Admin sends `/broadcast test` | AlertLog entries created for each user | MEDIUM |

### 1.4 Alert Engine

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| UT-029 | Alert triggered for matching rule | GitHub webhook matches event rule | Alert sent to `target_chat_id`, log entry created | HIGH |
| UT-030 | Alert not triggered for non-matching | GitHub webhook does not match | No alert sent, webhook returns 200 | HIGH |
| UT-031 | Alert log on success | Alert sent successfully | Log with `status='sent'`, `sent_at` populated | HIGH |
| UT-032 | Alert log on failure | Alert send fails | Log with `status='failed'`, `error_msg` populated | HIGH |
| UT-033 | Cron trigger evaluation | Cron schedule matches | All enabled cron rules evaluated | HIGH |
| UT-034 | Multiple alerts concurrent | Multiple events at same time | All handled, no data corruption | HIGH |

### 1.5 Database Models

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| UT-035 | User model creation | Valid user data | User record persisted | HIGH |
| UT-036 | User uniqueness constraint | Duplicate username | DB constraint violation / error | HIGH |
| UT-037 | AlertRule model creation | Valid rule data | AlertRule record persisted | HIGH |
| UT-038 | AlertRule FK constraint | Invalid `created_by` | FK violation / error | MEDIUM |
| UT-039 | AlertLog model creation | Valid log data | AlertLog record persisted | HIGH |
| UT-040 | AlertLog FK constraint | Invalid `rule_id` | FK violation / error | MEDIUM |
| UT-041 | `is_active` flag behavior | User with `is_active=False` | Excluded from broadcasts | HIGH |

### 1.6 API Endpoints

| Test ID | Test Case | Input | Expected Output | Priority |
|---------|-----------|-------|-----------------|----------|
| UT-042 | `POST /webhook/github` valid signature | Valid HMAC signature | 200 OK, alert triggered if matching | HIGH |
| UT-043 | `POST /webhook/github` invalid signature | Invalid HMAC | 401 Unauthorized | HIGH |
| UT-044 | `POST /webhook/github` push event | Push webhook payload | Alert triggered for matching event rules | HIGH |
| UT-045 | `POST /webhook/github` pull_request event | PR webhook payload | Alert triggered for matching rules | HIGH |
| UT-046 | `POST /webhook/github` issues event | Issues webhook payload | Alert triggered for matching rules | HIGH |
| UT-047 | `POST /webhook/github` malformed JSON | Invalid JSON body | 400 Bad Request | MEDIUM |
| UT-048 | `POST /webhook/alert` valid payload | Valid `{"alert_id": 123, "payload": {...}}` | 200 OK, alert triggered | HIGH |
| UT-049 | `POST /webhook/alert` invalid alert_id | Non-existent rule ID | 404 Not Found | HIGH |
| UT-050 | `POST /webhook/alert` malformed JSON | Invalid JSON body | 400 Bad Request | MEDIUM |
| UT-051 | `GET /health` returns status | Request to `/health` | `{"status": "healthy", ...}` JSON | HIGH |
| UT-052 | `GET /stats` returns statistics | Request to `/stats` | JSON with user/rule/alert counts | HIGH |

---

## 2. Integration Test Cases

### 2.1 Bot Lifecycle

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-001 | Bot startup | Run `python src/bot.py` | Bot connects to Telegram, no errors | HIGH |
| IT-002 | Bot shutdown | Send SIGTERM | Graceful shutdown, connections closed | MEDIUM |
| IT-003 | Bot restart | Restart while sending broadcast | Resume from interrupted state | HIGH |

### 2.2 GitHub Webhook Flow

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-004 | Push event → Alert | Send mock push webhook | Alert sent, log entry created | HIGH |
| IT-005 | PR event → Alert | Send mock PR webhook | Alert sent, correct message format | HIGH |
| IT-006 | Issue event → Alert | Send mock issue webhook | Alert sent, correct message format | HIGH |
| IT-007 | No matching rule | Send event with no matching rule | 200 OK, no alert sent | HIGH |
| IT-008 | Invalid signature | Send webhook with wrong secret | 401 returned, no alert | HIGH |

### 2.3 Broadcast Workflow

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-009 | Broadcast to 3 users | Create 3 users, send broadcast | All 3 receive message | HIGH |
| IT-010 | Broadcast with inactive users | 2 active + 1 inactive user | Only active users receive | HIGH |
| IT-011 | Rate limit handling | Broadcast to many users | Messages queued, no 429 crash | HIGH |
| IT-012 | Broadcast interruption | Kill bot mid-broadcast | Resume correctly on restart | HIGH |

### 2.4 Alert Engine

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-013 | Cron alert fires | Trigger cron rule manually | Alert sent at scheduled time | HIGH |
| IT-014 | Multiple alerts same event | Event triggers 2 rules | Both alerts sent, 2 logs | HIGH |
| IT-015 | Alert retry on failure | Simulate Telegram error | Retry with backoff, eventual success | HIGH |

### 2.5 Database Migration

| Test ID | Test Case | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| IT-016 | Fresh DB init | Delete DB, start bot | All tables created correctly | HIGH |
| IT-017 | DB upgrade | Add new column (future) | Migration runs without data loss | MEDIUM |
| IT-018 | Concurrent DB writes | Multiple alerts at once | No race conditions, data consistent | HIGH |

---

## 3. Edge Cases

### 3.1 Rate Limiting (Telegram 429)

| Edge Case | Expected Behavior | Priority |
|-----------|-------------------|----------|
| EC-001: First 429 received | Exponential backoff starts (1s) | HIGH |
| EC-002: Second consecutive 429 | Backoff doubles (2s) | HIGH |
| EC-003: Multiple 429 in a row | Max backoff of 60s | HIGH |
| EC-004: 429 during broadcast | Remaining messages queued | HIGH |
| EC-005: 429 during alert | Retry after backoff, alert logged | HIGH |
| EC-006: Recovery after 429 | Normal operation resumes | HIGH |

### 3.2 Bot Offline / Restart

| Edge Case | Expected Behavior | Priority |
|-----------|-------------------|----------|
| EC-007: Event occurs while offline | Event ignored (webhook not received) | HIGH |
| EC-008: Restart mid-broadcast | Resume from last successful user | HIGH |
| EC-009: Restart during alert sending | Retry alert on startup | MEDIUM |
| EC-010: DB corruption on restart | Error logged, bot fails graceful | HIGH |

### 3.3 Broadcast Edge Cases

| Edge Case | Expected Behavior | Priority |
|-----------|-------------------|----------|
| EC-011: Empty user list | "No active users" message, no error | HIGH |
| EC-012: User unsubscribed mid-broadcast | Skip user, continue to next | MEDIUM |
| EC-013: Very long broadcast message | Telegram 4096 char limit enforced | HIGH |
| EC-014: Unicode/special characters in message | Correctly encoded and sent | MEDIUM |
| EC-015: Duplicate `/broadcast` sent quickly | Idempotent or rate limit applied | MEDIUM |

### 3.4 Webhook Edge Cases

| Edge Case | Expected Behavior | Priority |
|-----------|-------------------|----------|
| EC-016: Duplicate webhook received | Processed once (idempotent) | MEDIUM |
| EC-017: Webhook during rate limit | Queued until quota resets | MEDIUM |
| EC-018: Malformed JSON in webhook | 400 returned, logged | HIGH |

### 3.5 Data Integrity

| Edge Case | Expected Behavior | Priority |
|-----------|-------------------|----------|
| EC-019: User deleted from DB mid-alert | Alert fails gracefully, logged | MEDIUM |
| EC-020: AlertRule deleted while triggered | Alert fails, logged with error | MEDIUM |
| EC-021: DB transaction rollback | No partial data written | HIGH |

---

## 4. Acceptance Criteria (from SPEC.md)

### 4.1 Commands

| Feature | Acceptance Criteria | Test Coverage |
|---------|---------------------|---------------|
| `/start` | Bot responds without crash; user registered in DB | UT-001, UT-002, UT-003 |
| `/help` | Shows command list (all commands for admin, public for others) | UT-004, UT-005 |
| `/status` | Shows bot status (online/offline), uptime, active users, rules | UT-006, UT-007 |
| `/ping` | Returns "pong" + latency in ms | UT-008, UT-009 |
| `/broadcast` | Admin-only; sends to all active users; handles rate limits | UT-023, UT-024, UT-025, IT-009, IT-010, IT-011 |
| `/alert` | CRUD operations for alert rules; admin-only | UT-011-UT-022 |

### 4.2 Webhooks

| Feature | Acceptance Criteria | Test Coverage |
|---------|---------------------|---------------|
| POST /webhook/github | Validates signature; triggers matching rules; returns 200/401 | UT-042, UT-043, UT-044, UT-045, UT-046 |
| POST /webhook/alert | Triggers alert by ID; returns 200/404/400 | UT-048, UT-049, UT-050 |
| GET /health | Returns health status with uptime | UT-051 |
| GET /stats | Returns user/rule/alert statistics | UT-052 |

### 4.3 Alert System

| Feature | Acceptance Criteria | Test Coverage |
|---------|---------------------|---------------|
| Alert trigger | Matching rules triggered on events | IT-004, IT-005, IT-006 |
| Alert logging | Every alert attempt logged (sent/failed) | UT-031, UT-032 |
| Retry logic | Failed alerts retried with exponential backoff | EC-001, EC-002, EC-003, IT-015 |
| Cron alerts | Alerts fire on schedule | IT-013 |

### 4.4 Error Handling

| Scenario | Acceptance Criteria | Test Coverage |
|----------|---------------------|---------------|
| Telegram rate limit (429) | Exponential backoff (1s, 2s, 4s... max 60s); queue messages | EC-001, EC-002, EC-003, EC-004, IT-011 |
| Bot restart during send | Resume from interrupted point | IT-003, EC-008, EC-009 |
| Empty broadcast list | Graceful "No active users" message | UT-024, EC-011 |
| DB unavailable | Retry 3x, then alert admin, return 503 | UT-003 |

---

## 5. Test Execution Checklist

### Pre-Run
- [ ] All environment variables set in `.env.test`
- [ ] Test database initialized (fresh SQLite)
- [ ] Mock Telegram bot token configured
- [ ] Mock GitHub webhook secret configured

### Unit Tests (UT)
- [ ] Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
- [ ] Target: ≥80% code coverage on `src/handlers.py`, `src/alert_engine.py`
- [ ] All UT-* tests pass

### Integration Tests (IT)
- [ ] Bot starts successfully
- [ ] Webhook endpoints respond correctly
- [ ] Broadcast reaches all test users
- [ ] Rate limit handling verified
- [ ] All IT-* tests pass

### Edge Case Tests (EC)
- [ ] Rate limit 429 simulated
- [ ] Bot restart simulated
- [ ] Empty user list tested
- [ ] All EC-* scenarios handled

### Final Validation
- [ ] QA checklist validated (TASK-012)
- [ ] All items pass or documented as known issues
- [ ] Report sent to Discord channel

---

**Document Version:** 1.0  
**Created:** 2026-04-22  
**Last Updated:** 2026-04-22  
**Author:** Goksu (QA Engineer)