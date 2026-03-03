# -*- coding: utf-8 -*-
"""
Асинхронная работа с SQLite базой данных
"""

import sqlite3
import json
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging

from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных (асинхронный)"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализация таблиц (синхронно)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_blocked INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Индексы для users
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)')
            
            # Таблица заявок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount INTEGER DEFAULT 0,
                    article TEXT,
                    phone TEXT,
                    review_date TEXT,
                    review_photo_path TEXT,
                    purchase_photo_path TEXT,
                    publication_photo_path TEXT,
                    status INTEGER DEFAULT 0,
                    paid_amount INTEGER DEFAULT 0,
                    admin_comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Индексы для applications
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_user_id ON applications(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_status ON applications(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_type ON applications(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_apps_created_at ON applications(created_at)')
            
            # Таблица обращений в поддержку
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ticket_id TEXT UNIQUE NOT NULL,
                    message TEXT,
                    status TEXT DEFAULT 'open',
                    admin_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица ответов поддержки
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_replies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message TEXT,
                    is_admin INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES support_requests(id)
                )
            ''')
            
            # Таблица логов действий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    ip TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Индекс для логов
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_user_id ON activity_logs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_created_at ON activity_logs(created_at)')
            
            # Таблица статистики по дням
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    new_users INTEGER DEFAULT 0,
                    applications INTEGER DEFAULT 0,
                    approved_applications INTEGER DEFAULT 0,
                    paid_amount INTEGER DEFAULT 0,
                    support_requests INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            
            logger.info("База данных инициализирована")
    
    @asynccontextmanager
    async def get_connection(self):
        """Асинхронный контекстный менеджер для соединения с БД"""
        loop = asyncio.get_event_loop()
        conn = await loop.run_in_executor(None, sqlite3.connect, self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            await loop.run_in_executor(None, conn.close)
    
    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    
    async def save_user(self, user_data: Dict[str, Any]) -> bool:
        """Сохраняет или обновляет пользователя"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users 
                    (user_id, username, first_name, last_name, language_code, last_activity)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        username = excluded.username,
                        first_name = excluded.first_name,
                        last_name = excluded.last_name,
                        language_code = excluded.language_code,
                        last_activity = CURRENT_TIMESTAMP,
                        is_blocked = 0
                ''', (
                    user_data['user_id'],
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('language_code')
                ))
                
                conn.commit()
                
                # Проверяем, новый ли пользователь
                cursor.execute('''
                    SELECT DATE(created_at) = DATE('now') as is_new 
                    FROM users WHERE user_id = ?
                ''', (user_data['user_id'],))
                row = cursor.fetchone()
                
                if row and row['is_new']:
                    await self._update_daily_stats('new_users', 1)
                
                return True
                
            except Exception as e:
                logger.error(f"Ошибка сохранения пользователя: {e}")
                return False
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получает информацию о пользователе"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def get_user_by_id(self, db_id: int) -> Optional[Dict]:
        """Получает пользователя по внутреннему ID"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (db_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def get_all_users(self, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Получает список всех пользователей"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_users_filtered(self, page: int = 1, per_page: int = 50, 
                                 search: str = None) -> List[Dict]:
        """Получает пользователей с фильтрацией и пагинацией"""
        offset = (page - 1) * per_page
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if search:
                cursor.execute('''
                    SELECT * FROM users 
                    WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ? 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                ''', (f'%{search}%', f'%{search}%', f'%{search}%', per_page, offset))
            else:
                cursor.execute('''
                    SELECT * FROM users 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                ''', (per_page, offset))
            
            users = [dict(row) for row in cursor.fetchall()]
            
            # Добавляем статистику для каждого пользователя
            for user in users:
                apps = await self.get_user_applications(user['user_id'])
                user['applications_count'] = len(apps)
                user['total_paid'] = sum(a.get('paid_amount', 0) for a in apps)
            
            return users
    
    async def count_users(self, search: str = None) -> int:
        """Считает общее количество пользователей"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if search:
                cursor.execute('''
                    SELECT COUNT(*) as count FROM users 
                    WHERE user_id LIKE ? OR username LIKE ? OR first_name LIKE ?
                ''', (f'%{search}%', f'%{search}%', f'%{search}%'))
            else:
                cursor.execute('SELECT COUNT(*) as count FROM users')
            
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    async def get_admins(self) -> List[int]:
        """Получает список ID администраторов"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE is_admin = 1')
            return [row['user_id'] for row in cursor.fetchall()]
    
    async def add_admin(self, user_id: int) -> bool:
        """Добавляет администратора"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    async def remove_admin(self, user_id: int) -> bool:
        """Удаляет администратора"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_admin = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    async def block_user(self, user_id: int) -> bool:
        """Блокирует пользователя"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    async def unblock_user(self, user_id: int) -> bool:
        """Разблокирует пользователя"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    async def get_user_applications(self, user_id: int) -> List[Dict]:
        """Получает все заявки пользователя"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM applications 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_user_applications_today(self, user_id: int) -> int:
        """Считает количество заявок пользователя за сегодня"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as count FROM applications 
                WHERE user_id = ? AND DATE(created_at) = DATE('now')
            ''', (user_id,))
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    async def user_exists(self, user_id: int) -> bool:
        """Проверяет существование пользователя"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone() is not None
    
    async def is_new_user(self, user_id: int) -> bool:
        """Проверяет, новый ли пользователь (сегодня)"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DATE(created_at) = DATE('now') as is_new 
                FROM users WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            return row and row['is_new'] == 1
    
    async def get_all_user_ids(self) -> List[int]:
        """Получает список всех ID пользователей (не заблокированных)"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users WHERE is_blocked = 0')
            return [row['user_id'] for row in cursor.fetchall()]
    
    async def mark_user_blocked(self, user_id: int):
        """Отмечает пользователя как заблокировавшего бота"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
            conn.commit()
    
    # ==================== ЗАЯВКИ ====================
    
    async def save_application(self, app_data: Dict[str, Any]) -> int:
        """Сохраняет заявку"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO applications 
                (user_id, type, amount, article, phone, review_date, 
                 review_photo_path, purchase_photo_path, publication_photo_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                app_data['user_id'],
                app_data.get('type', 'unknown'),
                app_data.get('amount', 0),
                app_data.get('article'),
                app_data.get('phone'),
                app_data.get('review_date'),
                app_data.get('review_photo'),
                app_data.get('purchase_photo'),
                app_data.get('publication_photo'),
                app_data.get('status', 0)
            ))
            
            app_id = cursor.lastrowid
            conn.commit()
            
            # Обновляем статистику
            await self._update_daily_stats('applications', 1)
            
            logger.info(f"Заявка {app_id} сохранена")
            return app_id
    
    async def get_application(self, app_id: int) -> Optional[Dict]:
        """Получает заявку по ID"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.username, u.first_name, u.last_name 
                FROM applications a
                JOIN users u ON a.user_id = u.user_id
                WHERE a.id = ?
            ''', (app_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def get_applications_filtered(self, page: int = 1, per_page: int = 50,
                                        status: int = None, type: str = None,
                                        user_id: int = None, search: str = None) -> List[Dict]:
        """Получает заявки с фильтрацией"""
        offset = (page - 1) * per_page
        
        query = '''
            SELECT a.*, u.username, u.first_name, u.last_name 
            FROM applications a
            JOIN users u ON a.user_id = u.user_id
            WHERE 1=1
        '''
        params = []
        
        if status is not None:
            query += ' AND a.status = ?'
            params.append(status)
        
        if type:
            query += ' AND a.type = ?'
            params.append(type)
        
        if user_id:
            query += ' AND a.user_id = ?'
            params.append(user_id)
        
        if search:
            query += ''' AND (a.article LIKE ? OR a.phone LIKE ? OR u.username LIKE ?)'''
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        query += ' ORDER BY a.created_at DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    async def count_applications_filtered(self, status: int = None, type: str = None,
                                         user_id: int = None, search: str = None) -> int:
        """Считает количество заявок с фильтром"""
        query = '''
            SELECT COUNT(*) as count 
            FROM applications a
            JOIN users u ON a.user_id = u.user_id
            WHERE 1=1
        '''
        params = []
        
        if status is not None:
            query += ' AND a.status = ?'
            params.append(status)
        
        if type:
            query += ' AND a.type = ?'
            params.append(type)
        
        if user_id:
            query += ' AND a.user_id = ?'
            params.append(user_id)
        
        if search:
            query += ''' AND (a.article LIKE ? OR a.phone LIKE ? OR u.username LIKE ?)'''
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    async def update_application_status(self, app_id: int, status: int, 
                                       paid_amount: int = 0, comment: str = None):
        """Обновляет статус заявки"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if paid_amount > 0:
                cursor.execute('''
                    UPDATE applications 
                    SET status = ?, paid_amount = ?, admin_comment = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, paid_amount, comment, app_id))
                
                # Обновляем статистику выплат
                if status == 1:  # Одобрено
                    await self._update_daily_stats('approved_applications', 1)
                    await self._update_daily_stats('paid_amount', paid_amount)
            else:
                cursor.execute('''
                    UPDATE applications 
                    SET status = ?, admin_comment = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, comment, app_id))
            
            conn.commit()
            logger.info(f"Статус заявки {app_id} обновлен на {status}")
    
    async def get_applications_by_type(self) -> List[Dict]:
        """Получает статистику по типам заявок"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    type,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as approved,
                    SUM(paid_amount) as total_paid
                FROM applications
                GROUP BY type
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== ПОДДЕРЖКА ====================
    
    async def save_support_request(self, user_id: int, ticket_id: str, message: str) -> int:
        """Сохраняет обращение в поддержку"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO support_requests (user_id, ticket_id, message)
                VALUES (?, ?, ?)
            ''', (user_id, ticket_id, message))
            
            request_id = cursor.lastrowid
            conn.commit()
            
            await self._update_daily_stats('support_requests', 1)
            
            return request_id
    
    async def get_support_requests_filtered(self, page: int = 1, per_page: int = 50,
                                           status: str = None) -> List[Dict]:
        """Получает обращения с фильтрацией"""
        offset = (page - 1) * per_page
        
        query = '''
            SELECT sr.*, u.username, u.first_name, u.last_name 
            FROM support_requests sr
            JOIN users u ON sr.user_id = u.user_id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND sr.status = ?'
            params.append(status)
        
        query += ' ORDER BY sr.created_at DESC LIMIT ? OFFSET ?'
        params.extend([per_page, offset])
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    async def count_support_requests(self, status: str = None) -> int:
        """Считает количество обращений"""
        query = 'SELECT COUNT(*) as count FROM support_requests'
        params = []
        
        if status:
            query += ' WHERE status = ?'
            params.append(status)
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    async def get_support_request(self, request_id: int) -> Optional[Dict]:
        """Получает обращение по ID"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sr.*, u.username, u.first_name, u.last_name 
                FROM support_requests sr
                JOIN users u ON sr.user_id = u.user_id
                WHERE sr.id = ?
            ''', (request_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def close_support_request(self, request_id: int, admin_id: int):
        """Закрывает обращение"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE support_requests 
                SET status = 'closed', admin_id = ?, closed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (admin_id, request_id))
            conn.commit()
    
    async def add_support_reply(self, request_id: int, user_id: int, 
                                message: str, is_admin: bool = False):
        """Добавляет ответ в обращение"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO support_replies (request_id, user_id, message, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (request_id, user_id, message, 1 if is_admin else 0))
            conn.commit()
    
    async def get_support_replies(self, request_id: int) -> List[Dict]:
        """Получает все ответы по обращению"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sr.*, u.username 
                FROM support_replies sr
                JOIN users u ON sr.user_id = u.user_id
                WHERE sr.request_id = ?
                ORDER BY sr.created_at ASC
            ''', (request_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== ЛОГИ ====================
    
    async def log_activity(self, user_id: int, action: str, details: Dict = None, ip: str = None):
        """Логирует действие пользователя"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activity_logs (user_id, action, details, ip)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action, json.dumps(details, ensure_ascii=False) if details else None, ip))
            conn.commit()
    
    async def get_recent_activity(self, limit: int = 50) -> List[Dict]:
        """Получает последние действия"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT al.*, u.username 
                FROM activity_logs al
                JOIN users u ON al.user_id = u.user_id
                ORDER BY al.created_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== СТАТИСТИКА ====================
    
    async def _update_daily_stats(self, field: str, value: int = 1):
        """Обновляет дневную статистику"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, есть ли запись за сегодня
            cursor.execute('SELECT id FROM daily_stats WHERE date = ?', (today,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute(f'''
                    UPDATE daily_stats 
                    SET {field} = {field} + ?, updated_at = CURRENT_TIMESTAMP
                    WHERE date = ?
                ''', (value, today))
            else:
                cursor.execute(f'''
                    INSERT INTO daily_stats (date, {field})
                    VALUES (?, ?)
                ''', (today, value))
            
            conn.commit()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получает общую статистику"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Всего пользователей
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            # Всего заявок
            cursor.execute('SELECT COUNT(*) as count FROM applications')
            total_applications = cursor.fetchone()['count']
            
            # Всего выплачено
            cursor.execute('SELECT SUM(paid_amount) as total FROM applications WHERE status = 1')
            total_paid = cursor.fetchone()['total'] or 0
            
            # Всего админов
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = 1')
            total_admins = cursor.fetchone()['count']
            
            # За сегодня
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE DATE(created_at) = ?) as today_users,
                    (SELECT COUNT(*) FROM applications WHERE DATE(created_at) = ?) as today_apps,
                    (SELECT COUNT(*) FROM applications WHERE DATE(created_at) = ? AND status = 1) as today_approved,
                    (SELECT IFNULL(SUM(paid_amount), 0) FROM applications WHERE DATE(created_at) = ? AND status = 1) as today_paid
            ''', (today, today, today, today))
            
            today_row = cursor.fetchone()
            
            # Статистика по типам
            by_type = await self.get_applications_by_type()
            
            # Ожидающие проверки
            cursor.execute('SELECT COUNT(*) as count FROM applications WHERE status = 0')
            pending = cursor.fetchone()['count']
            
            return {
                'total': {
                    'users': total_users,
                    'applications': total_applications,
                    'paid': total_paid,
                    'admins': total_admins
                },
                'today': {
                    'users': today_row['today_users'] if today_row else 0,
                    'applications': today_row['today_apps'] if today_row else 0,
                    'approved': today_row['today_approved'] if today_row else 0,
                    'paid': today_row['today_paid'] if today_row else 0
                },
                'by_type': by_type,
                'pending': pending
            }
    
    async def get_daily_stats(self, days: int = 30) -> List[Dict]:
        """Получает статистику по дням"""
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM daily_stats 
                WHERE date >= DATE('now', ?)
                ORDER BY date DESC
            ''', (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]

# Глобальный экземпляр для удобства
db = Database()