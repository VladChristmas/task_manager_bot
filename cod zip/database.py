"""
Модуль для работы с базой данных SQLite
"""
import sqlite3
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "bot_database.db"):
        """Инициализация базы данных"""
        self.db_path = db_path
        self.ensure_database()

    def ensure_database(self):
        """Создание базы данных и необходимых таблиц"""
        try:
            # Проверяем наличие директории для базы данных
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            conn = self.get_connection()
            cursor = conn.cursor()

            # Создание таблицы чатов с явным указанием DEFAULT для added_at
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    is_group BOOLEAN NOT NULL,
                    added_at TIMESTAMP DEFAULT (datetime('now'))
                )
            """)

            # Создание таблицы групп чатов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT (datetime('now'))
                )
            """)

            # Создание таблицы связей групп и чатов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_chats (
                    group_id INTEGER,
                    chat_id INTEGER,
                    FOREIGN KEY (group_id) REFERENCES chat_groups (id),
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                    PRIMARY KEY (group_id, chat_id)
                )
            """)

            # Создание таблицы заданий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    creator_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT (datetime('now'))
                )
            """)

            # Создание таблицы получателей заданий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_recipients (
                    task_id INTEGER,
                    chat_id INTEGER,
                    group_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (task_id) REFERENCES tasks (id),
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
                    FOREIGN KEY (group_id) REFERENCES chat_groups (id),
                    PRIMARY KEY (task_id, chat_id)
                )
            """)

            # Создание таблицы медиафайлов задания
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    file_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)

            # Создание таблицы медиафайлов ответов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    chat_id INTEGER,
                    file_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT (datetime('now')),
                    FOREIGN KEY (task_id) REFERENCES tasks (id),
                    FOREIGN KEY (chat_id) REFERENCES chats (chat_id)
                )
            """)

            conn.commit()
            logger.info("База данных успешно инициализирована")

        except sqlite3.Error as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}", exc_info=True)
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """Получение соединения с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Выполнение SQL запроса"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Логируем запрос до выполнения
            logger.info(f"Выполняется SQL запрос: {query}")
            if params:
                logger.info(f"Параметры запроса: {params}")

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
                logger.info("Запрос успешно выполнен (INSERT/UPDATE/DELETE)")
                return []

            result = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Получено результатов: {len(result)}")
            return result

        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}\nЗапрос: {query}\nПараметры: {params}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()