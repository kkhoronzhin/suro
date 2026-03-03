# -*- coding: utf-8 -*-
"""
Базовый класс для всех кэшбэк-обработчиков
"""

from abc import ABC, abstractmethod
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
import re
import os

from bot.instance import application
from bot.services.logger import bot_logger
from bot.services.database import db
from bot.services.google_sheets import log_application
from bot.services.file_storage import save_photo
from config import MEDIA_PATH, PUBLIC_URL, ADMIN_CHAT_ID

# Состояния для FSM
(WAITING_FOR_ARTICLE,
 WAITING_FOR_PHONE,
 WAITING_FOR_REVIEW_DATE,
 WAITING_FOR_PURCHASE_PHOTO,
 WAITING_FOR_REVIEW_PHOTO,
 WAITING_FOR_PUBLICATION_SCREENSHOT) = range(6)

class BaseCashbackHandler(ABC):
    """Абстрактный базовый класс для обработчиков кэшбэков"""
    
    def __init__(self, amount: int, name: str):
        self.amount = amount
        self.name = name
        self.states = self._get_states()
    
    @abstractmethod
    def _get_states(self) -> list:
        """Возвращает список состояний для данного типа кэшбэка"""
        pass
    
    @abstractmethod
    def get_intro_text(self) -> str:
        """Возвращает приветственный текст"""
        pass
    
    @abstractmethod
    def get_requirements_text(self) -> str:
        """Возвращает текст с требованиями"""
        pass
    
    async def start_flow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск процесса подачи заявки"""
        
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Проверяем, не слишком ли много заявок сегодня
        today_apps = await db.get_user_applications_today(user.id)
        if today_apps >= 3:
            await update.message.reply_text(
                "❌ Вы сегодня уже отправили 3 заявки. Попробуйте завтра!"
            )
            return ConversationHandler.END
        
        # Очищаем старые данные
        context.user_data.clear()
        context.user_data['cashback_type'] = self.name
        context.user_data['amount'] = self.amount
        
        # Отправляем приветствие
        await update.message.reply_text(
            self.get_intro_text(),
            parse_mode='Markdown'
        )
        
        # Отправляем картинку с инструкцией (если есть)
        try:
            image_path = f"images/opening_{self.amount}.jpg"
            if os.path.exists(image_path):
                with open(image_path, 'rb') as photo:
                    await update.message.reply_photo(photo)
        except:
            pass
        
        # Отправляем требования
        await update.message.reply_text(
            self.get_requirements_text(),
            parse_mode='Markdown'
        )
        
        # Запрашиваем артикул
        await update.message.reply_text(
            "🔢 Введите артикул товара с Wildberries:\n"
            "(можно найти в ссылке на товар)"
        )
        
        return WAITING_FOR_ARTICLE
    
    async def get_article(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение артикула"""
        
        article = update.message.text.strip()
        
        # Простая валидация артикула (только цифры)
        if not article.isdigit():
            await update.message.reply_text(
                "❌ Артикул должен состоять только из цифр.\n"
                "Попробуйте еще раз:"
            )
            return WAITING_FOR_ARTICLE
        
        context.user_data['article'] = article
        
        await update.message.reply_text(
            "📱 Введите номер телефона для перевода (в формате +79123456789):"
        )
        
        return WAITING_FOR_PHONE
    
    async def get_phone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение номера телефона"""
        
        phone = update.message.text.strip()
        
        # Валидация российского номера
        phone_pattern = r'^(\+7|8)[0-9]{10}$'
        if not re.match(phone_pattern, phone):
            await update.message.reply_text(
                "❌ Неверный формат номера.\n"
                "Используйте формат: +79123456789 или 89123456789"
            )
            return WAITING_FOR_PHONE
        
        # Приводим к единому формату
        if phone.startswith('8'):
            phone = '+7' + phone[1:]
        
        context.user_data['phone'] = phone
        
        await update.message.reply_text(
            "📅 Укажите дату отзыва (в формате ДД.ММ.ГГГГ):"
        )
        
        return WAITING_FOR_REVIEW_DATE
    
    async def get_review_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение даты отзыва"""
        
        date_text = update.message.text.strip()
        
        try:
            review_date = datetime.strptime(date_text, "%d.%m.%Y")
            
            # Проверяем, что дата не в будущем
            if review_date > datetime.now():
                await update.message.reply_text(
                    "❌ Дата не может быть в будущем!"
                )
                return WAITING_FOR_REVIEW_DATE
            
            context.user_data['review_date'] = date_text
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат даты.\n"
                "Используйте формат: ДД.ММ.ГГГГ (например, 25.12.2024)"
            )
            return WAITING_FOR_REVIEW_DATE
        
        # Запрашиваем скриншот покупки
        await update.message.reply_text(
            "🛍 Теперь пришлите скриншот покупки (чек из приложения WB):"
        )
        
        return WAITING_FOR_PURCHASE_PHOTO
    
    async def get_purchase_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение скриншота покупки"""
        
        user = update.effective_user
        photo = update.message.photo[-1]  # Берем самое большое фото
        
        # Сохраняем фото
        file_path = await save_photo(
            photo=photo,
            user_id=user.id,
            prefix=f"purchase_{self.amount}"
        )
        
        if file_path:
            context.user_data['purchase_photo'] = file_path
            context.user_data['purchase_photo_file_id'] = photo.file_id
            
            # Запрашиваем следующий шаг
            await update.message.reply_text(
                "⭐ Отлично! Теперь пришлите скриншот самого отзыва:"
            )
            
            return WAITING_FOR_REVIEW_PHOTO
        else:
            await update.message.reply_text(
                "❌ Не удалось сохранить фото. Попробуйте еще раз:"
            )
            return WAITING_FOR_PURCHASE_PHOTO
    
    async def get_review_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение скриншота отзыва"""
        
        user = update.effective_user
        photo = update.message.photo[-1]
        
        # Сохраняем фото
        file_path = await save_photo(
            photo=photo,
            user_id=user.id,
            prefix=f"review_{self.amount}"
        )
        
        if file_path:
            context.user_data['review_photo'] = file_path
            context.user_data['review_photo_file_id'] = photo.file_id
            
            # Если это расширенный кэшбэк (250₽), запрашиваем доп. шаг
            if self.amount == 250:
                await update.message.reply_text(
                    "📸 Финальный шаг! Пришлите скриншот публикации в сторис "
                    "с отметкой нашего магазина:"
                )
                return WAITING_FOR_PUBLICATION_SCREENSHOT
            else:
                # Завершаем оформление
                await self.finish_application(update, context)
                return ConversationHandler.END
        else:
            await update.message.reply_text(
                "❌ Не удалось сохранить фото. Попробуйте еще раз:"
            )
            return WAITING_FOR_REVIEW_PHOTO
    
    async def get_publication_screenshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение скриншота публикации (для 250₽)"""
        
        user = update.effective_user
        photo = update.message.photo[-1]
        
        file_path = await save_photo(
            photo=photo,
            user_id=user.id,
            prefix="publication"
        )
        
        if file_path:
            context.user_data['publication_photo'] = file_path
            
            # Завершаем оформление
            await self.finish_application(update, context)
        else:
            await update.message.reply_text(
                "❌ Не удалось сохранить фото. Попробуйте еще раз:"
            )
            return WAITING_FOR_PUBLICATION_SCREENSHOT
        
        return ConversationHandler.END
    
    async def finish_application(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Завершение оформления заявки"""
        
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Собираем все данные
        app_data = {
            'user_id': user.id,
            'username': user.username or user.first_name,
            'type': self.name,
            'amount': self.amount,
            'article': context.user_data.get('article'),
            'phone': context.user_data.get('phone'),
            'review_date': context.user_data.get('review_date'),
            'review_photo': context.user_data.get('review_photo'),
            'purchase_photo': context.user_data.get('purchase_photo'),
            'publication_photo': context.user_data.get('publication_photo'),
            'created_at': datetime.now().isoformat()
        }
        
        # Сохраняем в БД
        app_id = await db.save_application(app_data)
        
        # Логируем в Google Sheets
        try:
            await log_application(app_data)
        except Exception as e:
            bot_logger.error(f"Ошибка логирования в Google Sheets: {e}")
        
        # Отправляем подтверждение пользователю
        await update.message.reply_text(
            f"✅ *Заявка №{app_id} создана!*\n\n"
            f"Сумма: {self.amount}₽\n"
            f"Артикул: {app_data['article']}\n\n"
            "⏳ Ожидайте проверки в течение 5 рабочих дней.\n\n"
            "⚠️ *Важно:*\n"
            "• Не удаляйте отзыв до получения выплаты\n"
            "• Проверяйте статус в боте\n"
            "• При проблемах пишите в /support",
            parse_mode='Markdown'
        )
        
        # Уведомляем админов
        keyboard = [
            [
                InlineKeyboardButton("✅ Принять", callback_data=f"app_approve_{app_id}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"app_reject_{app_id}")
            ],
            [InlineKeyboardButton("👤 Профиль", callback_data=f"user_{user.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        admin_text = (
            f"🆕 *Новая заявка!*\n\n"
            f"ID: {app_id}\n"
            f"Сумма: {self.amount}₽\n"
            f"Пользователь: @{user.username or user.first_name} (ID: {user.id})\n"
            f"Артикул: {app_data['article']}\n"
            f"Телефон: {app_data['phone']}\n"
            f"Дата отзыва: {app_data['review_date']}\n"
            f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        bot_logger.log_user_action(
            user_id=user.id,
            action="application_created",
            details={"app_id": app_id, "amount": self.amount}
        )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена оформления заявки"""
        await update.message.reply_text(
            "❌ Оформление заявки отменено.\n"
            "Можете начать заново в любой момент."
        )
        context.user_data.clear()
        return ConversationHandler.END