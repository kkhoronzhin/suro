# -*- coding: utf-8 -*-
"""
Модели для веб-интерфейса
"""

from flask_login import UserMixin
from datetime import datetime

class WebUser(UserMixin):
    """Модель пользователя для Flask-Login"""
    
    def __init__(self, user_id, username, is_admin=False, email=None):
        self.id = user_id
        self.username = username
        self.is_admin = is_admin
        self.email = email
        self.authenticated = True
        self.active = True
        self.anonymous = False
    
    @property
    def is_authenticated(self):
        return self.authenticated
    
    @property
    def is_active(self):
        return self.active
    
    @property
    def is_anonymous(self):
        return self.anonymous
    
    def get_id(self):
        return str(self.id)
    
    def to_dict(self):
        """Преобразует в словарь для API"""
        return {
            'id': self.id,
            'username': self.username,
            'is_admin': self.is_admin,
            'email': self.email
        }

class AdminUser:
    """Модель администратора из базы данных"""
    
    def __init__(self, id=None, username=None, password_hash=None, 
                 email=None, is_superadmin=False, created_at=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email
        self.is_superadmin = is_superadmin
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            username=data.get('username'),
            password_hash=data.get('password_hash'),
            email=data.get('email'),
            is_superadmin=bool(data.get('is_superadmin', 0)),
            created_at=data.get('created_at')
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_superadmin': self.is_superadmin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def check_password(self, password):
        """Проверяет пароль"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class DashboardStats:
    """Статистика для дашборда"""
    
    def __init__(self, data=None):
        self.data = data or {}
    
    @property
    def total_users(self):
        return self.data.get('total', {}).get('users', 0)
    
    @property
    def total_applications(self):
        return self.data.get('total', {}).get('applications', 0)
    
    @property
    def total_paid(self):
        return self.data.get('total', {}).get('paid', 0)
    
    @property
    def total_admins(self):
        return self.data.get('total', {}).get('admins', 0)
    
    @property
    def today_users(self):
        return self.data.get('today', {}).get('users', 0)
    
    @property
    def today_applications(self):
        return self.data.get('today', {}).get('applications', 0)
    
    @property
    def today_approved(self):
        return self.data.get('today', {}).get('approved', 0)
    
    @property
    def today_paid(self):
        return self.data.get('today', {}).get('paid', 0)
    
    @property
    def pending_applications(self):
        return self.data.get('pending', 0)
    
    def to_dict(self):
        return self.data