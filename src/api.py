"""FastAPI webhooks and API endpoints."""

import hashlib
import hmac
import logging
import time

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import session_context
from .models import AlertLog

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Automation Bot API")

# Track start time for uptime calculation
start_time = time.time()


# ─── Health & Stats Endpoints ───────────────────────────────────────────────


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    import psutil
    import httpx

    # Memory usage
    memory_mb = psutil.Process().memory_info().rss / 1024 / 1024

    # DB connectivity check
    db_ok = True
    try:
        async with session_context() as session:
            await session.execute("SELECT 1")
    except Exception:
        db_ok = False

    # Telegram API latency
    from .config import get_settings
    settings = get_settings()
    latency_ms = None
    if settings.telegram_bot_token:
        try:
            async with httpx.AsyncClient() as client:
                start = time.time()
                await client.get(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/getMe",
                    timeout=5.0,
                )
                latency_ms = int((time.time() - start) * 1000)
        except Exception:
            latency_ms = None

    # Determine status
    status = "healthy" if db_ok else "degraded"
    if latency_ms and latency_ms > 500:
        status = "degraded"

    return JSONResponse(
        status_code=200 if status == "healthy" else 503,
        content={
            "status": status,
            "uptime_seconds": int(time.time() - start_time),
            "memory_mb": round(memory_mb, 1),
            "db_ok": db_ok,
            "latency_ms": latency_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    )


@app.get("/stats")
async def get_stats() -> JSONResponse:
    """Get bot statistics."""
    async with session_context() as session:
        # User stats
        result = await session.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active FROM users"
        )
        row = result.fetchone()
        total_users = row[0] if row else 0
        active_users = row[1] if row[1] else 0

        # Alert rule stats
        result = await session.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN is_enabled = 1 THEN 1 ELSE 0 END) as enabled FROM alert_rules"
        )
        row = result.fetchone()
        total_rules = row[0] if row else 0
        enabled_rules = row[1] if row[1] else 0

        # Alert log stats
        result = await session.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent, "
            "SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed, "
            "MAX(sent_at) as last_alert_at FROM alert_logs"
        )
        row = result.fetchone()
        total_alerts = row[0] if row[0] else 0
        alerts_sent = row[1] if row[1] else 0
        alerts_failed = row[2] if row[2] else 0
        last_alert_at = row[3] if row[3] else None

    # Calculate error rate and delivery success
    error_rate = round((alerts_failed / total_alerts * 100), 2) if total_alerts > 0 else 0.0
    delivery_success_rate = round((alerts_sent / total_alerts * 100), 2) if total_alerts > 0 else 0.0

    return JSONResponse(
        content={
            "total_users": total_users,
            "active_users": active_users,
            "total_alert_rules": total_rules,
            "enabled_rules": enabled_rules,
            "total_alerts_sent": alerts_sent,
            "alerts_failed": alerts_failed,
            "error_rate": error_rate,
            "delivery_success_rate": delivery_success_rate,
            "last_alert_at": last_alert_at.isoformat() if last_alert_at else None,
        }
    )


# ─── Webhook Endpoints ──────────────────────────────────────────────────────


@app.post("/webhook/github")
async def github_webhook(request: Request) -> JSONResponse:
    """Handle GitHub webhook events."""
    settings = get_settings()
    secret = settings.github_webhook_secret or ""

    # Validate signature
    if secret:
        signature = request.headers.get("x-hub-signature-256", "")
        body = await request.body()

        expected = (
            "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        )

        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event type
    event = request.headers.get("x-github-event", "")
    body = await request.json()

    logger.info(f"GitHub webhook: {event}")

    # Find matching event-based alert rules
    async with session_context() as session:
        result = await session.execute(
            "SELECT * FROM alert_rules WHERE trigger_type = 'event' AND is_enabled = 1"
        )
        rows = result.fetchall()
        columns = result.keys()
        rules = [dict(zip(columns, row)) for row in rows]

    # Process each matching rule
    import httpx

    for rule in rules:
        # Simple matching - check if event matches trigger_config
        config = rule.get("trigger_config", {})
        if config.get("event") != event:
            continue

        # Render message template
        template = rule.get("message_template", "Alert: {event}")
        try:
            message = template.format(
                event=event,
                repo=body.get("repository", {}).get("full_name", "unknown"),
                action=body.get("action", ""),
            )
        except Exception:
            message = f"Alert triggered: {event}"

        # Send Telegram message
        bot_token = settings.telegram_bot_token
        target_chat_id = rule.get("target_chat_id")
        if bot_token and target_chat_id:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": target_chat_id, "text": message},
                        timeout=10.0,
                    )
                    if resp.status_code == 200:
                        log_status = "sent"
                    else:
                        log_status = "failed"
                        logger.error(
                            f"Telegram API error: {resp.status_code} - {resp.text}"
                        )
            except Exception as e:
                log_status = "failed"
                logger.error(f"Failed to send Telegram message: {e}")
        else:
            log_status = "pending"  # No bot token configured

        # Create alert log
        async with session_context() as session:
            log = AlertLog(
                rule_id=rule["rule_id"],
                status=log_status,
                payload={"event": event, "body": body},
            )
            if log_status == "sent":
                from datetime import datetime

                log.sent_at = datetime.utcnow()
            session.add(log)
            await session.commit()

        logger.info(f"Triggered alert rule: {rule['name']} -> {log_status}")

    return JSONResponse(content={"status": "ok", "event": event})


@app.post("/webhook/alert")
async def alert_webhook(request: Request) -> JSONResponse:
    """Manual alert trigger endpoint."""
    body = await request.json()

    alert_id = body.get("alert_id")
    if not alert_id:
        raise HTTPException(status_code=400, detail="alert_id required")

    payload = body.get("payload", {})
    message = payload.get("message", "Alert triggered")

    async with session_context() as session:
        # Find the alert rule
        result = await session.execute(
            "SELECT * FROM alert_rules WHERE rule_id = :rule_id AND is_enabled = 1",
            {"rule_id": alert_id},
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Alert rule not found")

        columns = result.keys()
        rule = dict(zip(columns, row))

        # Create alert log
        log = AlertLog(
            rule_id=rule["rule_id"],
            status="pending",
            payload=payload,
        )
        session.add(log)
        await session.commit()

    logger.info(f"Manual alert triggered: rule_id={alert_id}")

    return JSONResponse(
        content={
            "status": "triggered",
            "rule_id": alert_id,
            "message": message,
        }
    )


# ─── Root ────────────────────────────────────────────────────────────────────


@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint."""
    return JSONResponse(content={"message": "Telegram Automation Bot API"})
