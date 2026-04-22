"""Telegram command handlers."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from .database import session_context
from .models import User, AlertRule
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - register user."""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name

    async with session_context() as session:
        # Check if user exists
        result = await session.execute(
            "SELECT user_id FROM users WHERE user_id = :user_id", {"user_id": user_id}
        )
        existing = result.fetchone()

        if existing:
            await update.message.reply_text(
                f"👋 Welcome back, {username}!\n\n"
                "You're already registered. Use /help to see available commands."
            )
        else:
            # Check if first user (make them admin)
            result = await session.execute("SELECT COUNT(*) as cnt FROM users")
            count = result.fetchone()[0]
            is_admin = count == 0

            new_user = User(
                user_id=user_id,
                username=username,
                is_admin=is_admin,
                is_active=True,
            )
            session.add(new_user)
            await session.commit()

            admin_note = " (you are the first admin!)" if is_admin else ""
            await update.message.reply_text(
                f"🎉 Welcome, {username}! You've been registered.{admin_note}\n\n"
                "Use /help to see available commands."
            )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command - show help."""
    await update.message.reply_text(
        "📚 *Available Commands:*\n\n"
        "/start - Register with the bot\n"
        "/help - Show this help message\n"
        "/status - Show bot statistics\n"
        "/ping - Check bot latency\n"
        "/broadcast `<message>` - Send message to all users (admin only)\n"
        "/alert `<action>` - Manage alert rules (admin only)\n\n"
        "Use /alert add, /alert list, /alert delete `<id>`, "
        "/alert enable `<id>`, /alert disable `<id>`",
        parse_mode="Markdown",
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command - show bot statistics."""
    async with session_context() as session:
        # Get user stats
        result = await session.execute(
            "SELECT COUNT(*) as total, SUM(is_active) as active FROM users"
        )
        user_stats = result.fetchone()
        total_users = user_stats[0] if user_stats else 0
        active_users = user_stats[1] if user_stats[1] else 0

        # Get alert rule stats
        result = await session.execute(
            "SELECT COUNT(*) as total, SUM(is_enabled) as enabled FROM alert_rules"
        )
        rule_stats = result.fetchone()
        total_rules = rule_stats[0] if rule_stats else 0
        enabled_rules = rule_stats[1] if rule_stats[1] else 0

        # Get alert log stats
        result = await session.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed FROM alert_logs"
        )
        log_stats = result.fetchone()
        total_alerts = log_stats[0] if log_stats else 0
        alerts_failed = log_stats[1] if log_stats[1] else 0

    await update.message.reply_text(
        "📊 *Bot Statistics*\n\n"
        f"👥 Users: {active_users}/{total_users} active\n"
        f"🔔 Alert Rules: {enabled_rules}/{total_rules} enabled\n"
        f"📨 Alerts Sent: {total_alerts} ({alerts_failed} failed)",
        parse_mode="Markdown",
    )


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ping command - latency check."""
    import time

    start = time.time()
    # Quick DB ping
    async with session_context() as session:
        await session.execute("SELECT 1")
    latency = (time.time() - start) * 1000
    await update.message.reply_text(f"🏓 Pong! DB latency: {latency:.1f}ms")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /broadcast command - send message to all users (admin only)."""
    user_id = update.effective_user.id

    # Check admin
    if not settings.is_admin(user_id):
        await update.message.reply_text("⛔ Unauthorized. Admin only.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast `<message>`")
        return

    message = " ".join(context.args)

    async with session_context() as session:
        result = await session.execute("SELECT user_id FROM users WHERE is_active = 1")
        users = result.fetchall()
        user_ids = [u[0] for u in users]

    if not user_ids:
        await update.message.reply_text("No active users to send to.")
        return

    await update.message.reply_text(f"📢 Sending to {len(user_ids)} users...")

    sent = 0
    failed = 0
    rate_limited = []
    for uid in user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
            # Simple rate limit mitigation
            import asyncio

            await asyncio.sleep(0.05)  # 50ms between messages
        except Exception as e:
            logger.error(f"Failed to send to {uid}: {e}")
            # Check if rate limited (429)
            if "429" in str(e) or "Too Many Requests" in str(e):
                rate_limited.append(uid)
                # Exponential backoff would go here in production
                await asyncio.sleep(1)
            failed += 1

    status_msg = f"📢 Broadcast complete.\nSent: {sent}\nFailed: {failed}"
    if rate_limited:
        status_msg += f"\nRate limited: {len(rate_limited)}"
    await update.message.reply_text(status_msg)


async def alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alert command - manage alert rules (admin only)."""
    user_id = update.effective_user.id

    # Check admin
    if not settings.is_admin(user_id):
        await update.message.reply_text("⛔ Unauthorized. Admin only.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /alert `<action>`\n"
            "Actions: add, list, delete `<id>`, enable `<id>`, disable `<id>`"
        )
        return

    action = context.args[0].lower()

    if action == "list":
        async with session_context() as session:
            result = await session.execute(
                "SELECT rule_id, name, trigger_type, is_enabled FROM alert_rules"
            )
            rules = result.fetchall()

        if not rules:
            await update.message.reply_text("No alert rules configured.")
            return

        lines = ["🔔 *Alert Rules:*\n"]
        for r in rules:
            status = "✅" if r[3] else "❌"
            lines.append(f"{status} `[{r[0]}]` {r[1]} ({r[2]})")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    elif action == "add":
        # Usage: /alert add <name> <trigger_type> <target_chat_id> <message_template>
        if len(context.args) < 4:
            await update.message.reply_text(
                "Usage: /alert add `<name>` `<trigger_type>` `<target_chat_id>` `<message_template>`\n\n"
                'Example: /alert add "My Alert" event 123456 "New push to {repo}"\n\n'
                "trigger_type: event, cron, or manual"
            )
            return

        name = context.args[0]
        trigger_type = context.args[1].lower()
        try:
            target_chat_id = int(context.args[2])
        except ValueError:
            await update.message.reply_text("Invalid target_chat_id. Must be a number.")
            return
        message_template = " ".join(context.args[3:])

        # Validate trigger_type
        if trigger_type not in ("event", "cron", "manual"):
            await update.message.reply_text(
                "Invalid trigger_type. Use: event, cron, or manual"
            )
            return

        # Parse trigger_config based on type
        if trigger_type == "event":
            trigger_config = {"event": "push"}
        elif trigger_type == "cron":
            trigger_config = {"schedule": "0 9 * * *"}
        else:
            trigger_config = {}

        async with session_context() as session:
            new_rule = AlertRule(
                name=name,
                trigger_type=trigger_type,
                trigger_config=trigger_config,
                message_template=message_template,
                target_chat_id=target_chat_id,
                created_by=user_id,
            )
            session.add(new_rule)
            await session.commit()
            rule_id = new_rule.rule_id

        await update.message.reply_text(
            f"✅ Alert rule created!\n\n"
            f"ID: {rule_id}\n"
            f"Name: {name}\n"
            f"Trigger: {trigger_type}\n"
            f"Target: {target_chat_id}\n\n"
            f"Edit via API or /alert list to manage"
        )

    elif action == "delete":
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /alert delete `<rule_id>`")
            return
        try:
            rule_id = int(context.args[1])
        except ValueError:
            await update.message.reply_text("Invalid rule ID.")
            return

        async with session_context() as session:
            await session.execute(
                "DELETE FROM alert_rules WHERE rule_id = :rule_id", {"rule_id": rule_id}
            )
            await session.commit()

        await update.message.reply_text(f"🗑️ Alert rule {rule_id} deleted.")

    elif action in ("enable", "disable"):
        if len(context.args) < 2:
            await update.message.reply_text(f"Usage: /alert {action} `<rule_id>`")
            return
        try:
            rule_id = int(context.args[1])
        except ValueError:
            await update.message.reply_text("Invalid rule ID.")
            return

        new_state = action == "enable"
        async with session_context() as session:
            await session.execute(
                "UPDATE alert_rules SET is_enabled = :state WHERE rule_id = :rule_id",
                {"state": new_state, "rule_id": rule_id},
            )
            await session.commit()

        state_str = "enabled" if new_state else "disabled"
        await update.message.reply_text(f"✅ Alert rule {rule_id} {state_str}.")

    else:
        await update.message.reply_text(
            "Unknown action. Use: add, list, delete, enable, disable"
        )


# Command registry for bot setup
COMMAND_HANDLERS = {
    "start": start_command,
    "help": help_command,
    "status": status_command,
    "ping": ping_command,
    "broadcast": broadcast_command,
    "alert": alert_command,
}
