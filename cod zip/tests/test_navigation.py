import pytest
from navigation_manager import NavigationManager

def test_navigation_manager_initialization():
    """Проверка инициализации менеджера навигации"""
    nav = NavigationManager()
    assert nav.menu_states is not None
    assert 'main_menu' in nav.menu_states

def test_get_menu_markup():
    """Проверка получения разметки меню"""
    nav = NavigationManager()
    keyboard, text = nav.get_menu_markup('main_menu')
    
    assert keyboard is not None
    assert text == "📋 Выберите действие:"
    assert isinstance(keyboard, list)
    assert len(keyboard) > 0

def test_add_to_history():
    """Проверка добавления состояния в историю"""
    nav = NavigationManager()
    user_data = {}
    
    nav.add_to_history(user_data, 'main_menu')
    assert 'navigation_history' in user_data
    assert user_data['navigation_history'] == ['main_menu']
    
    # Проверка ограничения истории
    for i in range(15):
        nav.add_to_history(user_data, f'state_{i}')
    assert len(user_data['navigation_history']) == 10

def test_get_previous_state():
    """Проверка получения предыдущего состояния"""
    nav = NavigationManager()
    user_data = {'navigation_history': ['main_menu', 'settings']}
    
    previous_state = nav.get_previous_state(user_data)
    assert previous_state == 'main_menu'

def test_clear_user_state():
    """Проверка очистки пользовательского состояния"""
    nav = NavigationManager()
    user_data = {
        'navigation_history': ['main_menu', 'settings'],
        'state': 'settings',
        'temp_data': 'some data'
    }
    
    nav.clear_user_state(user_data)
    assert 'navigation_history' in user_data
    assert 'state' in user_data
    assert 'temp_data' not in user_data
