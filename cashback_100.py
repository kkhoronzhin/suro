# -*- coding: utf-8 -*-
"""
Обработчик для кэшбэка 100₽ (текстовый отзыв)
"""

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update

from bot.handlers.cashback_base import BaseCashbackHandler, WAITING_FOR_ARTICLE, WAITING_FOR_PHONE, \
    WAITING_FOR_REVIEW_DATE, WAITING_FOR_PURCHASE_PHOTO, WAITING_FOR_REVIEW_PHOTO
from bot.instance import application
from bot.services.logger import bot_logger

class Cashback100Handler(BaseCashbackHandler):
    """Обработчик для 100₽ (текстовый отзыв)"""
    
    def __init__(self):
        super().__init__(amount=100, name="100")
    
    def _get_states(self):
        return [
            WAITING_FOR_ARTICLE,
            WAITING_FOR_PHONE,
            WAITING_FOR_REVIEW_DATE,
            WAITING_FOR_PURCHASE_PHOTO,
            WAITING_FOR_REVIEW_PHOTO
        ]
    
    def get_intro_text(self):
        return (
            "🎁 *100₽ за текстовый отзыв!*\n\n"
            "💬 Что нужно сделать:\n"
            "1. Оставить текстовый отзыв 5⭐ на Wildberries\n"
            "2. Сделать скриншот отзыва\n"
            "3. Сделать скриншот покупки\n"
            "4. Отправить их сюда\n\n"
            "👇 Следуйте инструкциям ниже:"
        )
    
    def get_requirements_text(self):
        return (
            "📋 *Требования:*\n"
            "• Отзыв должен быть на русском языке\n"
            "• Минимум 3 предложения\n"
            "• Оценка 5 звезд\n"
            "• Скриншоты четкие и читаемые\n\n"
            "💰 Награда: 100₽ на карту/телефон"
        )
    
    async def start_flow(self, update: Update, context):
        """Запуск процесса для 100₽"""
        return await super().start_flow(update, context)

# Создаем экземпляр обработчика
cashback_100 = Cashback100Handler()

# Создаем ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('cashback100', cashback_100.start_flow),
        MessageHandler(filters.Regex(r'^✍️ 100₽'), cashback_100.start_flow),
        CallbackQueryHandler(cashback_100.start_flow, pattern='^cb_100$')
    ],
    states={
        WAITING_FOR_ARTICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_100.get_article)],
        WAITING_FOR_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_100.get_phone)],
        WAITING_FOR_REVIEW_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_100.get_review_date)],
        WAITING_FOR_PURCHASE_PHOTO: [MessageHandler(filters.PHOTO, cashback_100.get_purchase_photo)],
        WAITING_FOR_REVIEW_PHOTO: [MessageHandler(filters.PHOTO, cashback_100.get_review_photo)]
    },
    fallbacks=[CommandHandler('cancel', cashback_100.cancel)]
)

def register_handlers():
    """Регистрирует обработчики для 100₽"""
    application.add_handler(conv_handler)
    bot_logger.info("Обработчик 100₽ зарегистрирован")