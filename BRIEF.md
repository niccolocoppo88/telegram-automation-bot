# Telegram Automation Bot — BRIEF

**Version:** 1.0  
**Date:** 2026-04-22  
**Status:** DRAFT — Per review e implementazione

---

## 1. Goal & Vision

Automazione che risponde a trigger (cron o manuali) e notifica il team su Telegram — invece di dover controllare manualmente GitHub/Linear/altri tool, il bot porta le info a voi.

**Visione:** Un hub di automazione che tiene il team sincronizzato senza aprire 10 tool diversi.

---

## 2. Core Features (v1)

### 2.1 Alert Automatici
Notifica su Telegram quando succede qualcosa di rilevante.

**Trigger supportati:**
- `cron` — schedule-based (es. ogni giorno alle 9)
- `event` — webhook-based (es. GitHub PR merged, CI failed)
- `manual` — trigger diretto via comando

**Alert types:**
- `github_pr` — PR opened/merged/closed
- `github_ci` — build success/failure
- `github_issue` — issue assigned/created/closed
- `scheduled` — reminder temporizzato

### 2.2 Command Handling
Risponde a comandi Telegram.

| Comando | Descrizione |
|---------|-------------|
| `/start` | Registra l'utente, mostra messaggio di benvenuto |
| `/help` | Lista tutti i comandi disponibili |
| `/status` | Mostra stato bot (online/offline) + statistiche |
| `/ping` | Risponde "pong" + latenza |
| `/broadcast <msg>` | Invia messaggio a tutti gli utenti registrati (admin only) |
| `/alert add <name> <trigger>` | Crea un nuovo AlertRule |
| `/alert list` | Lista tutti gli AlertRule attivi |
| `/alert delete <id>` | Elimina un AlertRule |
| `/alert enable <id>` | Abilita un AlertRule |
| `/alert disable <id>` | Disabilita un AlertRule |

### 2.3 Notification Broadcast
Admin può inviare messaggi broadcast a tutti gli utenti registrati.

**Requisiti:**
- Solo admin può fare broadcast
- Lista utenti vuota → messaggio di errore graceful
- Rate limit Telegram (420 error) → exponential backoff + queue

---

## 3. User Flows

### 3.1 Registrazione Utente
```
User → /start → Bot risponde welcome message → User aggiunto a DB (is_active=true)
```

### 3.2 Creazione AlertRule (Admin)
```
Admin → /alert add <name> <trigger_type> <config> 
→ Bot valida config → AlertRule creato in DB → Confirm message
```

### 3.3 Trigger Scatta
```
External Event (GitHub webhook / Cron job) → Bot API riceve trigger
→ Evalua AlertRule matching → Prepara notifica → Invia a Telegram
→ Log in AlertLog (sent_at, status) → Errore? Logga error_msg
```

### 3.4 Broadcast
```
Admin → /broadcast <msg> → Bot fetch lista utenti attivi
→ Per ogni utente: invia messaggio → Handle rate limit con backoff
→ Log broadcast in AlertLog
```

### 3.5 Rate Limit Handling
```
Telegram API returns 429 → Exponential backoff (1s, 2s, 4s, 8s, max 60s)
→ Queue remaining messages → Retry con backoff → Confirm sent
```

### 3.6 Bot Restart Handling
```
Bot restart → Load AlertRules from DB → Resume cron jobs
→ Check pending messages in queue → Resume sending
→ Handle gracefully se nessun pending
```

---

## 4. API Endpoints (FastAPI)

### 4.1 Webhook Endpoints
```
POST /webhook/github
  - Receives GitHub webhook events
  - Validates signature
  - Triggers matching AlertRule
  - Returns 200 on success

POST /webhook/alert
  - Manual alert trigger
  - Body: { "alert_id": "...", "payload": {...} }
  - Returns 200 on success
```

### 4.2 Internal API
```
GET /health
  - Returns bot status

GET /stats
  - Returns: total alerts, active rules, sent notifications
```

---

## 5. Data Model

### 5.1 User
| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `user_id` | INTEGER | Primary key (Telegram user ID) |
| `username` | TEXT | Telegram username |
| `is_admin` | BOOLEAN | Può fare broadcast |
| `is_active` | BOOLEAN | Account attivo |
| `registered_at` | DATETIME | Data registrazione |

### 5.2 AlertRule
| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `rule_id` | INTEGER | Primary key |
| `name` | TEXT | Nome descrittivo |
| `trigger_type` | TEXT | "cron" / "event" / "manual" |
| `trigger_config` | JSON | Configurazione trigger |
| `message_template` | TEXT | Template messaggio Telegram |
| `target_chat_id` | INTEGER | Chat Telegram destinazione |
| `is_enabled` | BOOLEAN | Rule attiva/disattiva |
| `created_by` | INTEGER | FK → User.user_id |
| `created_at` | DATETIME | Data creazione |

### 5.3 AlertLog
| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `log_id` | INTEGER | Primary key |
| `rule_id` | INTEGER | FK → AlertRule.rule_id |
| `triggered_at` | DATETIME | Quando è scattato |
| `sent_at` | DATETIME | Quando è stato inviato |
| `status` | TEXT | "pending" / "sent" / "failed" |
| `error_msg` | TEXT | Messaggio errore se failed |
| `payload` | JSON | Dati originali del trigger |

---

## 6. Configuration

### 6.1 Environment Variables
```bash
TELEGRAM_BOT_TOKEN=     # Token bot Telegram
TELEGRAM_BOT_DEBUG=false # Modalità debug
GITHUB_WEBHOOK_SECRET=   # Secret per validare webhook GitHub
DATABASE_URL=           # SQLite path o PostgreSQL URL
LOG_LEVEL=INFO          # DEBUG/INFO/WARNING/ERROR
```

### 6.2 Docker
- Image: `python:3.11-slim`
- Port exposed: 8000 (FastAPI) + 8080 (bot webhook receiver)
- Volume: `/app/data` per SQLite DB

---

## 7. Edge Cases & Error Handling

| Situazione | Handling |
|------------|----------|
| Bot offline durante evento | Retry logic con exponential backoff |
| Rate limit Telegram (429) | Exponential backoff + queue, max 60s |
| Broadcast con lista vuota | "No active users" message, no error |
| Invalid webhook signature | 401 Unauthorized, log attempt |
| AlertRule not found | "Rule not found" message, no crash |
| DB connection failed | Retry 3x, then alert admin + log error |
| Bot restart durante invio | Queue preserved, resume on restart |

---

## 8. v1 Scope vs v2 Scope

### v1 (This Implementation)
- Single bot instance
- Basic command handling
- Manual + cron triggers
- SQLite database
- GitHub webhooks (basic)

### v2 (Future)
- Daily Briefing Vocal ☕
- Multi-tenant / multi-project
- Natural language queries
- Scheduled digest emails
- Advanced analytics

---

## 9. Acceptance Criteria

1. Bot risponde a `/start`, `/help`, `/status`, `/ping` senza crash
2. `/broadcast` raggiunge tutti gli utenti registrati
3. Alert automatici arrivano entro 5 minuti dal trigger
4. Rate limit Telegram gestito senza perdita messaggi
5. Bot restart non perde AlertRule configurate
6. Tutti i test QA passano (QA checklist di Goksu)
