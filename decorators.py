# -*- coding: utf-8 -*-
"""
Декораторы для обработчиков бота
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import logging

from bot.services.subscription import check_subscription
from bot.services.database import db
from bot.services.logger import bot_logger

logger = logging.getLogger(__name__)

def admin_required(func):
    """
    Декоратор, проверяющий права администратора
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Проверяем, есть ли пользователь в списке админов
        if user_id not in context.bot_data.get('admins', set()):
            await update.message.reply_text(
                "❌ У вас нет прав для выполнения этой команды."
            )
            bot_logger.warning(f"User {user_id} tried to access admin command without permissions")
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def subscription_required(func):
    """
    Декоратор, проверяющий подписку на канал
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Админы пропускаются
        if user_id in context.bot_data.get('admins', set()):
            return await func(update, context, *args, **kwargs)
        
        # Проверяем подписку
        is_subscribed = await check_subscription(context.bot, user_id)
        
        if not is_subscribed:
            await update.message.reply_text(
                "❌ Для использования бота необходимо подписаться на наш канал!\n\n"
                "После подписки нажмите /start"
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def rate_limit(max_calls: int = 5, period: int = 60):
    """
    Декоратор для ограничения частоты вызовов
    
    Args:
        max_calls: максимальное количество вызовов за период
        period: период в секундах
    """
    def decorator(func):
        user_calls = {}
        
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            
            # Админы не ограничены
            if user_id in context.bot_data.get('admins', set()):
                return await func(update, context, *args, **kwargs)
            
            from time import time
            now = time()
            
            # Очищаем старые записи
            user_calls[user_id] = [t for t in user_calls.get(user_id, []) if now - t < period]
            
            if len(user_calls.get(user_id, [])) >= max_calls:
                await update.message.reply_text(
                    f"⏳ Слишком много запросов. Подождите {period} секунд."
                )
                return
            
            # Добавляем текущий вызов
            user_calls.setdefault(user_id, []).append(now)
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    
    return decorator

def log_action(action_name: str = None):
    """
    Декоратор для логирования действий пользователя
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            username = update.effective_user.username
            
            action = action_name or func.__name__
            
            # Логируем начало действия
            bot_logger.info(f"User {user_id} (@{username}) started action: {action}")
            
            try:
                result = await func(update, context, *args, **kwargs)
                
                # Логируем успешное завершение
                bot_logger.info(f"User {user_id} completed action: {action}")
                
                # Сохраняем в БД
                await db.log_activity(
                    user_id=user_id,
                    action=action,
                    details={'success': True}
                )
                
                return result
                
            except Exception as e:
                # Логируем ошибку
                bot_logger.error(f"User {user_id} failed action {action}: {e}")
                
                # Сохраняем в БД
                await db.log_activity(
                    user_id=user_id,
                    action=action,
                    details={'success': False, 'error': str(e)}
                )
                
                raise
        
        return wrapper
    
    return decorator

def catch_errors(func):
    """
    Декоратор для отлова ошибок в обработчиках
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            
            # Пытаемся отправить сообщение пользователю
            try:
                await update.message.reply_text(
                    "😔 Произошла ошибка. Администраторы уже уведомлены."
                )
            except:
                pass
            
            # Пробрасываем ошибку дальше для глобального обработчика
            raise
    
    return wrapper