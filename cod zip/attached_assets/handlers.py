import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters
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
db = Database("bot_database.db")  # Используем тот же путь, что и в bot.py
nav_manager = NavigationManager()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text("Главное меню:", reply_markup=reply_markup)
        logger.info("Главное меню успешно отображено")
    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        await error_handler(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    try:
        logger.info(f"Получена команда /help от пользователя {update.effective_user.id}")
        await update.message.reply_text(HELP_TEXT)
        logger.info("Справка успешно отображена")
    except Exception as e:
        logger.error(f"Error in help command: {e}", exc_info=True)
        await error_handler(update, context)

async def add_chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addchat command"""
    try:
        logger.info(f"Получена команда /addchat от пользователя {update.effective_user.id}")

        # Проверяем тип чата
        chat_id = update.effective_chat.id
        chat_title = update.effective_chat.title
        if not chat_title and update.effective_chat.type == 'private':
            chat_title = f"Личный чат с {update.effective_user.first_name}"

        is_group = update.effective_chat.type in ['group', 'supergroup']

        logger.info(f"Попытка добавления чата: ID={chat_id}, Title={chat_title}, Type={update.effective_chat.type}")

        # Проверяем, не добавлен ли уже этот чат
        existing_chat = db.execute_query("SELECT chat_id FROM chats WHERE chat_id = ?", (chat_id,))
        if existing_chat:
            await update.message.reply_text(
                "Этот чат уже подключен к боту.\n"
                "Используйте команду меню '👥 Просмотр списка подключенных чатов' для просмотра всех чатов."
            )
            logger.info(f"Попытка повторного добавления существующего чата: {chat_id}")
            return

        # Добавляем новый чат
        db.execute_query(
            "INSERT INTO chats (chat_id, title, is_group) VALUES (?, ?, ?)",
            (chat_id, chat_title, is_group)
        )

        logger.info(f"Добавлен новый чат: {chat_title} ({chat_id})")
        await update.message.reply_text(
            f"Чат успешно подключен к боту!\n"
            f"Тип чата: {'Группа' if is_group else 'Личный чат'}\n"
            f"Используйте команду меню '👥 Просмотр списка подключенных чатов' для просмотра всех чатов."
        )

    except Exception as e:
        logger.error(f"Error in add chat command: {e}", exc_info=True)
        await error_handler(update, context)

async def create_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle task creation"""
    try:
        logger.info(f"Начало создания задания от пользователя {update.effective_user.id}")
        context.user_data['state'] = 'awaiting_task_text'
        keyboard = [
            [KeyboardButton("🔙 Отмена")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Введите текст задания или отправьте файлы (фото/документы).\n"
            "Поддерживаемые форматы: pdf, doc, docx, xls, xlsx, txt",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in create task command: {e}", exc_info=True)
        await error_handler(update, context)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings command"""
    try:
        logger.info(f"Открытие настроек пользователем {update.effective_user.id}")
        if not is_admin(update.effective_user.id):
            logger.warning(f"Попытка неавторизованного доступа к настройкам")
            await update.message.reply_text(UNAUTHORIZED)
            return

        keyboard = [
            [KeyboardButton("👥 Управление чатами")],
            [KeyboardButton("📊 Настройки уведомлений")],
            [KeyboardButton("🔙 Назад")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Настройки:", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in settings command: {e}", exc_info=True)
        await error_handler(update, context)

async def create_chat_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chat group creation"""
    try:
        logger.info(f"Начало создания группы чатов пользователем {update.effective_user.id}")
        context.user_data['state'] = 'creating_chat_group'
        keyboard = [
            [KeyboardButton("🔙 Отмена")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Введите название для новой группы чатов:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in create chat group command: {e}", exc_info=True)
        await error_handler(update, context)

async def view_connected_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle viewing connected chats"""
    try:
        logger.info(f"Получена команда просмотра подключенных чатов от пользователя {update.effective_user.id}")

        # Получаем список подключенных чатов из базы данных
        chats = db.execute_query("""
            SELECT chat_id, title, is_group, added_at
            FROM chats
            ORDER BY added_at DESC
        """)

        logger.info(f"Найдено чатов в базе данных: {len(chats) if chats else 0}")

        if not chats:
            await update.message.reply_text("Нет подключенных чатов. Используйте команду /addchat в чате или группе, чтобы добавить их в список.")
            logger.info("Подключенные чаты не найдены")
            return

        # Формируем ответ с информацией о чатах
        response = "👥 Подключенные чаты:\n\n"
        for chat in chats:
            chat_type = "Группа" if chat['is_group'] else "Личный чат"
            response += f"• {chat['title']}\n"
            response += f"  Тип: {chat_type}\n"
            response += f"  ID: {chat['chat_id']}\n"
            response += f"  Добавлен: {chat['added_at']}\n\n"

        await update.message.reply_text(response)
        logger.info("Список подключенных чатов успешно отправлен")

    except Exception as e:
        logger.error(f"Error in view connected chats command: {e}", exc_info=True)
        await error_handler(update, context)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    try:
        message_text = update.message.text
        logger.info(f"Получено текстовое сообщение от пользователя {update.effective_user.id}: {message_text}")

        # Обработка кнопок главного меню
        if message_text == "📝 Создать новое задание":
            await create_task_command(update, context)
        elif message_text == "📋 Просмотр активных заданий":
            await view_active_tasks_command(update, context)
        elif message_text == "👥 Просмотр списка подключенных чатов":
            await view_connected_chats_command(update, context)
        elif message_text == "⚙️ Настройки":
            await settings_command(update, context)
        elif message_text == "❓ Помощь":
            await help_command(update, context)
        elif message_text == "👥 Создать группу чатов":
            await create_chat_group_command(update, context)
        elif message_text == "🔙 Отмена" or message_text == "🔙 Назад":
            context.user_data.clear()  # Очищаем пользовательские данные
            await start_command(update, context)
        else:
            # Логируем необработанное сообщение
            logger.info(f"Необработанное сообщение: {update.to_dict()}")
            # Отправляем пользователю сообщение о том, что команда не распознана
            await update.message.reply_text(INVALID_COMMAND)

    except Exception as e:
        logger.error(f"Error handling text message: {e}", exc_info=True)
        await error_handler(update, context)

async def submit_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /submit_report command"""
    try:
        logger.info(f"Получена команда /submit_report от пользователя {update.effective_user.id}")
        # Create task in database
        task_id = db.create_task(
            text="New report submission",
            creator_id=update.effective_user.id
        )

        context.user_data['awaiting_report'] = True
        context.user_data['current_task_id'] = task_id

        await update.message.reply_text("Please send your report file.")
        logger.info(f"Создано новое задание с ID: {task_id}")
    except Exception as e:
        logger.error(f"Error in submit report command: {e}", exc_info=True)
        await error_handler(update, context)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document messages"""
    try:
        logger.info(f"Получен документ от пользователя {update.effective_user.id}")
        if not context.user_data.get('awaiting_report'):
            logger.warning("Получен документ, но не ожидается отчет")
            return

        document = update.message.document
        if not is_valid_report_format(document.file_name):
            logger.warning(f"Неверный формат файла: {document.file_name}")
            await update.message.reply_text(INVALID_FORMAT)
            return

        if not is_valid_file_size(document.file_size):
            logger.warning(f"Файл слишком большой: {document.file_size} bytes")
            await update.message.reply_text(REPORT_TOO_LARGE)
            return

        task_id = context.user_data.get('current_task_id')
        if not task_id:
            logger.error("Не найдено активное задание")
            await update.message.reply_text("Error: No active task found")
            return

        # Save file information using new database structure
        db.execute_query(
            "INSERT INTO task_media (task_id, file_id, file_type) VALUES (?, ?, ?)",
            (task_id, document.file_id, 'document')
        )

        context.user_data['awaiting_report'] = False
        await update.message.reply_text(REPORT_SUBMITTED)
        logger.info(f"Документ успешно сохранен для задания {task_id}")

    except Exception as e:
        logger.error(f"Error handling document: {e}", exc_info=True)
        await error_handler(update, context)

async def my_reports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_reports command"""
    try:
        logger.info(f"Получена команда /my_reports от пользователя {update.effective_user.id}")
        # Get user's tasks from database
        tasks = db.execute_query("""
            SELECT t.*, tm.file_id, tm.file_type
            FROM tasks t
            LEFT JOIN task_media tm ON t.id = tm.task_id
            WHERE t.creator_id = ?
            ORDER BY t.created_at DESC
        """, (update.effective_user.id,))

        if not tasks:
            await update.message.reply_text(NO_REPORTS_FOUND)
            logger.info("Отчеты не найдены для пользователя")
            return

        response = "Your submitted reports:\n\n"
        for task in tasks:
            response += format_report_info(task) + "\n\n"

        await update.message.reply_text(response)
        logger.info(f"Отправлен список отчетов пользователю")

    except Exception as e:
        logger.error(f"Error in my reports command: {e}", exc_info=True)
        await error_handler(update, context)

async def collect_reports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /collect_reports command (admin only)"""
    try:
        logger.info(f"Получена команда /collect_reports от пользователя {update.effective_user.id}")
        if not is_admin(update.effective_user.id):
            logger.warning(f"Попытка неавторизованного доступа к команде collect_reports")
            await update.message.reply_text(UNAUTHORIZED)
            return

        # Get all tasks with their media files
        tasks = db.execute_query("""
            SELECT t.*, u.username, tm.file_id, tm.file_type
            FROM tasks t
            LEFT JOIN users u ON t.creator_id = u.user_id
            LEFT JOIN task_media tm ON t.id = tm.task_id
            ORDER BY t.created_at DESC
        """)

        if not tasks:
            await update.message.reply_text(NO_REPORTS_FOUND)
            logger.info("Отчеты не найдены")
            return

        response = "All submitted reports:\n\n"
        current_task_id = None
        for task in tasks:
            if current_task_id != task['id']:
                response += format_report_info(task) + "\n\n"
                current_task_id = task['id']

        await update.message.reply_text(response)
        logger.info("Отправлен полный список отчетов администратору")

    except Exception as e:
        logger.error(f"Error in collect reports command: {e}", exc_info=True)
        await error_handler(update, context)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    logger.error(f"Error details: {context.error}", exc_info=True)
    if update:
        logger.info(f"Update type: {type(update)}")
        logger.info(f"Update details: {update.to_dict()}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def view_active_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle viewing active tasks"""
    try:
        logger.info(f"Получена команда просмотра активных заданий от пользователя {update.effective_user.id}")

        # Получаем активные задания из базы данных
        tasks = db.execute_query("""
            SELECT t.*, tm.file_id, tm.file_type
            FROM tasks t
            LEFT JOIN task_media tm ON t.id = tm.task_id
            WHERE t.status = 'active'
            ORDER BY t.created_at DESC
        """)

        if not tasks:
            await update.message.reply_text("Нет активных заданий")
            logger.info("Активные задания не найдены")
            return

        # Формируем ответ с информацией о заданиях
        response = "📋 Активные задания:\n\n"
        current_task_id = None
        for task in tasks:
            if current_task_id != task['id']:
                response += format_report_info(task) + "\n\n"
                current_task_id = task['id']

        await update.message.reply_text(response)
        logger.info("Список активных заданий успешно отправлен")

    except Exception as e:
        logger.error(f"Error in view active tasks command: {e}", exc_info=True)
        await error_handler(update, context)


async def debug_db_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /debug_db command (admin only)"""
    try:
        logger.info(f"Получена команда /debug_db от пользователя {update.effective_user.id}")
        if not is_admin(update.effective_user.id):
            logger.warning(f"Попытка неавторизованного доступа к debug_db")
            await update.message.reply_text(UNAUTHORIZED)
            return

        # Проверяем таблицы
        tables = {
            'chats': db.execute_query("SELECT COUNT(*) as count FROM chats"),
            'chat_groups': db.execute_query("SELECT COUNT(*) as count FROM chat_groups"),
            'tasks': db.execute_query("SELECT COUNT(*) as count FROM tasks")
        }

        response = "📊 Статистика базы данных:\n\n"
        for table_name, count in tables.items():
            response += f"• {table_name}: {count[0]['count']} записей\n"

        # Получаем последние добавленные чаты
        recent_chats = db.execute_query("""
            SELECT chat_id, title, is_group, added_at
            FROM chats
            ORDER BY added_at DESC
            LIMIT 5
        """)

        if recent_chats:
            response += "\n🆕 Последние добавленные чаты:\n"
            for chat in recent_chats:
                response += f"• {chat['title']} (ID: {chat['chat_id']})\n"
                response += f"  Добавлен: {chat['added_at']}\n"

        await update.message.reply_text(response)
        logger.info("Отправлена отладочная информация о базе данных")

    except Exception as e:
        logger.error(f"Error in debug_db command: {e}", exc_info=True)
        await error_handler(update, context)

def register_handlers(application):
    """Register all handlers"""
    try:
        # Basic commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("addchat", add_chat_command))
        application.add_handler(CommandHandler("submit_report", submit_report_command))
        application.add_handler(CommandHandler("my_reports", my_reports_command))
        application.add_handler(CommandHandler("collect_reports", collect_reports_command))
        application.add_handler(CommandHandler("debug_db", debug_db_command))  # Добавляем новый обработчик

        # Message handlers
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

        # Add handler for logging all messages
        application.add_handler(MessageHandler(
            filters.ALL, 
            lambda update, context: logger.info(f"Received update: {update.to_dict()}")
        ))

        # Error handler
        application.add_error_handler(error_handler)

        logger.info("Handlers registered successfully")
        logger.info("Registered commands: /start, /help, /addchat, /submit_report, /my_reports, /collect_reports, /debug_db")
    except Exception as e:
        logger.error(f"Error registering handlers: {e}", exc_info=True)
        raise