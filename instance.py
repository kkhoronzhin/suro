# -*- coding: utf-8 -*-
"""
Экземпляр бота с FSM и хранилищем
"""

from telegram.ext import Application, ApplicationBuilder, PicklePersistence
from telegram.ext.filters import BaseFilter
import logging
from config import BOT_TOKEN

logger = logging.getLogger(__name__)

# Создаем персистентное хранилище для состояний
persistence = PicklePersistence(filepath="data/bot_persistence.pkl")

# Создаем приложение
application = ApplicationBuilder() \
    .token(BOT_TOKEN) \
    .persistence(persistence) \
    .concurrent_updates(True) \
    .build()

# Фильтр для проверки подписки (будет использоваться в middleware)
class SubscriptionFilter(BaseFilter):
    def __init__(self, check_function):
        self.check_function = check_function
        self.name = "SubscriptionFilter"
    
    def filter(self, message):
        """Фильтр пропускает только сообщения от подписанных пользователей"""
        if not message.from_user:
            return False
        return self.check_function(message.from_user.id)

# Функция для получения бота (для обратной совместимости)
def get_bot():
    return application.bot

# Функция для запуска бота
async def run_bot():
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    logger.info("Бот запущен и слушает обновления")

# Функция для остановки бота
async def stop_bot():
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    logger.info("Бот остановлен")