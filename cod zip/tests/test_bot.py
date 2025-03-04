import pytest
import os
from unittest.mock import patch, MagicMock
from bot import TelegramBot

def test_bot_initialization():
    """Проверка инициализации бота"""
    with patch.dict('os.environ', {'BOT_TOKEN': 'test_token'}):
        bot = TelegramBot()
        assert bot.token == 'test_token'
        assert bot.app is None
        assert bot._running is False

def test_bot_initialization_without_token():
    """Проверка инициализации бота без токена"""
    with patch.dict('os.environ', clear=True):
        with pytest.raises(ValueError):
            TelegramBot()

@pytest.mark.asyncio
async def test_bot_start():
    """Проверка запуска бота"""
    with patch.dict('os.environ', {'BOT_TOKEN': 'test_token'}):
        with patch('telegram.ext.Application') as mock_app:
            mock_app_instance = MagicMock()
            mock_app.builder.return_value.token.return_value.build.return_value = mock_app_instance
            
            bot = TelegramBot()
            await bot.start()
            
            assert bot._running is True
            mock_app_instance.initialize.assert_called_once()
            mock_app_instance.start.assert_called_once()
            mock_app_instance.run_polling.assert_called_once_with(drop_pending_updates=True)

@pytest.mark.asyncio
async def test_bot_stop():
    """Проверка остановки бота"""
    with patch.dict('os.environ', {'BOT_TOKEN': 'test_token'}):
        with patch('telegram.ext.Application') as mock_app:
            mock_app_instance = MagicMock()
            mock_app.builder.return_value.token.return_value.build.return_value = mock_app_instance
            
            bot = TelegramBot()
            bot.app = mock_app_instance
            bot._running = True
            
            await bot.stop()
            
            assert bot._running is False
            mock_app_instance.stop.assert_called_once()
            mock_app_instance.shutdown.assert_called_once()
