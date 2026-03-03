# -*- coding: utf-8 -*-
"""
Модель заявки
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import IntEnum

class ApplicationStatus(IntEnum):
    """Статусы заявки"""
    PENDING = 0   # Ожидает проверки
    APPROVED = 1  # Одобрено
    REJECTED = 2  # Отклонено
    
    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

@dataclass
class Application:
    """Модель заявки на кэшбэк"""
    
    id: Optional[int] = None
    user_id: int = 0
    type: str = 'unknown'  # 100, 150, 250, raffle
    amount: int = 0
    article: Optional[str] = None
    phone: Optional[str] = None
    review_date: Optional[str] = None
    review_photo_path: Optional[str] = None
    purchase_photo_path: Optional[str] = None
    publication_photo_path: Optional[str] = None
    status: ApplicationStatus = ApplicationStatus.PENDING
    paid_amount: int = 0
    admin_comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Дополнительные поля (не в БД)
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создает заявку из словаря"""
        status_value = data.get('status', 0)
        if isinstance(status_value, str):
            status_value = int(status_value)
        
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            type=data.get('type'),
            amount=data.get('amount', 0),
            article=data.get('article'),
            phone=data.get('phone'),
            review_date=data.get('review_date'),
            review_photo_path=data.get('review_photo_path'),
            purchase_photo_path=data.get('purchase_photo_path'),
            publication_photo_path=data.get('publication_photo_path'),
            status=ApplicationStatus(status_value),
            paid_amount=data.get('paid_amount', 0),
            admin_comment=data.get('admin_comment'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            username=data.get('username'),
            user_full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
        )
    
    def to_dict(self) -> dict:
        """Преобразует заявку в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'amount': self.amount,
            'article': self.article,
            'phone': self.phone,
            'review_date': self.review_date,
            'review_photo_path': self.review_photo_path,
            'purchase_photo_path': self.purchase_photo_path,
            'publication_photo_path': self.publication_photo_path,
            'status': self.status.value,
            'paid_amount': self.paid_amount,
            'admin_comment': self.admin_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def status_display(self) -> str:
        """Отображаемое название статуса"""
        return {
            ApplicationStatus.PENDING: "⏳ Ожидает",
            ApplicationStatus.APPROVED: "✅ Одобрено",
            ApplicationStatus.REJECTED: "❌ Отклонено"
        }.get(self.status, "Неизвестно")
    
    @property
    def status_color(self) -> str:
        """Цвет статуса для CSS"""
        return {
            ApplicationStatus.PENDING: "warning",
            ApplicationStatus.APPROVED: "success",
            ApplicationStatus.REJECTED: "danger"
        }.get(self.status, "muted")
    
    @property
    def review_photo_url(self) -> Optional[str]:
        """URL скриншота отзыва"""
        if self.review_photo_path:
            from config import PUBLIC_URL
            return f"{PUBLIC_URL}/media/{self.review_photo_path}"
        return None
    
    @property
    def purchase_photo_url(self) -> Optional[str]:
        """URL скриншота покупки"""
        if self.purchase_photo_path:
            from config import PUBLIC_URL
            return f"{PUBLIC_URL}/media/{self.purchase_photo_path}"
        return None
    
    @property
    def publication_photo_url(self) -> Optional[str]:
        """URL скриншота публикации"""
        if self.publication_photo_path:
            from config import PUBLIC_URL
            return f"{PUBLIC_URL}/media/{self.publication_photo_path}"
        return None