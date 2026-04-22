"""Command handlers for Telegram bot."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command — register user and show welcome message."""
    await update.message.reply_text(
        "👋 Benvenuto nel Telegram Automation Bot!\n\n"
        "Usa /help per vedere i comandi disponibili."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command — show command list."""
    await update.message.reply_text(
        "📋 **Comandi disponibili:**\n\n"
        "/start - Registrati al bot\n"
        "/help - Mostra questa lista\n"
        "/status - Mostra stato del bot\n"
        "/ping - Verifica responsività\n"
        "/alert - Gestisci regole di alert\n"
        "/broadcast <messaggio> - Invia messaggio a tutti (admin only)"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command — show bot status and statistics."""
    await update.message.reply_text(
        f"✅ Bot attivo — uptime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ping command — respond with pong and latency."""
    start_time = datetime.now()
    await update.message.reply_text("🏓 Pong!")
    latency = (datetime.now() - start_time).total_seconds() * 1000
    logger.info(f"Ping response, latency: {latency:.2f}ms")


async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alert command — manage alert rules."""
    await update.message.reply_text(
        "⚠️ Gestione alert — TODO: implementare CRUD alert rules"
    )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /broadcast command — send message to all users (admin only)."""
    await update.message.reply_text(
        "📢 Broadcast — TODO: implementare invio a tutti gli utenti"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unexpected errors."""
    logger.error(f"Exception while handling an update: {context.error}")


# Alias for compatibility
help = help_command