#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для миграции старой базы данных в новую структуру
Запускать: python scripts/migrate_db.py
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

# Добавляем родительскую папку в путь
sys.path.append(str(Path(__file__).parent.parent))

from config import DATABASE_PATH

def backup_db(db_path):
    """Создает бэкап существующей БД"""
    if os.path.exists(db_path):
        backup_path = db_path + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(db_path, backup_path)
        print(f"✅ Создан бэкап: {backup_path}")
        return backup_path
    return None

def migrate_users(old_conn, new_conn):
    """Миграция таблицы пользователей"""
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    # Проверяем, есть ли старая таблица
    old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not old_cursor.fetchone():
        print("⚠️ Таблица users не найдена в старой БД, пропускаем")
        return 0
    
    # Получаем данные из старой таблицы
    old_cursor.execute("SELECT * FROM users")
    old_users = old_cursor.fetchall()
    
    # Получаем названия колонок
    old_cursor.execute("PRAGMA table_info(users)")
    old_columns = [col[1] for col in old_cursor.fetchall()]
    
    migrated = 0
    for user in old_users:
        user_dict = dict(zip(old_columns, user))
        
        # Преобразуем в новую структуру
        new_cursor.execute('''
            INSERT OR IGNORE INTO users 
            (id, user_id, username, first_name, last_name, language_code, 
             is_admin, is_blocked, created_at, last_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_dict.get('id'),
            user_dict.get('user_id') or user_dict.get('telegram_id'),
            user_dict.get('username'),
            user_dict.get('name') or user_dict.get('first_name'),
            user_dict.get('lastname') or user_dict.get('last_name'),
            user_dict.get('language_code', 'ru'),
            1 if user_dict.get('admin', 0) > 0 else 0,
            0,
            user_dict.get('created_at', datetime.now().isoformat()),
            user_dict.get('last_activity', datetime.now().isoformat())
        ))
        migrated += 1
    
    new_conn.commit()
    print(f"✅ Перенесено пользователей: {migrated}")
    return migrated

def migrate_applications(old_conn, new_conn):
    """Миграция таблицы заявок"""
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    # Ищем старые таблицы с заявками
    old_tables = ['raffle', 'raffles', 'roulette', 'reward']
    total_migrated = 0
    
    for table in old_tables:
        old_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not old_cursor.fetchone():
            print(f"⚠️ Таблица {table} не найдена, пропускаем")
            continue
        
        # Определяем тип заявки
        app_type = {
            'raffle': '150',
            'raffles': '100',
            'roulette': '250',
            'reward': '5000'
        }.get(table, 'unknown')
        
        # Получаем данные
        old_cursor.execute(f"SELECT * FROM {table}")
        apps = old_cursor.fetchall()
        
        # Получаем названия колонок
        old_cursor.execute(f"PRAGMA table_info({table})")
        old_columns = [col[1] for col in old_cursor.fetchall()]
        
        migrated = 0
        for app in apps:
            app_dict = dict(zip(old_columns, app))
            
            new_cursor.execute('''
                INSERT INTO applications 
                (user_id, type, article, phone, review_date, 
                 review_photo_path, purchase_photo_path, status, paid_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                app_dict.get('user_id'),
                app_type,
                app_dict.get('artikul'),
                app_dict.get('phone'),
                app_dict.get('review_date'),
                app_dict.get('photo1') or app_dict.get('review_photo'),
                app_dict.get('photo2') or app_dict.get('purchase_photo'),
                app_dict.get('status', 0),
                0,
                app_dict.get('created_at', datetime.now().isoformat())
            ))
            migrated += 1
        
        new_conn.commit()
        print(f"✅ Перенесено заявок из {table} ({app_type}₽): {migrated}")
        total_migrated += migrated
    
    return total_migrated

def main():
    """Главная функция миграции"""
    
    print("=" * 50)
    print("Миграция базы данных SURO Bot")
    print("=" * 50)
    
    # Ищем старую БД
    old_db_path = None
    possible_paths = [
        "data.db",
        "database.db",
        "../data.db",
        "../database.db",
        "/root/bot/data.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            old_db_path = path
            break
    
    if not old_db_path:
        print("❌ Старая база данных не найдена!")
        return
    
    print(f"📁 Найдена старая БД: {old_db_path}")
    
    # Бэкап старой и создание новой
    if os.path.exists(DATABASE_PATH):
        backup_db(DATABASE_PATH)
    
    # Подключаемся к старой БД
    old_conn = sqlite3.connect(old_db_path)
    old_conn.row_factory = sqlite3.Row
    
    # Создаем новую БД
    from bot.services.database import Database
    db = Database()
    
    # Миграция
    print("\n📊 Миграция пользователей...")
    users_migrated = migrate_users(old_conn, db._get_connection())
    
    print("\n📝 Миграция заявок...")
    apps_migrated = migrate_applications(old_conn, db._get_connection())
    
    old_conn.close()
    
    print("\n" + "=" * 50)
    print("✅ Миграция завершена!")
    print(f"👥 Перенесено пользователей: {users_migrated}")
    print(f"📄 Перенесено заявок: {apps_migrated}")
    print("=" * 50)

if __name__ == "__main__":
    main()