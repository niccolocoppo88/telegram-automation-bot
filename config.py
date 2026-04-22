"""Configuration management via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram Bot
    telegram_bot_token: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/bot.db"

    # OpenAI
    openai_api_key: str = ""

    # GitHub Webhook
    github_webhook_secret: str = ""

    # Admin users (comma-separated Telegram user IDs)
    admin_user_ids: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Log level
    log_level: str = "INFO"


settings = Settings()