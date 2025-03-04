import os
import logging
import telebot
from dotenv import load_dotenv
from database import Database
import sys
import signal
import time
import requests
from requests.exceptions import RequestException
from threading import Lock
import atexit
import fcntl
import errno

# Создаем директорию для логов, если её нет
if not os.path.exists('logs'):
    os.makedirs('logs')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database("bot_database.db")  # Используем тот же путь, что и в bot.py

class TelegramBot:
    """Основной класс бота"""
    _instance = None
    _initialized = False
    _lock = Lock()
    _pid_file = 'bot.pid'
    _pid_fd = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelegramBot, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализация бота"""
        if self._initialized:
            return

        try:
            if not self._ensure_single_instance():
                raise RuntimeError("Another instance is already running")

            with self._lock:
                # Загрузка переменных окружения
                load_dotenv()
                logger.info("Loading environment variables...")

                # Получение токена
                self.token = os.getenv('BOT_TOKEN')
                if not self.token:
                    logger.error("BOT_TOKEN not found in environment variables")
                    raise ValueError("BOT_TOKEN не найден в переменных окружения")
                logger.info("BOT_TOKEN successfully loaded")

                # Очистка старых соединений
                self._clear_webhook()
                self._clear_pending_updates()

                # Инициализация бота с таймаутом и параметрами
                self.bot = telebot.TeleBot(
                    self.token,
                    parse_mode='HTML',
                    threaded=True,
                    num_threads=1  # Один поток для избежания конфликтов
                )

                # Устанавливаем параметры запросов к API
                telebot.apihelper.RETRY_ON_ERROR = True
                telebot.apihelper.CONNECT_TIMEOUT = 3.5
                telebot.apihelper.READ_TIMEOUT = 10

                self._setup_handlers()
                self._initialized = True
                logger.info("Bot initialized successfully")

                # Настройка обработчика сигналов для корректного завершения
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)

                # Регистрация очистки при выходе
                atexit.register(self._cleanup)

        except Exception as e:
            logger.error(f"Error during initialization: {e}", exc_info=True)
            self._cleanup()
            raise

    def _ensure_single_instance(self):
        """Проверка, что запущен только один экземпляр бота"""
        try:
            logger.info(f"Checking for existing bot instance (PID: {os.getpid()})")
            self._pid_fd = os.open(self._pid_file, os.O_CREAT | os.O_RDWR)
            fcntl.flock(self._pid_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.write(self._pid_fd, str(os.getpid()).encode())
            logger.info(f"Successfully acquired lock for PID {os.getpid()}")
            return True
        except (IOError, OSError) as e:
            if e.errno == errno.EACCES or e.errno == errno.EAGAIN:
                logger.warning("Another instance is already running")
                if self._pid_fd:
                    os.close(self._pid_fd)
                return False
            raise

    def _cleanup(self):
        """Очистка ресурсов при завершении"""
        try:
            if self._pid_fd is not None:
                logger.info(f"Cleaning up resources for PID {os.getpid()}")
                fcntl.flock(self._pid_fd, fcntl.LOCK_UN)
                os.close(self._pid_fd)
                try:
                    os.unlink(self._pid_file)
                except OSError as e:
                    if e.errno != errno.ENOENT:  # Игнорируем ошибку если файл уже удален
                        raise
                logger.info("Process lock released and PID file removed")
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _clear_webhook(self):
        """Очистка webhook'а перед запуском polling"""
        try:
            api_url = f"https://api.telegram.org/bot{self.token}/deleteWebhook"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                logger.info("Successfully cleared webhook")
            else:
                logger.warning(f"Failed to clear webhook: {response.text}")
        except RequestException as e:
            logger.warning(f"Error clearing webhook: {e}")

    def _clear_pending_updates(self):
        """Очистка очереди обновлений перед запуском"""
        try:
            api_url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            params = {'offset': -1, 'limit': 1, 'timeout': 1}
            response = requests.get(api_url, params=params, timeout=5)
            if response.status_code == 200:
                logger.info("Successfully cleared pending updates")
            else:
                logger.warning(f"Failed to clear updates: {response.text}")
        except RequestException as e:
            logger.warning(f"Error clearing updates: {e}")

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения работы"""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)

    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        try:
            logger.info("Setting up command handlers...")

            @self.bot.message_handler(commands=['start'])
            def start_command(message):
                try:
                    logger.info(f"Received /start command from user {message.from_user.id}")
                    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.row(
                        telebot.types.KeyboardButton("📝 Создать новое задание"),
                        telebot.types.KeyboardButton("📋 Просмотр активных заданий")
                    )
                    markup.row(
                        telebot.types.KeyboardButton("👥 Просмотр списка подключенных чатов"),
                        telebot.types.KeyboardButton("👥 Создать группу чатов")
                    )
                    markup.row(
                        telebot.types.KeyboardButton("⚙️ Настройки"),
                        telebot.types.KeyboardButton("❓ Помощь")
                    )
                    self.bot.reply_to(message, "Главное меню:", reply_markup=markup)
                    logger.info("Main menu displayed successfully")
                except Exception as e:
                    logger.error(f"Error in start command: {e}", exc_info=True)
                    self.bot.reply_to(message, "Произошла ошибка. Пожалуйста, попробуйте позже.")

            @self.bot.message_handler(commands=['help'])
            def help_command(message):
                try:
                    from constants import HELP_TEXT
                    logger.info(f"Received /help command from user {message.from_user.id}")
                    self.bot.reply_to(message, HELP_TEXT)
                    logger.info("Help message sent successfully")
                except Exception as e:
                    logger.error(f"Error in help command: {e}", exc_info=True)
                    self.bot.reply_to(message, "Произошла ошибка. Пожалуйста, попробуйте позже.")

            @self.bot.message_handler(commands=['addchat'])
            def add_chat_command(message):
                try:
                    logger.info(f"Received /addchat command in chat {message.chat.id}")
                    chat_id = message.chat.id
                    chat_title = message.chat.title or f"Личный чат с {message.from_user.first_name}"
                    is_group = message.chat.type in ['group', 'supergroup']

                    # Проверка существующего чата
                    existing_chat = db.execute_query("SELECT chat_id FROM chats WHERE chat_id = ?", (chat_id,))
                    if existing_chat:
                        self.bot.reply_to(message, "Этот чат уже подключен к боту.")
                        return

                    # Добавление нового чата
                    db.execute_query(
                        "INSERT INTO chats (chat_id, title, is_group) VALUES (?, ?, ?)",
                        (chat_id, chat_title, is_group)
                    )
                    self.bot.reply_to(message, "Чат успешно подключен к боту!")
                    logger.info(f"Chat {chat_id} successfully added")

                except Exception as e:
                    logger.error(f"Error in add chat command: {e}", exc_info=True)
                    self.bot.reply_to(message, "Произошла ошибка. Пожалуйста, попробуйте позже.")

            @self.bot.message_handler(func=lambda message: True)
            def handle_text(message):
                try:
                    logger.info(f"Received message from user {message.from_user.id}: {message.text}")
                    if message.text == "❓ Помощь":
                        help_command(message)
                    elif message.text == "📝 Создать новое задание":
                        self.bot.reply_to(message, "Функция создания задания в разработке")
                    elif message.text == "📋 Просмотр активных заданий":
                        self.bot.reply_to(message, "Функция просмотра заданий в разработке")
                    else:
                        self.bot.reply_to(message, "Команда не распознана")
                except Exception as e:
                    logger.error(f"Error handling message: {e}", exc_info=True)
                    self.bot.reply_to(message, "Произошла ошибка. Пожалуйста, попробуйте позже.")

            logger.info("All handlers registered successfully")

        except Exception as e:
            logger.error(f"Error setting up handlers: {e}", exc_info=True)
            raise

    def start(self):
        """Запуск бота"""
        try:
            with self._lock:
                logger.info("Starting Telegram bot...")
                self.bot.infinity_polling(
                    skip_pending=True,
                    timeout=10,
                    long_polling_timeout=5,
                    allowed_updates=["message"],
                    restart_on_change=True
                )
        except Exception as e:
            logger.error(f"Error starting bot: {e}", exc_info=True)
            self.stop()
            raise

    def stop(self):
        """Остановка бота"""
        try:
            if self.bot:
                logger.info("Stopping bot...")
                self.bot.stop_polling()
                time.sleep(1)  # Даем время на завершение всех процессов
                logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        # Инициализация базы данных
        db.ensure_database()
        logger.info("Database initialized successfully")

        # Запуск бота
        bot = TelegramBot()
        bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        if 'bot' in locals():
            bot.stop()
    except Exception as e:
        logger.error(f"Critical error during application startup: {e}", exc_info=True)
        raise