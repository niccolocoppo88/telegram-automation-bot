# KICKOFF DOC — Telegram Automation Bot

**📅 2026-04-22 | Status: IN PROGRESS**

---

## 1. Goal

Automazione che risponde a trigger (cron o manuali) e notifica il team su Telegram — invece di dover controllare manualmente GitHub/Linear/altri tool, il bot porta le info a voi.

---

## 2. Core Features (v1)

1. **Alert automatici** — notifica su Telegram quando succede qualcosa di rilevante (PR merge, CI fallita, issue assignato)
2. **Command handling** — risponde a comandi come `/status`, `/help`, `/ping`
3. **Notification broadcast** — invia messaggi broadcast a tutti gli utenti registrati

_v2 (se il bot funziona bene): Daily Briefing vocale come proponeva Elisa ☕_

---

## 3. Entity Relationships

```
User (Telegram User)
├── user_id (PK)
├── username
├── is_active
└── registered_at

AlertRule (trigger configurato)
├── rule_id (PK)
├── name
├── trigger_type (cron | event | manual)
├── payload (JSON config)
├── target_chat_id
└── created_by

AlertLog (storia degli alert)
├── log_id (PK)
├── rule_id (FK → AlertRule)
├── sent_at
├── status (sent | failed)
└── error_msg
```

---

## 4. User Flows

1. **Admin crea AlertRule** → Configura trigger → Assegna a chat/utente
2. **Bot risponde a comando** → `/status` mostra alert attivi, `/help` lista comandi
3. **Trigger scatta** → Bot evalua rule → Invia notifica su Telegram → Logga in AlertLog
4. **Broadcast** → Admin invia `/broadcast <msg>` → Bot inoltra a tutti gli iscritti

---

## 5. Stack

- **Bot:** Python + python-telegram-bot
- **API:** FastAPI
- **Hosting:** Docker su VPS
- **CI/CD:** GitHub Actions
- **Notification:** cron + bot message

---

## 6. Chi fa cosa

| Fase | Chi |
|------|-----|
| Lead + Coordinamento | Thomas |
| Stack + Architecture | Thomas/Goksu |
| Goal + Feature + QA checklist | Goksu |
| Entity Relationships + Scope | Elisa |
| Dockerfile + Deploy setup | Piotr |

---

## 7. Pipeline

```
Brief → Design Spec → Architecture Review → Mockup → Implementazione
```

---

## 8. Timeline

| Quando | Cosa |
|--------|------|
| Stanotte | Kickoff doc |
| Domani 09:00 | Brief su GitHub |
| Domani (Goksu) | QA checklist |
| +24h | Piotr review |
| Dopo review | Implementazione 🚀 |

---

## 9. Votazione

- Thomas → ✅ Telegram Automation Bot
- Goksu → ✅ Telegram Automation Bot
- Elisa → 🟡 Daily Briefing Vocal (minoranza, v2)
- **Majority: 2-1 — Procediamo**

---

## 10. QA Checklist

- [ ] Bot risponde a `/start` senza crash
- [ ] `/help` mostra lista comandi corretta
- [ ] `/status` riporta stato bot (online/offline)
- [ ] CI fail → notifica arriva entro X min
- [ ] Broadcast raggiunge tutti gli utenti registrati
- [ ] Handle Telegram rate limit (420 error)
- [ ] Handle bot restart durante invio messaggio

**Edge case da coprire:**
- Bot offline durante evento → retry logic
- Rate limit Telegram → exponential backoff + queue
- Broadcast con lista vuota → handle gracefully
