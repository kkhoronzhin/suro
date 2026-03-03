# -*- coding: utf-8 -*-
"""
Обработчик для кэшбэка 150₽ (отзыв с фото)
"""

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update

from bot.handlers.cashback_base import BaseCashbackHandler, WAITING_FOR_ARTICLE, WAITING_FOR_PHONE, \
    WAITING_FOR_REVIEW_DATE, WAITING_FOR_PURCHASE_PHOTO, WAITING_FOR_REVIEW_PHOTO
from bot.instance import application
from bot.services.logger import bot_logger

class Cashback150Handler(BaseCashbackHandler):
    """Обработчик для 150₽ (отзыв с фото)"""
    
    def __init__(self):
        super().__init__(amount=150, name="150")
    
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
            "🎁 *150₽ за отзыв с фото!*\n\n"
            "📸 Что нужно сделать:\n"
            "1. Оставить отзыв с 3+ фото на Wildberries\n"
            "2. Оценка 5 звезд\n"
            "3. Сделать скриншоты отзыва и покупки\n"
            "4. Отправить их сюда\n\n"
            "👇 Следуйте инструкциям:"
        )
    
    def get_requirements_text(self):
        return (
            "📋 *Требования:*\n"
            "• Минимум 3 качественных фото\n"
            "• Отзыв на русском языке\n"
            "• Оценка 5 звезд\n"
            "• Скриншоты четкие\n\n"
            "💰 Награда: 150₽ на карту/телефон"
        )

# Создаем экземпляр обработчика
cashback_150 = Cashback150Handler()

# Создаем ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('cashback150', cashback_150.start_flow),
        MessageHandler(filters.Regex(r'^📸 150₽'), cashback_150.start_flow),
        CallbackQueryHandler(cashback_150.start_flow, pattern='^cb_150$')
    ],
    states={
        WAITING_FOR_ARTICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_150.get_article)],
        WAITING_FOR_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_150.get_phone)],
        WAITING_FOR_REVIEW_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_150.get_review_date)],
        WAITING_FOR_PURCHASE_PHOTO: [MessageHandler(filters.PHOTO, cashback_150.get_purchase_photo)],
        WAITING_FOR_REVIEW_PHOTO: [MessageHandler(filters.PHOTO, cashback_150.get_review_photo)]
    },
    fallbacks=[CommandHandler('cancel', cashback_150.cancel)]
)

def register_handlers():
    """Регистрирует обработчики для 150₽"""
    application.add_handler(conv_handler)
    bot_logger.info("Обработчик 150₽ зарегистрирован")