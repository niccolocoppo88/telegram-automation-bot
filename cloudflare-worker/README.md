# Cloudflare Worker — GitHub Webhook → Telegram

Il worker riceve eventi da GitHub e li inoltra al bot Telegram.

## Setup

### 1. Crea account Cloudflare
- Vai su https://dash.cloudflare.com
- Crea account gratis

### 2. Installa Wrangler CLI
```bash
npm install -g wrangler
wrangler login
```

### 3. Configura secrets
```bash
cd cloudflare-worker
wrangler secret put TELEGRAM_BOT_TOKEN
# Inserisci: 8795721421:AAHWgss5Q5eWiF9BAiOfegDdGZjMZHKOoUo

wrangler secret put TELEGRAM_CHAT_ID
# Inserisci: 623447167905824769
```

### 4. Deploy
```bash
wrangler deploy
```

Ti dará un URL come:
```
https://telegram-github-webhook.<username>.workers.dev
```

### 5. Configura GitHub webhook
- Nel repo GitHub → Settings → Webhooks → Add webhook
- Payload URL: `https://telegram-github-webhook.<username>.workers.dev`
- Content type: `application/json`
- Events: seleziona quelli che vuoi (push, pull requests, workflow runs)

## Variabili d'ambiente

| Variable | Descrizione |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Token del bot Telegram |
| `TELEGRAM_CHAT_ID` | Tuo Chat ID Telegram |
| `WEBHOOK_SECRET` | Secret per verificare webhook (opzionale) |

## Eventi supportati

- **Push** — notifica su push a branch
- **Pull Request** — notifica su PR aperto/chiuso/merge
- **Workflow Run** — notifica su CI/CD completato
- **Issue** — notifica su issue creata/chiusa

## Test locale

```bash
wrangler dev
# Invia una richiesta test:
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"ref":"refs/heads/main","commits":[{"author":{"name":"Test"}}],"repository":{"full_name":"test/repo"}}'
```
