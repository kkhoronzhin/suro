# -*- coding: utf-8 -*-
"""
Главный файл бота - инициализация и регистрация всех обработчиков
"""

import logging
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler

from bot.instance import application
from bot.middlewares.subscription import setup_subscription_middleware
from bot.services.logger import bot_logger
from bot.services.database import Database
from bot.handlers import (
    admin, support,
    cashback_100, cashback_150, cashback_250, raffle_5000
)

# Настройка логирования
logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска бота"""
    
    try:
        # Инициализируем базу данных
        db = Database()
        await db.init()
        application.bot_data['db'] = db
        
        # Загружаем список админов
        admins = await db.get_admins()
        application.bot_data['admins'] = set(admins)
        bot_logger.info(f"Загружено {len(admins)} администраторов")
        
        # Регистрируем middleware для проверки подписки
        setup_subscription_middleware(application)
        
        # Регистрируем все обработчики
        register_handlers()
        
        # Запускаем бота
        await application.initialize()
        await application.start()
        await application.updater.start_polling(
            allowed_updates=['message', 'callback_query', 'chat_member']
        )
        
        bot_logger.info("✅ Бот успешно запущен!")
        
        # Держим бота запущенным
        while True:
            await asyncio.sleep(3600)  # Спим час
            
    except Exception as e:
        bot_logger.error(f"❌ Критическая ошибка при запуске бота: {e}", exc_info=True)
        raise

def register_handlers():
    """Регистрация всех обработчиков"""
    
    # Базовые команды
    from bot.handlers.base import register_base_handlers
    register_base_handlers()
    
    # Админ-команды
    admin.register_admin_handlers()
    
    # Поддержка
    support.register_support_handlers()
    
    # Кэшбэки
    cashback_100.register_handlers()
    cashback_150.register_handlers()
    cashback_250.register_handlers()
    raffle_5000.register_handlers()
    
    bot_logger.info("Все обработчики зарегистрированы")

if __name__ == "__main__":
    asyncio.run(main())