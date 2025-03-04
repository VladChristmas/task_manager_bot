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
        self._ensure_database()

    def _ensure_database(self):
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

    def get_active_tasks(self) -> Dict:
        """Получение активных заданий с дополнительной информацией"""
        try:
            tasks = {}
            conn = self.get_connection()
            cursor = conn.cursor()

            # Получаем основную информацию о заданиях
            cursor.execute("""
                SELECT t.id, t.text, t.created_at, t.status,
                       tr.chat_id, tr.status as recipient_status,
                       c.title as chat_title
                FROM tasks t
                JOIN task_recipients tr ON t.id = tr.task_id
                JOIN chats c ON tr.chat_id = c.chat_id
                WHERE t.status = 'active'
                ORDER BY t.created_at DESC
            """)

            task_rows = cursor.fetchall()

            for row in task_rows:
                task_id = row['id']
                if task_id not in tasks:
                    tasks[task_id] = {
                        'text': row['text'],
                        'created_at': row['created_at'],
                        'status': row['status'],
                        'recipients': {},
                        'media': []
                    }

                # Добавляем информацию о получателе
                chat_id = row['chat_id']
                tasks[task_id]['recipients'][chat_id] = {
                    'chat_title': row['chat_title'],
                    'status': row['recipient_status'],
                    'media': []
                }

            # Получаем медиафайлы заданий
            for task_id in tasks:
                cursor.execute("""
                    SELECT file_id, file_type
                    FROM task_media
                    WHERE task_id = ?
                """, (task_id,))

                media_files = cursor.fetchall()
                tasks[task_id]['media'] = [
                    {'file_id': m['file_id'], 'file_type': m['file_type']}
                    for m in media_files
                ]

                # Получаем медиафайлы ответов
                cursor.execute("""
                    SELECT chat_id, file_id, file_type
                    FROM response_media
                    WHERE task_id = ?
                """, (task_id,))

                response_media = cursor.fetchall()
                for media in response_media:
                    chat_id = media['chat_id']
                    if chat_id in tasks[task_id]['recipients']:
                        tasks[task_id]['recipients'][chat_id]['media'].append({
                            'file_id': media['file_id'],
                            'file_type': media['file_type']
                        })

            return tasks

        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении активных заданий: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_task(self, text: str, creator_id: int) -> int:
        """Создание нового задания"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO tasks (text, creator_id)
                VALUES (?, ?)
            """, (text, creator_id))

            task_id = cursor.lastrowid
            conn.commit()
            return task_id

        except sqlite3.Error as e:
            logger.error(f"Ошибка при создании задания: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def add_task_recipient(self, task_id: int, chat_id: int, group_id: Optional[int] = None):
        """Добавление получателя задания"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO task_recipients (task_id, chat_id, group_id)
                VALUES (?, ?, ?)
            """, (task_id, chat_id, group_id))

            conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении получателя задания: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_chat_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение списка групп чатов"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, created_at
                FROM chat_groups
                ORDER BY name
            """)

            return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении групп чатов: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_group_chats(self, group_id: int) -> List[Dict[str, Any]]:
        """Получение списка чатов в группе"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT c.chat_id, c.title
                FROM chats c
                JOIN group_chats gc ON c.chat_id = gc.chat_id
                WHERE gc.group_id = ?
                ORDER BY c.title
            """, (group_id,))

            return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении чатов группы: {e}")
            raise
        finally:
            if conn:
                conn.close()