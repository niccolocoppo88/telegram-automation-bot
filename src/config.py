"""Environment configuration using Pydantic."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


def _parse_admin_ids(value: str | list[int] | None) -> list[int]:
    """Parse admin user IDs from comma-separated string."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    return []


class Settings(BaseSettings):
    """Bot settings loaded from environment variables."""

    telegram_bot_token: str = ""
    database_url: str = "sqlite+aiosqlite:///./bot.db"
    admin_user_ids: str = ""  # Comma-separated string from env
    log_level: str = "INFO"
    github_webhook_secret: str = ""
    webhook_host: str = "https://your-domain.com"
    webhook_port: int = 8080

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def is_admin(self, user_id: int) -> bool:
        """Check if user_id is an admin."""
        admin_ids = _parse_admin_ids(self.admin_user_ids)
        return user_id in admin_ids


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()