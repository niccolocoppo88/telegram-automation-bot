# KICKOFF — Telegram Automation Bot
📅 2026-04-22 | Status: APPROVED

---

## 1. Goal

Automazione che risponde a trigger (cron o manuali) e notifica il team su Telegram — invece di dover controllare manualmente GitHub/Linear/altri tool, il bot porta le info a voi.

---

## 2. Core Features (v1)

1. **Alert automatici** — notifica su Telegram quando succede qualcosa di rilevante (PR merge, CI fallita, issue assignato)
2. **Command handling** — risponde a comandi come `/status`, `/help`, `/ping`
3. **Notification broadcast** — invia messaggi broadcast a tutti gli utenti registrati

*v2: Daily Briefing vocale ☕*

---

## 3. Scope

| In scope | Out of scope |
|----------|--------------|
| Basic command handling | Natural language queries |
| Manual broadcast | Scheduled digest |
| Alert via webhook/trigger | |

---

## 4. Entity Relationships

```
User (Telegram User)
├── user_id (PK)
├── username
├── is_active
└── registered_at

AlertRule (trigger configurato)
├── rule_id (PK)
├── event_type
├── payload
└── created_at

NotificationLog (storia notifiche)
├── log_id (PK)
├── user_id (FK)
├── message
└── sent_at
```

---

## 5. Stack Tecnico

- **Bot:** Python + `python-telegram-bot`
- **API Layer:** FastAPI
- **Hosting:** Docker su VPS
- **CI/CD:** GitHub Actions
- **Notification:** cron + bot message

---

## 6. Chi fa cosa

| Fase | Chi |
|------|-----|
| Kickoff doc | Thomas |
| Goal + Feature + QA checklist | Goksu |
| Brief + Entity relationships | Elisa |
| Dockerfile + Deploy | Piotr (24h from wake) |
| Lead / Coordinamento | Thomas |

---

## 7. QA Perspective + Feature Validation

**F1 — Alert automatici**
- Test: simulare evento (push, CI fail), verificare msg su Telegram
- Edge: bot offline, retry logic, rate limit

**F2 — Command handling**
- Test: inviare `/status`, `/help`, `/ping`, verificare risposta
- Edge: comando sconosciuto, utente non autorizzato, command injection

**F3 — Notification broadcast**
- Test: broadcast a utenti registrati, verificare consegna
- Edge: utente non registrato, broadcast fallito

| Risk | Mitigation |
|-------|------------|
| Telegram rate limit | exponential backoff + queue |
| Bot crash in production | Docker healthcheck + restart policy |
| Staggered deploy | blue-green o rolling update |

---

## 8. Pipeline

```
Brief → Design Spec → Architecture Review → Mockup → Implementazione
```
- Tutto su **GitHub** (no Linear)
- Piotr ha **24h** per review

---

## 9. Votazione

- Thomas → ✅ Telegram Automation Bot
- Goksu → ✅ Telegram Automation Bot
- Elisa → 🟡 Daily Briefing Vocal (minoranza, v2)
- **2-1 — Procediamo**

---

## 10. Timeline

| Quando | Cosa |
|--------|------|
| Stanotte (Thomas) | Kickoff doc su GitHub |
| Domani 09:00 (Elisa) | Brief su GitHub |
| Domani (Goksu) | QA checklist |
| +24h (Piotr) | Dockerfile + Deploy review |
| Dopo review | Implementazione 🚀 |
