# -*- coding: utf-8 -*-
"""
Админ-команды и утилиты
"""

import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram.constants import ParseMode

from bot.instance import application
from bot.services.logger import bot_logger
from bot.services.database import db
from bot.services.subscription import clear_subscription_cache
from config import ADMIN_CHAT_ID

# Состояния для разговоров
(WAITING_FOR_ADD_ADMIN_ID,
 WAITING_FOR_DEL_ADMIN_ID,
 WAITING_FOR_BROADCAST,
 WAITING_FOR_PM_USER_ID,
 WAITING_FOR_PM_TEXT) = range(5)

def admin_required(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in context.bot_data.get('admins', set()):
            await update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

@admin_required
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика бота"""
    
    stats = await db.get_stats()
    
    text = (
        "📊 *Статистика бота*\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"📝 Всего заявок: {stats['total_applications']}\n"
        f"💰 Выплачено: {stats['total_paid']}₽\n"
        f"👑 Администраторов: {stats['total_admins']}\n\n"
        f"📅 *За сегодня:*\n"
        f"Новых: {stats['today_users']}\n"
        f"Заявок: {stats['today_applications']}\n"
    )
    
    await update.message.reply_text(text, parse_mode='Markdown')
    
    bot_logger.log_user_action(
        user_id=update.effective_user.id,
        action="stats",
        details=stats
    )

@admin_required
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления администратора"""
    
    await update.message.reply_text(
        "👑 Введите Telegram ID пользователя, которого хотите сделать администратором:\n"
        "(можно получить через /getid)"
    )
    return WAITING_FOR_ADD_ADMIN_ID

@admin_required
async def add_admin_receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение ID для добавления админа"""
    
    try:
        user_id = int(update.message.text.strip())
        
        # Проверяем, существует ли пользователь
        user_exists = await db.user_exists(user_id)
        if not user_exists:
            await update.message.reply_text(
                "❌ Пользователь с таким ID не найден в базе.\n"
                "Он должен хотя бы раз запустить бота."
            )
            return ConversationHandler.END
        
        # Добавляем админа
        await db.add_admin(user_id)
        
        # Обновляем кэш админов
        admins = await db.get_admins()
        context.bot_data['admins'] = set(admins)
        
        await update.message.reply_text(f"✅ Пользователь {user_id} теперь администратор!")
        
        # Уведомляем нового админа
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="👑 Вам выданы права администратора в боте!"
            )
        except:
            pass
        
        bot_logger.log_user_action(
            user_id=update.effective_user.id,
            action="add_admin",
            details={"new_admin_id": user_id}
        )
        
    except ValueError:
        await update.message.reply_text("❌ Некорректный ID. Введите число.")
        return WAITING_FOR_ADD_ADMIN_ID
    
    return ConversationHandler.END

@admin_required
async def del_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало удаления администратора"""
    
    await update.message.reply_text(
        "👑 Введите Telegram ID пользователя, которого хотите лишить прав:"
    )
    return WAITING_FOR_DEL_ADMIN_ID

@admin_required
async def del_admin_receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение ID для удаления админа"""
    
    try:
        user_id = int(update.message.text.strip())
        
        # Удаляем админа
        await db.remove_admin(user_id)
        
        # Обновляем кэш
        admins = await db.get_admins()
        context.bot_data['admins'] = set(admins)
        
        await update.message.reply_text(f"✅ У пользователя {user_id} отозваны права администратора.")
        
        bot_logger.log_user_action(
            user_id=update.effective_user.id,
            action="remove_admin",
            details={"removed_admin_id": user_id}
        )
        
    except ValueError:
        await update.message.reply_text("❌ Некорректный ID. Введите число.")
        return WAITING_FOR_DEL_ADMIN_ID
    
    return ConversationHandler.END

@admin_required
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало рассылки"""
    
    await update.message.reply_text(
        "📢 Введите текст для рассылки всем пользователям:\n\n"
        "Поддерживается Markdown. Для отмены: /cancel"
    )
    return WAITING_FOR_BROADCAST

@admin_required
async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка рассылки"""
    
    text = update.message.text
    admin_id = update.effective_user.id
    
    # Подтверждение
    keyboard = [
        [
            InlineKeyboardButton("✅ Отправить", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="broadcast_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.user_data['broadcast_text'] = text
    
    await update.message.reply_text(
        f"📢 *Предпросмотр:*\n\n{text}\n\n---\n\nПодтвердите отправку:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения рассылки"""
    
    query = update.callback_query
    await query.answer()
    
    if query.data == "broadcast_confirm":
        text = context.user_data.get('broadcast_text', '')
        
        await query.edit_message_text("📤 Начинаю рассылку...")
        
        # Получаем всех пользователей
        users = await db.get_all_user_ids()
        
        sent = 0
        failed = 0
        
        for user_id in users:
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    parse_mode='Markdown'
                )
                sent += 1
                await asyncio.sleep(0.05)  # Чтобы не флудить
            except Exception as e:
                failed += 1
                if "blocked" in str(e).lower():
                    await db.mark_user_blocked(user_id)
        
        await query.message.reply_text(
            f"✅ Рассылка завершена!\n\n"
            f"📨 Отправлено: {sent}\n"
            f"❌ Не доставлено: {failed}"
        )
        
        bot_logger.log_user_action(
            user_id=update.effective_user.id,
            action="broadcast",
            details={"sent": sent, "failed": failed}
        )
        
    elif query.data == "broadcast_cancel":
        await query.edit_message_text("❌ Рассылка отменена.")
    
    context.user_data.pop('broadcast_text', None)

@admin_required
async def pm_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало личного сообщения"""
    
    await update.message.reply_text(
        "✉️ Введите Telegram ID пользователя:"
    )
    return WAITING_FOR_PM_USER_ID

async def pm_receive_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение ID для личного сообщения"""
    
    try:
        user_id = int(update.message.text.strip())
        
        # Проверяем существование
        user = await db.get_user(user_id)
        if not user:
            await update.message.reply_text("❌ Пользователь не найден.")
            return ConversationHandler.END
        
        context.user_data['pm_user_id'] = user_id
        context.user_data['pm_user_info'] = user
        
        await update.message.reply_text(
            f"✉️ Введите сообщение для @{user['username'] or user_id}:\n"
            "(поддерживается Markdown)"
        )
        return WAITING_FOR_PM_TEXT
        
    except ValueError:
        await update.message.reply_text("❌ Некорректный ID. Введите число.")
        return WAITING_FOR_PM_USER_ID

async def pm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка личного сообщения"""
    
    text = update.message.text
    user_id = context.user_data['pm_user_id']
    user_info = context.user_data.get('pm_user_info', {})
    
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✉️ *Сообщение от администрации:*\n\n{text}",
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(f"✅ Сообщение отправлено пользователю @{user_info.get('username', user_id)}")
        
        bot_logger.log_user_action(
            user_id=update.effective_user.id,
            action="pm_sent",
            details={"to_user": user_id}
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при отправке: {e}")
    
    return ConversationHandler.END

@admin_required
async def update_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /update - обновление данных пользователей"""
    
    await update.message.reply_text("🔄 Обновляю данные пользователей...")
    
    updated = await db.refresh_all_users(context.bot)
    
    await update.message.reply_text(f"✅ Обновлено {updated} пользователей.")

@admin_required
async def clear_cache_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /clear_cache - очистка кэша"""
    
    clear_subscription_cache()
    await update.message.reply_text("🧹 Кэш проверки подписки очищен.")

@admin_required
async def get_logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /logs - получение логов"""
    
    lines = 50
    if context.args and context.args[0].isdigit():
        lines = int(context.args[0])
    
    try:
        with open('logs/bot.log', 'r') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
        
        text = f"📋 *Последние {len(last_lines)} строк лога:*\n```\n"
        text += ''.join(last_lines)[:3500]  # Ограничение Telegram
        text += "\n```"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка чтения логов: {e}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего действия"""
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END

def register_admin_handlers():
    """Регистрирует админ-обработчики"""
    
    # Простые команды
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('update', update_users_command))
    application.add_handler(CommandHandler('clear_cache', clear_cache_command))
    application.add_handler(CommandHandler('logs', get_logs_command))
    
    # Добавление админа
    add_admin_conv = ConversationHandler(
        entry_points=[CommandHandler('addadmin', add_admin_start)],
        states={
            WAITING_FOR_ADD_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_receive_id)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(add_admin_conv)
    
    # Удаление админа
    del_admin_conv = ConversationHandler(
        entry_points=[CommandHandler('deladmin', del_admin_start)],
        states={
            WAITING_FOR_DEL_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, del_admin_receive_id)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(del_admin_conv)
    
    # Рассылка
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('msg', broadcast_start)],
        states={
            WAITING_FOR_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_send)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(broadcast_conv)
    
    # Личные сообщения
    pm_conv = ConversationHandler(
        entry_points=[CommandHandler('pm', pm_start)],
        states={
            WAITING_FOR_PM_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, pm_receive_user_id)],
            WAITING_FOR_PM_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, pm_send)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(pm_conv)
    
    # Callback для рассылки
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CallbackQueryHandler(broadcast_callback, pattern=r'^broadcast_'))