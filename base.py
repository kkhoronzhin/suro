# -*- coding: utf-8 -*-
"""
Базовые обработчики (start, help, menu)
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from bot.instance import application
from bot.services.logger import bot_logger
from bot.services.database import db
from config import ADMIN_CHAT_ID

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Сохраняем/обновляем пользователя в БД
    user_data = {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'language_code': user.language_code
    }
    await db.save_user(user_data)
    
    # Проверяем параметры (например, /start gift)
    args = context.args
    if args and args[0] == 'gift':
        await update.message.reply_text("🎁 Вы открыли бота по спецссылке! Спасибо!")
    
    # Приветственное сообщение
    welcome_text = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🎁 *SURO* — бонусы за отзывы на Wildberries!\n\n"
        "💫 *Наши магазины:*\n"
        "👉 [Wildberries](https://www.wildberries.ru/seller/52880)\n"
        "👉 [Ozon](https://www.ozon.ru/seller/suro-2015051/)\n\n"
        "💰 *Выберите награду:*\n"
        "• 100₽ — текстовый отзыв\n"
        "• 150₽ — отзыв с фото/видео\n"
        "• 250₽ — расширенный отзыв + сторис\n"
        "• 5000₽ — розыгрыш!\n\n"
        "👇 Выберите вариант ниже:"
    )
    
    # Инлайн-клавиатура
    inline_keyboard = [
        [
            InlineKeyboardButton("✍️ 100₽ - текст", callback_data="cb_100"),
            InlineKeyboardButton("📸 150₽ - фото", callback_data="cb_150")
        ],
        [
            InlineKeyboardButton("🎥 250₽ - расширенный", callback_data="cb_250"),
            InlineKeyboardButton("🏆 5000₽ - розыгрыш", callback_data="raffle")
        ]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)
    
    # Reply-клавиатура (для быстрого доступа)
    reply_keyboard = [
        [KeyboardButton("✍️ 100₽ - текстовый отзыв")],
        [KeyboardButton("📸 150₽ - отзыв с фото")],
        [KeyboardButton("🎥 250₽ - расширенный отзыв")],
        [KeyboardButton("🏆 Участвовать в розыгрыше 5000₽")],
        [KeyboardButton("🆘 Поддержка")]
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=inline_markup,
        disable_web_page_preview=True
    )
    
    # Отправляем второе сообщение с reply-клавиатурой
    await update.message.reply_text(
        "👇 Или используйте кнопки ниже:",
        reply_markup=reply_markup
    )
    
    # Уведомление админов о новом пользователе
    is_new = await db.is_new_user(user.id)
    if is_new:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"👤 Новый пользователь: @{user.username or user.first_name} (ID: {user.id})"
        )
    
    bot_logger.log_user_action(
        user_id=user.id,
        action="start",
        details={"username": user.username}
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    
    user = update.effective_user
    is_admin = user.id in context.bot_data.get('admins', set())
    
    help_text = (
        "📚 *Список команд:*\n\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/support - Связаться с поддержкой\n"
        "/menu - Показать меню\n\n"
        "📞 *По всем вопросам:* @suro_support"
    )
    
    if is_admin:
        admin_help = (
            "\n\n👑 *Админ-команды:*\n"
            "/stats - Статистика\n"
            "/msg - Рассылка всем\n"
            "/pm - Личное сообщение\n"
            "/update - Обновить данные\n"
            "/addadmin - Добавить админа\n"
            "/deladmin - Удалить админа\n"
            "/logs - Посмотреть логи\n"
            "/clear_cache - Очистить кэш"
        )
        help_text += admin_help
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu - показывает главное меню"""
    await start_command(update, context)

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений (reply-кнопки)"""
    
    text = update.message.text
    
    if text == "✍️ 100₽ - текстовый отзыв":
        await cashback_100.start_flow(update, context)
    elif text == "📸 150₽ - отзыв с фото":
        await cashback_150.start_flow(update, context)
    elif text == "🎥 250₽ - расширенный отзыв":
        await cashback_250.start_flow(update, context)
    elif text == "🏆 Участвовать в розыгрыше 5000₽":
        await raffle_5000.start_flow(update, context)
    elif text == "🆘 Поддержка":
        await support_command(update, context)
    else:
        await update.message.reply_text(
            "Я не понимаю эту команду. Используйте /help для списка команд."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок"""
    
    error = context.error
    user = update.effective_user if update else None
    
    # Логируем ошибку
    bot_logger.error(
        f"Ошибка при обработке обновления: {error}",
        extra={
            "user_id": user.id if user else None,
            "update": str(update) if update else None
        },
        exc_info=True
    )
    
    # Уведомляем админов
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🔥 *Критическая ошибка:*\n```\n{error}\n```",
            parse_mode='Markdown'
        )
    except:
        pass
    
    # Сообщаем пользователю (если есть)
    if update and update.effective_chat:
        await update.effective_chat.send_message(
            "😔 Произошла ошибка. Администраторы уже уведомлены."
        )

def register_base_handlers():
    """Регистрирует базовые обработчики"""
    
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('menu', menu_command))
    application.add_handler(CommandHandler('s', support_command))  # Алиас для поддержки
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # Глобальный обработчик ошибок
    application.add_error_handler(error_handler)