# -*- coding: utf-8 -*-
"""
Модель пользователя
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime

@dataclass
class User:
    """Модель пользователя Telegram"""
    
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = 'ru'
    is_admin: bool = False
    is_blocked: bool = False
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создает пользователя из словаря"""
        return cls(
            user_id=data.get('user_id'),
            username=data.get('username'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            language_code=data.get('language_code', 'ru'),
            is_admin=bool(data.get('is_admin', 0)),
            is_blocked=bool(data.get('is_blocked', 0)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            last_activity=datetime.fromisoformat(data['last_activity']) if data.get('last_activity') else None
        )
    
    def to_dict(self) -> dict:
        """Преобразует пользователя в словарь"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'language_code': self.language_code,
            'is_admin': int(self.is_admin),
            'is_blocked': int(self.is_blocked),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }
    
    @property
    def full_name(self) -> str:
        """Полное имя пользователя"""
        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)
        return ' '.join(parts) or "Unknown"
    
    @property
    def mention(self) -> str:
        """Упоминание пользователя в Telegram"""
        if self.username:
            return f"@{self.username}"
        return f"[{self.full_name}](tg://user?id={self.user_id})"
    
    @property
    def is_active(self) -> bool:
        """Проверяет, активен ли пользователь"""
        if not self.last_activity:
            return False
        
        # Считаем активным, если был активен в последние 30 дней
        delta = datetime.now() - self.last_activity
        return delta.days < 30