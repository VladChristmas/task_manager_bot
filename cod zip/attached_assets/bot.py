import logging
import os
import asyncio
import nest_asyncio
from telegram.ext import Application
from handlers import register_handlers
from dotenv import load_dotenv
from database import Database

# Настройка логирования в файл и консоль
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database("bot_database.db")  # Явно указываем путь к файлу базы данных

class TelegramBot:
    """Основной класс бота"""

    def __init__(self):
        """Инициализация бота"""
        # Применяем nest_asyncio для поддержки вложенных циклов событий
        nest_asyncio.apply()

        # Загрузка переменных окружения
        load_dotenv()

        self.token = os.environ.get('BOT_TOKEN')
        if not self.token:
            raise ValueError("BOT_TOKEN не найден в переменных окружения")

        self.app = None
        self._running = False

    async def start(self):
        """Запуск бота"""
        try:
            # Инициализация приложения
            self.app = Application.builder().token(self.token).build()

            # Регистрация обработчиков из handlers.py
            register_handlers(self.app)

            # Запуск бота
            self._running = True
            logger.info("Запуск Telegram бота...")

            await self.app.run_polling(drop_pending_updates=True)

        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self):
        """Остановка бота"""
        try:
            if self.app and self._running:
                logger.info("Останавливаем бота...")
                await self.app.stop()
                self._running = False
                logger.info("Бот успешно остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}", exc_info=True)

if __name__ == "__main__":
    # Убедимся, что база данных инициализирована перед запуском бота
    try:
        db._ensure_database()
        logger.info("База данных успешно инициализирована")

        bot = TelegramBot()
        asyncio.run(bot.start())
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске приложения: {e}", exc_info=True)
        raise