"""
Обработчики команд для Telegram бота
"""
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    CallbackContext, 
    CommandHandler, 
    MessageHandler, 
    Filters
)
from database import Database
from navigation_manager import NavigationManager
from constants import *
from utils import (
    is_valid_report_format,
    is_valid_file_size,
    format_report_info,
    is_admin
)

logger = logging.getLogger(__name__)
db = Database("bot_database.db")
nav_manager = NavigationManager()

def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    try:
        logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
        keyboard = [
            [KeyboardButton("📝 Создать новое задание")],
            [KeyboardButton("📋 Просмотр активных заданий")],
            [KeyboardButton("👥 Просмотр списка подключенных чатов")],
            [KeyboardButton("👥 Создать группу чатов")],
            [KeyboardButton("⚙️ Настройки")],
            [KeyboardButton("❓ Помощь")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text("Главное меню:", reply_markup=reply_markup)
        logger.info("Главное меню успешно отображено")
    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        error_handler(update, context)

def help_command(update: Update, context: CallbackContext):
    """Handle help command"""
    try:
        update.message.reply_text(HELP_TEXT)
    except Exception as e:
        logger.error(f"Error in help command: {e}", exc_info=True)
        error_handler(update, context)

def add_chat_command(update: Update, context: CallbackContext):
    """Handle add chat command"""
    try:
        update.message.reply_text("Функция добавления чата будет реализована позже")
    except Exception as e:
        logger.error(f"Error in add chat command: {e}", exc_info=True)
        error_handler(update, context)

def handle_text_message(update: Update, context: CallbackContext):
    """Handle text messages"""
    try:
        message_text = update.message.text
        logger.info(f"Received text message from user {update.effective_user.id}: {message_text}")
        update.message.reply_text("Сообщение получено")
    except Exception as e:
        logger.error(f"Error in text message handler: {e}", exc_info=True)
        error_handler(update, context)

def error_handler(update: Update, context: CallbackContext):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        update.effective_message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )

def register_handlers(dispatcher):
    """Register all handlers"""
    try:
        # Basic commands
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("addchat", add_chat_command))

        # Message handlers
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_message))

        # Error handler
        dispatcher.add_error_handler(error_handler)

        logger.info("Handlers registered successfully")
    except Exception as e:
        logger.error(f"Error registering handlers: {e}", exc_info=True)
        raise