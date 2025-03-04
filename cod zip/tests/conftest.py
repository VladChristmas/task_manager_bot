import pytest
import os
import tempfile
from unittest.mock import MagicMock
from telegram import Update
from telegram.ext import ContextTypes
from database import Database

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.effective_chat.id = 123456789
    update.effective_user.id = 5171183387  # Admin ID from .env
    update.effective_user.username = "test_user"
    update.message = MagicMock()
    update.message.text = "/start"
    return update

@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context

@pytest.fixture
def temp_db():
    # Создаем временную базу данных для тестов
    fd, path = tempfile.mkstemp()
    db = Database(path)
    db._ensure_database()
    
    yield db
    
    # Очищаем после тестов
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.send_message = MagicMock()
    bot.send_document = MagicMock()
    return bot
