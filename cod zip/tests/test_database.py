import pytest
from database import Database

def test_database_initialization(temp_db):
    """Проверка инициализации базы данных"""
    assert temp_db is not None

def test_add_chat(temp_db):
    """Проверка добавления чата"""
    chat_id = 123456789
    title = "Test Chat"
    is_group = False
    
    temp_db.add_chat(chat_id, title, is_group)
    chat = temp_db.get_chat(chat_id)
    
    assert chat is not None
    assert chat['chat_id'] == chat_id
    assert chat['title'] == title
    assert chat['is_group'] == is_group

def test_create_chat_group(temp_db):
    """Проверка создания группы чатов"""
    group_name = "Test Group"
    chat_ids = [123456789, 987654321]
    
    # Сначала добавляем чаты
    for chat_id in chat_ids:
        temp_db.add_chat(chat_id, f"Chat {chat_id}", False)
    
    group_id = temp_db.create_chat_group(group_name, chat_ids)
    assert group_id is not None
    
    group = temp_db.get_chat_group(group_id)
    assert group['name'] == group_name
    
    group_chats = temp_db.get_group_chats(group_id)
    assert len(group_chats) == len(chat_ids)
    assert all(chat['chat_id'] in chat_ids for chat in group_chats)

def test_add_task(temp_db):
    """Проверка добавления задания"""
    task_text = "Test Task"
    chat_ids = [123456789]
    
    # Добавляем чат
    temp_db.add_chat(chat_ids[0], "Test Chat", False)
    
    task_id = temp_db.add_task(task_text, chat_ids)
    assert task_id is not None
    
    task = temp_db.get_task(task_id)
    assert task['text'] == task_text
    
    task_chats = temp_db.get_task_chats(task_id)
    assert len(task_chats) == len(chat_ids)
    assert task_chats[0]['chat_id'] == chat_ids[0]
