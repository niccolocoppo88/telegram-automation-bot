"""Main bot entry point."""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import settings
from src import handlers as h


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, settings.log_level, logging.INFO),
    )


async def post_init(application: Application) -> None:
    """Run after bot initialization."""
    await application.bot.set_my_commands([
        ("start", "Start the bot and register"),
        ("help", "Show available commands"),
        ("status", "Show bot status and statistics"),
        ("ping", "Check bot responsiveness"),
        ("alert", "Manage alert rules"),
    ])


def create_app() -> Application:
    """Create and configure the bot application."""
    setup_logging()

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    # Register command handlers
    app.add_handler(CommandHandler("start", h.start))
    app.add_handler(CommandHandler("help", h.help))
    app.add_handler(CommandHandler("status", h.status))
    app.add_handler(CommandHandler("ping", h.ping))
    app.add_handler(CommandHandler("alert", h.alert))
    app.add_handler(CommandHandler("broadcast", h.broadcast))

    # Register error handler
    app.add_error_handler(h.error_handler)

    return app


def main() -> None:
    """Run the bot."""
    app = create_app()
    app.run_polling()


if __name__ == "__main__":
    main()