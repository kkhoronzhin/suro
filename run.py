#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SURO Bot - Точка входа
Запускает бота и веб-сервер одновременно
"""

import asyncio
import threading
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            os.path.join(log_dir, 'bot.log'),
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_bot():
    """Запуск Telegram бота"""
    try:
        from bot.main import main as bot_main
        logger.info("Запуск Telegram бота...")
        asyncio.run(bot_main())
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)

def run_web():
    """Запуск Flask веб-сервера"""
    try:
        from web.app import app
        logger.info("Запуск веб-сервера...")
        
        host = os.getenv('FLASK_HOST', '0.0.0.0')
        port = int(os.getenv('FLASK_PORT', 8080))
        
        app.run(host=host, port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске веб-сервера: {e}", exc_info=True)

def main():
    """Главная функция"""
    logger.info("=" * 50)
    logger.info("SURO Bot - Запуск")
    logger.info("=" * 50)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем веб-сервер в основном потоке
    run_web()

if __name__ == "__main__":
    main()