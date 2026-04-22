"""Alert engine for evaluating and sending alerts."""
import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from .database import session_context
from .models import AlertRule, AlertLog

logger = logging.getLogger(__name__)


class AlertEngine:
    """Engine for evaluating alert rules and triggering notifications."""

    def __init__(self, bot=None):
        """Initialize alert engine with optional bot reference."""
        self.bot = bot

    async def evaluate_event(self, event_type: str, payload: dict[str, Any]) -> list[int]:
        """Evaluate event-based rules and return list of triggered rule_ids."""
        triggered = []

        async with session_context() as session:
            result = await session.execute(
                select(AlertRule).where(
                    AlertRule.trigger_type == "event",
                    AlertRule.is_enabled == True,
                )
            )
            rules = result.scalars().all()

            for rule in rules:
                config = rule.trigger_config or {}
                if config.get("event") == event_type:
                    await self._trigger_rule(rule, payload)
                    triggered.append(rule.rule_id)

        return triggered

    async def _trigger_rule(self, rule: AlertRule, payload: dict[str, Any]) -> None:
        """Trigger a single alert rule."""
        # Create pending log entry
        async with session_context() as session:
            log = AlertLog(
                rule_id=rule.rule_id,
                status="pending",
                payload=payload,
            )
            session.add(log)
            await session.commit()
            log_id = log.log_id

        logger.info(f"Alert rule {rule.rule_id} triggered (log_id={log_id})")

        # If bot is available, send the message
        if self.bot:
            try:
                message = self._render_template(rule.message_template, payload)
                await self.bot.send_message(
                    chat_id=rule.target_chat_id,
                    text=message,
                )

                # Update log as sent
                async with session_context() as session:
                    result = await session.execute(
                        select(AlertLog).where(AlertLog.log_id == log_id)
                    )
                    log_entry = result.scalar_one_or_none()
                    if log_entry:
                        log_entry.status = "sent"
                        log_entry.sent_at = datetime.utcnow()
                        await session.commit()

            except Exception as e:
                logger.error(f"Failed to send alert {log_id}: {e}")
                async with session_context() as session:
                    result = await session.execute(
                        select(AlertLog).where(AlertLog.log_id == log_id)
                    )
                    log_entry = result.scalar_one_or_none()
                    if log_entry:
                        log_entry.status = "failed"
                        log_entry.error_msg = str(e)
                        await session.commit()

    def _render_template(self, template: str, payload: dict[str, Any]) -> str:
        """Simple template rendering with {key} substitution."""
        try:
            return template.format(**payload)
        except KeyError:
            return template


# Singleton instance
_alert_engine: AlertEngine | None = None


def get_alert_engine(bot=None) -> AlertEngine:
    """Get or create the alert engine singleton."""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine(bot)
    return _alert_engine
