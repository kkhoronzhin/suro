# -*- coding: utf-8 -*-
"""
Обработчик для кэшбэка 250₽ (расширенный отзыв + сторис)
"""

from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update

from bot.handlers.cashback_base import BaseCashbackHandler, WAITING_FOR_ARTICLE, WAITING_FOR_PHONE, \
    WAITING_FOR_REVIEW_DATE, WAITING_FOR_PURCHASE_PHOTO, WAITING_FOR_REVIEW_PHOTO, WAITING_FOR_PUBLICATION_SCREENSHOT
from bot.instance import application
from bot.services.logger import bot_logger

class Cashback250Handler(BaseCashbackHandler):
    """Обработчик для 250₽ (расширенный отзыв)"""
    
    def __init__(self):
        super().__init__(amount=250, name="250")
    
    def _get_states(self):
        return [
            WAITING_FOR_ARTICLE,
            WAITING_FOR_PHONE,
            WAITING_FOR_REVIEW_DATE,
            WAITING_FOR_PURCHASE_PHOTO,
            WAITING_FOR_REVIEW_PHOTO,
            WAITING_FOR_PUBLICATION_SCREENSHOT
        ]
    
    def get_intro_text(self):
        return (
            "🎁 *250₽ за расширенный отзыв!*\n\n"
            "🎥 Что нужно сделать:\n"
            "1. Оставить отзыв с 5+ качественными фото\n"
            "2. Снять видеообзор (30+ секунд)\n"
            "3. Опубликовать сторис с отметкой @suro_man\n"
            "4. Прислать скриншоты всего\n\n"
            "👇 Следуйте инструкциям:"
        )
    
    def get_requirements_text(self):
        return (
            "📋 *Требования:*\n"
            "• Минимум 5 качественных фото\n"
            "• Видео от 30 секунд\n"
            "• Сторис с отметкой\n"
            "• Оценка 5 звезд\n"
            "• Все скриншоты четкие\n\n"
            "💰 Награда: 250₽ на карту/телефон"
        )

# Создаем экземпляр обработчика
cashback_250 = Cashback250Handler()

# Создаем ConversationHandler
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('cashback250', cashback_250.start_flow),
        MessageHandler(filters.Regex(r'^🎥 250₽'), cashback_250.start_flow),
        CallbackQueryHandler(cashback_250.start_flow, pattern='^cb_250$')
    ],
    states={
        WAITING_FOR_ARTICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_250.get_article)],
        WAITING_FOR_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_250.get_phone)],
        WAITING_FOR_REVIEW_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cashback_250.get_review_date)],
        WAITING_FOR_PURCHASE_PHOTO: [MessageHandler(filters.PHOTO, cashback_250.get_purchase_photo)],
        WAITING_FOR_REVIEW_PHOTO: [MessageHandler(filters.PHOTO, cashback_250.get_review_photo)],
        WAITING_FOR_PUBLICATION_SCREENSHOT: [MessageHandler(filters.PHOTO, cashback_250.get_publication_screenshot)]
    },
    fallbacks=[CommandHandler('cancel', cashback_250.cancel)]
)

def register_handlers():
    """Регистрирует обработчики для 250₽"""
    application.add_handler(conv_handler)
    bot_logger.info("Обработчик 250₽ зарегистрирован")