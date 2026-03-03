# -*- coding: utf-8 -*-
"""
Конфигурация приложения
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем .env
load_dotenv()

# Базовая директория
BASE_DIR = Path(__file__).parent.absolute()

# Токены бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env")

ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
ERROR_CHAT_ID = os.getenv('ERROR_CHAT_ID', ADMIN_CHAT_ID)

# Канал для проверки подписки
REQUIRED_CHANNEL = os.getenv('REQUIRED_CHANNEL', '@suro_shop')
REQUIRED_CHANNEL_ID = int(os.getenv('REQUIRED_CHANNEL_ID', '-1003854017888'))

# Пути к данным
DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'data' / 'database.db'))
MEDIA_PATH = os.getenv('MEDIA_PATH', str(BASE_DIR / 'data' / 'media'))

# Создаем папки
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(MEDIA_PATH, exist_ok=True)
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Google Sheets
GOOGLE_SHEETS_KEY = os.getenv('GOOGLE_SHEETS_KEY')
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')

# Веб-сервер
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
PUBLIC_URL = os.getenv('PUBLIC_URL', 'http://localhost:8080')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 8080))

# Настройки бота
MAX_APPLICATIONS_PER_DAY = 3  # Максимум заявок в день от одного пользователя
MESSAGE_TIMEOUT = 300  # Таймаут для FSM (5 минут)

# Настройки логов
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Версия
VERSION = '2.0.0'
VERSION_NAME = 'SURO Bot'