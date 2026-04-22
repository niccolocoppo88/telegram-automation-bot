"""FastAPI application for webhook endpoints."""

import logging
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Automation Bot - Webhook API")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
) -> JSONResponse:
    """Handle incoming GitHub webhooks."""
    body = await request.body()

    # Validate signature (placeholder — implement with secret)
    if settings.github_webhook_secret:
        expected_sig = f"sha256={compute_hmac(settings.github_webhook_secret, body)}"
        if x_hub_signature_256 != expected_sig:
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse event
    event = request.headers.get("x-github-event", "unknown")
    payload: dict[str, Any] = await request.json()

    logger.info(f"GitHub webhook received: event={event}")

    # TODO: Match event to AlertRule and trigger
    # For now, just acknowledge
    return JSONResponse(content={"status": "received", "event": event})


def compute_hmac(secret: str, body: bytes) -> str:
    """Compute HMAC-SHA256 signature for webhook validation."""
    import hmac
    import hashlib
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)