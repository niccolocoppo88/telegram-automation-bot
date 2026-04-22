"""Shared pytest fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from telegram import Update, Message, User as TelegramUser
from telegram.ext import ContextTypes


@pytest.fixture
def mock_update():
    """Create a mock Update object."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.chat = MagicMock()
    update.message.chat.id = 123456
    return update


@pytest.fixture
def mock_context():
    """Create a mock ContextTypes.DEFAULT_TYPE."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context


@pytest.fixture
def mock_user():
    """Create a mock Telegram User."""
    user = MagicMock(spec=TelegramUser)
    user.id = 123456
    user.username = "testuser"
    user.first_name = "Test"
    return user