# -*- coding: utf-8 -*-
"""
Обработчик чата поддержки
Позволяет пользователям писать в поддержку, а админам отвечать
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from datetime import datetime
import uuid

from bot.instance import application
from config import ADMIN_CHAT_ID
from bot.services.logger import bot_logger
from bot.services.database import db

logger = logging.getLogger(__name__)

# Состояния для разговора
(WAITING_FOR_SUPPORT_MESSAGE, WAITING_FOR_ADMIN_REPLY) = range(2)

# Хранилище активных диалогов
# {admin_message_id: user_chat_id}
active_support_dialogs = {}

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /support - начало обращения в поддержку"""
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Создаем уникальный ID для обращения
    ticket_id = str(uuid.uuid4())[:8]
    context.user_data['ticket_id'] = ticket_id
    
    text = (
        "🆘 *Служба поддержки*\n\n"
        "Опишите вашу проблему или вопрос. Мы ответим в ближайшее время.\n\n"
        "Вы можете прикрепить фото или файлы.\n\n"
        "Для отмены нажмите /cancel"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')
    
    return WAITING_FOR_SUPPORT_MESSAGE

async def receive_support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает сообщение от пользователя и пересылает админам"""
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    message = update.message
    ticket_id = context.user_data.get('ticket_id', 'NO_TICKET')
    
    # Сохраняем в БД
    db.save_support_request(
        user_id=user.id,
        username=user.username,
        ticket_id=ticket_id,
        message_text=message.text or "📷 Фото/файл"
    )
    
    # Формируем сообщение для админов
    text = (
        f"🆘 *Новое обращение в поддержку*\n\n"
        f"🎫 Билет: `{ticket_id}`\n"
        f"👤 Пользователь: @{user.username or 'нет'}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"*Сообщение:*\n{message.text or '[Фото/файл]'}"
    )
    
    # Создаем клавиатуру для ответа
    keyboard = [
        [InlineKeyboardButton("✏️ Ответить", callback_data=f"reply_{chat_id}_{ticket_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем админам
    if message.text:
        admin_msg = await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        # Пересылаем оригинальное сообщение с подписью
        admin_msg = await message.forward(ADMIN_CHAT_ID)
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    # Сохраняем связь
    active_support_dialogs[admin_msg.message_id] = {
        'user_chat_id': chat_id,
        'user_id': user.id,
        'ticket_id': ticket_id
    }
    
    # Подтверждаем пользователю
    await update.message.reply_text(
        "✅ Ваше обращение отправлено. Мы ответим в ближайшее время.\n"
        "Вы можете продолжить писать - все сообщения будут добавлены к обращению."
    )
    
    bot_logger.log_user_action(
        user_id=user.id,
        action="support_request",
        details={"ticket_id": ticket_id}
    )
    
    return WAITING_FOR_SUPPORT_MESSAGE

async def admin_reply_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для админов - ответ на обращение"""
    
    query = update.callback_query
    await query.answer()
    
    if not query.data.startswith('reply_'):
        return
    
    _, user_chat_id, ticket_id = query.data.split('_', 2)
    user_chat_id = int(user_chat_id)
    
    # Сохраняем информацию в контексте
    context.user_data['replying_to'] = {
        'chat_id': user_chat_id,
        'ticket_id': ticket_id
    }
    
    await query.edit_message_text(
        text=f"{query.message.text}\n\n---\n✏️ *Введите ответ:*",
        parse_mode='Markdown'
    )
    
    return WAITING_FOR_ADMIN_REPLY

async def receive_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает ответ от админа и пересылает пользователю"""
    
    admin = update.effective_user
    reply_info = context.user_data.get('replying_to')
    
    if not reply_info:
        await update.message.reply_text("❌ Не найден активный диалог")
        return ConversationHandler.END
    
    user_chat_id = reply_info['chat_id']
    ticket_id = reply_info['ticket_id']
    
    try:
        # Отправляем ответ пользователю
        text = (
            f"💬 *Ответ поддержки*\n\n"
            f"{update.message.text}"
        )
        
        await context.bot.send_message(
            chat_id=user_chat_id,
            text=text,
            parse_mode='Markdown'
        )
        
        # Подтверждаем админу
        await update.message.reply_text(
            f"✅ Ответ отправлен пользователю. Билет #{ticket_id}"
        )
        
        bot_logger.log_user_action(
            user_id=admin.id,
            action="admin_reply",
            details={"ticket_id": ticket_id}
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при отправке: {e}\n"
            "Возможно, пользователь заблокировал бота."
        )
    
    # Очищаем контекст
    context.user_data.pop('replying_to', None)
    
    return ConversationHandler.END

async def cancel_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена обращения"""
    await update.message.reply_text("❌ Обращение отменено")
    context.user_data.pop('ticket_id', None)
    context.user_data.pop('replying_to', None)
    return ConversationHandler.END

async def support_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /history - история обращений (только для админов)"""
    
    user_id = update.effective_user.id
    
    # Проверяем, админ ли
    if user_id not in context.bot_data.get('admins', set()):
        await update.message.reply_text("❌ У вас нет прав для этой команды")
        return
    
    # Получаем историю из БД
    requests = db.get_support_requests(limit=10)
    
    if not requests:
        await update.message.reply_text("📭 История обращений пуста")
        return
    
    text = "📋 *Последние обращения:*\n\n"
    for req in requests:
        text += (
            f"🎫 {req['ticket_id']} | @{req['username'] or 'нет'}\n"
            f"💬 {req['message'][:50]}...\n"
            f"📅 {req['created_at']}\n\n"
        )
    
    await update.message.reply_text(text, parse_mode='Markdown')

def register_support_handlers():
    """Регистрирует обработчики поддержки"""
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('support', support_command),
            CommandHandler('s', support_command)  # Сокращенная версия
        ],
        states={
            WAITING_FOR_SUPPORT_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_support_message),
                MessageHandler(filters.PHOTO, receive_support_message),
                MessageHandler(filters.Document.ALL, receive_support_message),
                CommandHandler('cancel', cancel_support)
            ],
            WAITING_FOR_ADMIN_REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_reply),
                CommandHandler('cancel', cancel_support)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_support)]
    )
    
    application.add_handler(conv_handler)
    
    # Обработчик для callback'ов админов
    application.add_handler(CommandHandler('history', support_history_command))
    
    # Обработчик для inline-ответов
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(admin_reply_callback, pattern=r'^reply_'))
    
    logger.info("Обработчики поддержки зарегистрированы")