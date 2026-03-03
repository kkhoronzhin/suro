# -*- coding: utf-8 -*-
"""
Сервис для проверки подписки на канал
"""

import logging
from telegram import Bot
from telegram.error import TelegramError
from config import REQUIRED_CHANNEL_ID, ADMIN_CHAT_ID
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Кэш для результатов проверки
_subscription_cache = {}
_cache_ttl = timedelta(minutes=5)  # Время жизни кэша

async def check_subscription(bot: Bot, user_id: int) -> bool:
    """
    Проверяет, подписан ли пользователь на канал
    
    Args:
        bot: Экземпляр бота
        user_id: ID пользователя Telegram
    
    Returns:
        bool: True если подписан, False если нет
    """
    
    # Проверяем кэш
    cache_key = f"{user_id}"
    if cache_key in _subscription_cache:
        cache_time, result = _subscription_cache[cache_key]
        if datetime.now() - cache_time < _cache_ttl:
            return result
    
    try:
        # Пытаемся получить информацию о пользователе в канале
        chat_member = await bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL_ID,
            user_id=user_id
        )
        
        # Проверяем статус
        is_subscribed = chat_member.status in [
            'member', 'administrator', 'creator'
        ]
        
        # Сохраняем в кэш
        _subscription_cache[cache_key] = (datetime.now(), is_subscribed)
        
        logger.debug(f"Проверка подписки для {user_id}: {is_subscribed}")
        return is_subscribed
        
    except TelegramError as e:
        # Если пользователь не в канале, получаем ошибку
        if "user not found" in str(e).lower():
            _subscription_cache[cache_key] = (datetime.now(), False)
            return False
        
        # Другие ошибки (бот не админ, проблемы с сетью и т.д.)
        logger.error(f"Ошибка при проверке подписки для {user_id}: {e}")
        
        # В случае ошибки считаем, что пользователь подписан
        # чтобы не блокировать всех при проблемах с API
        return True

async def force_check_subscription(bot: Bot, user_id: int) -> bool:
    """
    Принудительная проверка подписки (без кэша)
    """
    try:
        chat_member = await bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL_ID,
            user_id=user_id
        )
        return chat_member.status in ['member', 'administrator', 'creator']
    except TelegramError:
        return False

def clear_subscription_cache(user_id: int = None):
    """
    Очищает кэш проверки подписки
    
    Args:
        user_id: Если указан, очищает только для этого пользователя
    """
    global _subscription_cache
    
    if user_id:
        cache_key = f"{user_id}"
        _subscription_cache.pop(cache_key, None)
    else:
        _subscription_cache.clear()
    
    logger.info(f"Кэш подписки очищен{' для ' + str(user_id) if user_id else ''}")

async def notify_admins_about_unsubscribe(bot: Bot, user_id: int, username: str = None):
    """
    Уведомляет админов об отписке пользователя
    """
    try:
        text = (
            f"🚫 Пользователь отписался от канала!\n\n"
            f"ID: {user_id}\n"
            f"Username: @{username if username else 'отсутствует'}"
        )
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text
        )
    except Exception as e:
        logger.error(f"Ошибка при уведомлении об отписке: {e}")