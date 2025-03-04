import pytest
from utils import (
    is_valid_report_format,
    is_valid_file_size,
    generate_report_id,
    format_report_info,
    is_admin
)

def test_valid_report_format():
    """Проверка валидации формата отчета"""
    assert is_valid_report_format('report.pdf') is True
    assert is_valid_report_format('report.doc') is True
    assert is_valid_report_format('report.txt') is True
    assert is_valid_report_format('report.exe') is False
    assert is_valid_report_format('report') is False

def test_valid_file_size():
    """Проверка валидации размера файла"""
    max_size = 20 * 1024 * 1024  # 20MB
    assert is_valid_file_size(1024) is True
    assert is_valid_file_size(max_size) is True
    assert is_valid_file_size(max_size + 1) is False

def test_generate_report_id():
    """Проверка генерации ID отчета"""
    report_id = generate_report_id()
    assert isinstance(report_id, str)
    assert len(report_id) > 0

def test_format_report_info():
    """Проверка форматирования информации об отчете"""
    report = {
        'report_id': 'TEST001',
        'timestamp': '2024-02-26 12:00:00',
        'status': 'Принят',
        'filename': 'test_report.pdf'
    }
    
    formatted_info = format_report_info(report)
    assert 'TEST001' in formatted_info
    assert '2024-02-26' in formatted_info
    assert 'Принят' in formatted_info
    assert 'test_report.pdf' in formatted_info

def test_is_admin():
    """Проверка функции определения администратора"""
    import os
    with pytest.MonkeyPatch.context() as m:
        m.setenv('ADMIN_ID', '5171183387,123456')
        assert is_admin(5171183387) is True
        assert is_admin(123456) is True
        assert is_admin(999999) is False
