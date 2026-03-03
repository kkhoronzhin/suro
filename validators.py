# -*- coding: utf-8 -*-
"""
Валидаторы для различных типов данных
"""

import re
from datetime import datetime
from typing import Optional, Tuple

def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация российского номера телефона
    
    Returns:
        Tuple[bool, Optional[str]]: (валиден ли, нормализованный номер)
    """
    # Убираем все не-цифры
    digits = re.sub(r'\D', '', phone)
    
    # Проверяем длину
    if len(digits) == 11 and digits.startswith(('7', '8')):
        # Нормализуем в формат +7XXXXXXXXXX
        normalized = '+7' + digits[1:]
        return True, normalized
    
    elif len(digits) == 10 and digits.startswith('9'):
        # Добавляем +7
        normalized = '+7' + digits
        return True, normalized
    
    return False, None

def validate_article(article: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация артикула Wildberries
    """
    # Артикул должен содержать только цифры
    if article and article.isdigit():
        return True, article
    return False, None

def validate_date(date_str: str, format: str = "%d.%m.%Y") -> Tuple[bool, Optional[datetime]]:
    """
    Валидация даты
    """
    try:
        date = datetime.strptime(date_str.strip(), format)
        
        # Проверяем, что дата не в будущем
        if date <= datetime.now():
            return True, date
        
        return False, None
    except ValueError:
        return False, None

def validate_email(email: str) -> bool:
    """
    Валидация email
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """
    Валидация URL
    """
    pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w .-]*$'
    return bool(re.match(pattern, url))

def validate_amount(amount: str) -> Tuple[bool, Optional[int]]:
    """
    Валидация суммы (для выплат)
    """
    try:
        value = int(amount)
        if 0 < value <= 100000:  # Максимум 100к
            return True, value
    except ValueError:
        pass
    return False, None

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Очищает текст от потенциально опасных символов
    """
    # Удаляем управляющие символы
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length] + '...'
    
    return text

def is_russian_phone(phone: str) -> bool:
    """
    Проверяет, является ли номер российским
    """
    digits = re.sub(r'\D', '', phone)
    return len(digits) in [10, 11] and (digits.startswith('7') or digits.startswith('8') or digits.startswith('9'))

def extract_digits(text: str) -> str:
    """
    Извлекает только цифры из строки
    """
    return re.sub(r'\D', '', text)