"""Tests for Telegram command handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User as TGUser, Message, Chat


@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    user = TGUser(id=123456, is_bot=False, first_name="Test", username="testuser")
    chat = Chat(id=123456, type="private")
    message = MagicMock(spec=Message)
    message.from_user = user
    message.chat = chat
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.effective_user = user
    update.effective_message = message
    update.message = message
    return update


@pytest.fixture
def mock_context():
    """Create a mock Telegram context."""
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.args = []
    return context


@pytest.mark.asyncio
async def test_start_command_new_user(mock_update, mock_context):
    """Test /start command for new user."""
    from src.handlers import start_command

    with patch("src.handlers.session_context") as mock_session_ctx:
        mock_session = AsyncMock()

        # First call: check if user exists (returns None = user doesn't exist)
        # Second call: count users (returns (0,) = first user)
        mock_result1 = MagicMock()
        mock_result1.fetchone = MagicMock(return_value=None)
        mock_result2 = MagicMock()
        mock_result2.fetchone = MagicMock(return_value=(0,))

        mock_session.execute = AsyncMock(side_effect=[mock_result1, mock_result2])

        mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.return_value.__aexit__ = AsyncMock()

        await start_command(mock_update, mock_context)

        # Verify reply was sent
        mock_update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context):
    """Test /help command."""
    from src.handlers import help_command

    await help_command(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()


@pytest.mark.asyncio
async def test_status_command(mock_update, mock_context):
    """Test /status command."""
    from src.handlers import status_command

    with patch("src.handlers.session_context") as mock_session_ctx:
        mock_session = AsyncMock()
        # Return values for user stats, rule stats, log stats
        mock_session.execute = AsyncMock(
            side_effect=[
                AsyncMock().return_value,
                AsyncMock().return_value,
                AsyncMock().return_value,
            ]
        )
        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(
            side_effect=[
                (10, 8),  # user stats
                (5, 4),  # rule stats
                (100, 2),  # log stats
            ]
        )
        mock_session.execute.return_value = mock_result

        mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.return_value.__aexit__ = AsyncMock()

        await status_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called()
