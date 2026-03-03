# -*- coding: utf-8 -*-
"""
Обработчик для розыгрыша 5000₽
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime
import random

from bot.handlers.cashback_base import BaseCashbackHandler, WAITING_FOR_ARTICLE, WAITING_FOR_PHONE, \
    WAITING_FOR_REVIEW_DATE, WAITING_FOR_PURCHASE_PHOTO, WAITING_FOR_REVIEW_PHOTO
from bot.instance import application
from bot.services.logger import bot_logger
from bot.services.database import db
from config import ADMIN_CHAT_ID

class Raffle5000Handler(BaseCashbackHandler):
    """Обработчик для розыгрыша 5000₽"""
    
    def __init__(self):
        super().__init__(amount=5000, name="raffle")
    
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
            "🏆 *РОЗЫГРЫШ 5000₽!*\n\n"
            "Каждый месяц мы разыгрываем денежные призы среди наших покупателей!\n\n"
            "🎁 *Призы:*\n"
            "🥇 1 место — 5000₽\n"
            "🥈 2 место — 3000₽\n"
            "🥉 3 место — 2000₽\n"
            "🏅 4-10 место — 1000₽\n\n"
            "👇 Хотите поучаствовать?"
        )
    
    def get_requirements_text(self):
        return (
            "📋 *Как участвовать:*\n\n"
            "1. Сделайте красивую фотографию нашего товара\n"
            "2. Оставьте отзыв с этим фото на Wildberries\n"
            "3. Пришлите скриншоты сюда\n"
            "4. Ждите результатов в начале месяца!\n\n"
            "⭐ Чем креативнее фото, тем выше шанс!"
        )
    
    async def start_flow(self, update: Update, context):
        """Запуск процесса участия в розыгрыше"""
        
        # Показываем информационное меню
        keyboard = [
            [InlineKeyboardButton("❓ Подробнее", callback_data="raffle_info")],
            [InlineKeyboardButton("✅ Участвовать", callback_data="raffle_participate")],
            [InlineKeyboardButton("🏆 Результаты", callback_data="raffle_results")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            self.get_intro_text(),
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        return ConversationHandler.END
    
    async def raffle_info(self, update: Update, context):
        """Показывает подробную информацию о розыгрыше"""
        
        query = update.callback_query
        await query.answer()
        
        text = (
            "📅 *О розыгрыше*\n\n"
            "• Проводится каждый месяц\n"
            "• Участвуют все, кто оставил отзыв с фото\n"
            "• Победителей выбирает жюри\n"
            "• Результаты 1-го числа каждого месяца\n\n"
            "🎯 *Критерии оценки:*\n"
            "• Качество фото\n"
            "• Креативность\n"
            "• Полезность отзыва\n\n"
            "Удачи! 🍀"
        )
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="raffle_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def raffle_participate(self, update: Update, context):
        """Начало участия в розыгрыше"""
        
        query = update.callback_query
        await query.answer()
        
        # Переходим к сбору данных
        return await super().start_flow(update, context)
    
    async def raffle_results(self, update: Update, context):
        """Показывает результаты последнего розыгрыша"""
        
        query = update.callback_query
        await query.answer()
        
        # Получаем последние результаты из БД
        results = await db.get_last_raffle_results()
        
        if results:
            text = "🏆 *Результаты прошлого месяца:*\n\n"
            for i, winner in enumerate(results[:10], 1):
                text += f"{i}. {winner['username']} — {winner['prize']}₽\n"
        else:
            text = "📭 Результаты пока не объявлены. Следите за новостями!"
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="raffle_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def raffle_back(self, update: Update, context):
        """Возврат в главное меню розыгрыша"""
        
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("❓ Подробнее", callback_data="raffle_info")],
            [InlineKeyboardButton("✅ Участвовать", callback_data="raffle_participate")],
            [InlineKeyboardButton("🏆 Результаты", callback_data="raffle_results")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            self.get_intro_text(),
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

# Создаем экземпляр обработчика
raffle_5000 = Raffle5000Handler()

# Создаем ConversationHandler для сбора данных
conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler('raffle', raffle_5000.start_flow),
        MessageHandler(filters.Regex(r'^🏆'), raffle_5000.start_flow),
        CallbackQueryHandler(raffle_5000.raffle_participate, pattern='^raffle_participate$')
    ],
    states={
        WAITING_FOR_ARTICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_5000.get_article)],
        WAITING_FOR_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_5000.get_phone)],
        WAITING_FOR_REVIEW_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, raffle_5000.get_review_date)],
        WAITING_FOR_PURCHASE_PHOTO: [MessageHandler(filters.PHOTO, raffle_5000.get_purchase_photo)],
        WAITING_FOR_REVIEW_PHOTO: [MessageHandler(filters.PHOTO, raffle_5000.get_review_photo)]
    },
    fallbacks=[CommandHandler('cancel', raffle_5000.cancel)]
)

def register_handlers():
    """Регистрирует обработчики для розыгрыша"""
    
    # Регистрируем ConversationHandler
    application.add_handler(conv_handler)
    
    # Регистрируем CallbackQueryHandler'ы
    application.add_handler(CallbackQueryHandler(raffle_5000.raffle_info, pattern='^raffle_info$'))
    application.add_handler(CallbackQueryHandler(raffle_5000.raffle_results, pattern='^raffle_results$'))
    application.add_handler(CallbackQueryHandler(raffle_5000.raffle_back, pattern='^raffle_back$'))
    
    bot_logger.info("Обработчик розыгрыша 5000₽ зарегистрирован")