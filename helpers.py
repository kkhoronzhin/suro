# -*- coding: utf-8 -*-
"""
Вспомогательные функции
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import hashlib
import json

def generate_ticket_id(length: int = 8) -> str:
    """
    Генерирует уникальный ID для обращения
    """
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

def format_number(number: int) -> str:
    """
    Форматирует число с разделителями
    """
    return f"{number:,}".replace(",", " ")

def format_phone(phone: str) -> str:
    """
    Форматирует номер телефона в читаемый вид
    """
    # Убираем все не-цифры
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return phone

def parse_phone(phone: str) -> str:
    """
    Приводит номер к стандартному виду +7XXXXXXXXXX
    """
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11 and digits.startswith('7'):
        return '+' + digits
    elif len(digits) == 11 and digits.startswith('8'):
        return '+7' + digits[1:]
    elif len(digits) == 10:
        return '+7' + digits
    
    return phone

def get_date_range(days: int = 30) -> tuple:
    """
    Возвращает диапазон дат (сегодня - days)
    """
    end = datetime.now()
    start = end - timedelta(days=days)
    return start, end

def split_list(lst: List, chunk_size: int) -> List[List]:
    """
    Разбивает список на части
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def dict_to_hash(data: Dict) -> str:
    """
    Создает хеш из словаря (для кэширования)
    """
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.md5(json_str.encode()).hexdigest()

def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы для Markdown
    """
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def truncate(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Обрезает текст до указанной длины
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def parse_command_args(text: str) -> List[str]:
    """
    Парсит аргументы команды
    """
    if not text:
        return []
    
    parts = text.strip().split()
    if len(parts) <= 1:
        return []
    
    return parts[1:]

def get_client_ip(request) -> str:
    """
    Получает IP клиента из Flask request
    """
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr

def time_ago(date: datetime) -> str:
    """
    Возвращает строку вида "5 минут назад"
    """
    now = datetime.now()
    diff = now - date
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "только что"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} мин. назад"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} ч. назад"
    elif seconds < 2592000:
        days = int(seconds // 86400)
        return f"{days} дн. назад"
    else:
        return date.strftime("%d.%m.%Y")