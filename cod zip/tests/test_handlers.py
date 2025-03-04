import pytest
from unittest.mock import patch, MagicMock
from handlers import start_command, help_command, debug_db_command
from constants import HELP_TEXT, WELCOME_MESSAGE

@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context):
    """Проверка команды /start"""
    await start_command(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args
    assert WELCOME_MESSAGE in args[0]

@pytest.mark.asyncio
async def test_help_command(mock_update, mock_context):
    """Проверка команды /help"""
    await help_command(mock_update, mock_context)
    
    mock_update.message.reply_text.assert_called_once_with(HELP_TEXT)

@pytest.mark.asyncio
async def test_debug_db_command_admin(mock_update, mock_context, temp_db):
    """Проверка команды /debug_db для администратора"""
    with patch('handlers.is_admin', return_value=True):
        await debug_db_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once()

@pytest.mark.asyncio
async def test_debug_db_command_non_admin(mock_update, mock_context):
    """Проверка команды /debug_db для не-администратора"""
    with patch('handlers.is_admin', return_value=False):
        await debug_db_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_called_once_with(
            "У вас нет прав для выполнения этой команды."
        )
