import os
from datetime import datetime
from typing import Optional
import logging
from config import ALLOWED_REPORT_FORMATS, MAX_REPORT_SIZE

logger = logging.getLogger(__name__)

def setup_logging():
    """Настройка системы логирования"""
    # Создаем форматтер, который скрывает конфиденциальные данные
    class SensitiveFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None):
            super().__init__(fmt, datefmt)
            self.sensitive_keys = ['bot_token', 'api_key', 'password']

        def format(self, record):
            message = super().format(record)
            # Маскируем конфиденциальные данные в логах
            for key in self.sensitive_keys:
                if key in message.lower():
                    message = message.replace(getattr(record, 'msg', ''), '[СКРЫТО]')
            return message

    formatter = SensitiveFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

def is_valid_report_format(filename: str) -> bool:
    """Проверка допустимого формата файла отчета"""
    try:
        _, ext = os.path.splitext(filename.lower())
        return ext in ALLOWED_REPORT_FORMATS
    except Exception as e:
        logger.error(f"Ошибка при проверке формата файла: {e}")
        return False

def is_valid_file_size(file_size: int) -> bool:
    """Проверка размера файла на соответствие ограничениям"""
    try:
        return file_size <= MAX_REPORT_SIZE
    except Exception as e:
        logger.error(f"Ошибка при проверке размера файла: {e}")
        return False

def generate_report_id() -> str:
    """Генерация уникального идентификатора отчета"""
    try:
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    except Exception as e:
        logger.error(f"Ошибка при генерации ID отчета: {e}")
        return f"ERROR_{datetime.now().timestamp()}"

def format_report_info(report: dict) -> str:
    """Форматирование информации об отчете для отображения"""
    try:
        return (f"ID отчета: {report.get('report_id', 'Н/Д')}\n"
                f"Отправлен: {report.get('timestamp', 'Н/Д')}\n"
                f"Статус: {report.get('status', 'Неизвестно')}\n"
                f"Имя файла: {report.get('filename', 'Н/Д')}")
    except Exception as e:
        logger.error(f"Ошибка при форматировании информации отчета: {e}")
        return "Ошибка при получении информации об отчете"

def is_admin(user_id: int) -> bool:
    """Проверка является ли пользователь администратором"""
    try:
        admin_ids = os.environ.get('ADMIN_ID', '').split(',')
        return str(user_id) in admin_ids
    except Exception as e:
        logger.error(f"Ошибка при проверке прав администратора: {e}")
        return False