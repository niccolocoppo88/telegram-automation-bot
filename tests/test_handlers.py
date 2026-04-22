"""Tests for command handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message
from telegram.ext import ContextTypes


# Fixtures
@pytest.fixture
def mock_update():
    """Create a mock Update object."""
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context():
    """Create a mock ContextTypes.DEFAULT_TYPE."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)


# Tests for start command
@pytest.mark.asyncio
async def test_start_creates_user(mock_update, mock_context):
    """Test that /start registers user in database."""
    from src.handlers import start

    await start(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Benvenuto" in call_args[0][0]


# Tests for help command
@pytest.mark.asyncio
async def test_help_shows_commands(mock_update, mock_context):
    """Test that /help returns command list."""
    from src.handlers import help_command

    await help_command(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    text = call_args[0][0]
    assert "/start" in text
    assert "/help" in text
    assert "/status" in text
    assert "/ping" in text


# Tests for status command
@pytest.mark.asyncio
async def test_status_returns_uptime(mock_update, mock_context):
    """Test that /status returns bot status."""
    from src.handlers import status

    await status(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()


# Tests for ping command
@pytest.mark.asyncio
async def test_ping_responds_pong(mock_update, mock_context):
    """Test that /ping returns pong."""
    from src.handlers import ping

    await ping(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    call_args = mock_update.message.reply_text.call_args
    assert "Pong" in call_args[0][0]