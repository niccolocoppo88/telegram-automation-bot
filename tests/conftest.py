"""
Test configuration and fixtures for Telegram Automation Bot tests.
"""
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

# Set test environment before importing app modules
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token_123"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test_secret"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_bot():
    """Mock telegram.Bot with controlled responses"""
    bot = MagicMock()
    bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))
    bot.edit_message_text = AsyncMock(return_value=MagicMock())
    bot.delete_message = AsyncMock(return_value=MagicMock())
    bot.get_me = AsyncMock(return_value=MagicMock(
        id=123456,
        username="test_bot",
        first_name="Test Bot"
    ))
    return bot


@pytest.fixture
def mock_update():
    """Mock telegram.Update"""
    update = MagicMock()
    update.effective_user = MagicMock(
        id=12345,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    update.effective_chat = MagicMock(id=67890)
    update.effective_message = MagicMock(
        message_id=111,
        chat=MagicMock(id=67890),
        date=datetime.now(),
        text="/start"
    )
    update.callback_query = None
    return update


@pytest.fixture
def mock_context():
    """Mock telegram.ext.Context"""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))
    context.bot_data = {}
    context._chat_id = 67890
    return context


@pytest.fixture
def mock_application():
    """Mock telegram.ext.Application"""
    app = MagicMock()
    app.bot = MagicMock()
    app.bot.send_message = AsyncMock(return_value=MagicMock(message_id=123))
    app.update_queue = MagicMock()
    return app


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "user_id": 12345,
        "username": "testuser",
        "is_admin": False,
        "is_active": True,
        "registered_at": datetime.now()
    }


@pytest.fixture
def sample_admin_data():
    """Sample admin user data for testing"""
    return {
        "user_id": 99999,
        "username": "admin",
        "is_admin": True,
        "is_active": True,
        "registered_at": datetime.now()
    }


@pytest.fixture
def sample_alert_rule():
    """Sample alert rule for testing"""
    return {
        "rule_id": 1,
        "name": "Test Rule",
        "trigger_type": "event",
        "trigger_config": {"event": "push", "repo": "test/repo"},
        "message_template": "Test alert: {event}",
        "target_chat_id": 67890,
        "is_enabled": True,
        "created_by": 99999,
        "created_at": datetime.now()
    }


@pytest.fixture
def sample_cron_rule():
    """Sample cron alert rule for testing"""
    return {
        "rule_id": 2,
        "name": "Daily Report",
        "trigger_type": "cron",
        "trigger_config": {"schedule": "0 9 * * *"},
        "message_template": "Daily report at {time}",
        "target_chat_id": 67890,
        "is_enabled": True,
        "created_by": 99999,
        "created_at": datetime.now()
    }


@pytest.fixture
def mock_github_webhook_push():
    """Mock GitHub push webhook payload"""
    return {
        "ref": "refs/heads/main",
        "repository": {
            "name": "test-repo",
            "full_name": "test/test-repo",
            "html_url": "https://github.com/test/test-repo"
        },
        "commits": [
            {
                "message": "Test commit",
                "author": {"name": "Test Author", "email": "test@example.com"}
            }
        ],
        "pusher": {"name": "testuser"}
    }


@pytest.fixture
def mock_github_webhook_pr():
    """Mock GitHub pull_request webhook payload"""
    return {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "title": "Test PR",
            "state": "open",
            "user": {"login": "testuser"},
            "html_url": "https://github.com/test/test-repo/pull/42"
        },
        "repository": {
            "name": "test-repo",
            "full_name": "test/test-repo"
        }
    }


@pytest.fixture
def mock_github_webhook_issues():
    """Mock GitHub issues webhook payload"""
    return {
        "action": "opened",
        "issue": {
            "number": 1,
            "title": "Test Issue",
            "state": "open",
            "user": {"login": "testuser"},
            "html_url": "https://github.com/test/test-repo/issues/1"
        },
        "repository": {
            "name": "test-repo",
            "full_name": "test/test-repo"
        }
    }


@pytest.fixture
def mock_rate_limit_response():
    """Simulate Telegram 429 rate limit response"""
    class MockRateLimitError(Exception):
        def __init__(self):
            self.description = "Too Many Requests: retry after 1"
            self.retry_after = 1


@pytest.fixture
def mock_telegram_error_500():
    """Simulate Telegram 500 server error"""
    class MockServerError(Exception):
        def __init__(self):
            self.description = "Internal Server Error"


@pytest.fixture
def test_db_session():
    """In-memory SQLite session for testing"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:", echo=False)
    Session = sessionmaker(bind=engine)

    # Import models to ensure they're registered
    from src.models import Base, User, AlertRule, AlertLog

    # Create all tables
    Base.metadata.create_all(engine)

    session = Session()
    yield session
    session.close()