"""Main bot entry point."""

import asyncio
import logging
import os
import signal
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import get_settings
from .database import init_db, close_db
from .handlers import COMMAND_HANDLERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global application reference
app: Application | None = None


async def post_init(application: Application) -> None:
    """Post-initialization hook."""
    await init_db()
    logger.info("Database initialized")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context.error}")


def setup_bot() -> Application:
    """Set up and return the bot application."""
    global app

    settings = get_settings()
    bot_token = settings.telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")

    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")

    # Build application
    app = Application.builder().token(bot_token).post_init(post_init).build()

    # Add command handlers
    for command, handler in COMMAND_HANDLERS.items():
        app.add_handler(CommandHandler(command, handler))

    # Add error handler
    app.add_error_handler(error_handler)

    return app


async def run_bot() -> None:
    """Run the bot."""
    application = setup_bot()

    # Handle shutdown gracefully
    loop = asyncio.get_event_loop()

    def shutdown():
        logger.info("Shutting down...")
        asyncio.create_task(application.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown)

    # Start polling
    logger.info("Starting bot...")
    await application.initialize()
    await application.start()
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

    # Cleanup
    await close_db()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise


if __name__ == "__main__":
    main()
