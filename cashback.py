# -*- coding: utf-8 -*-
"""
Состояния FSM для кэшбэков
"""

from telegram.ext import ConversationHandler

# Состояния для сбора данных
(
    WAITING_FOR_ARTICLE,
    WAITING_FOR_PHONE,
    WAITING_FOR_REVIEW_DATE,
    WAITING_FOR_PURCHASE_PHOTO,
    WAITING_FOR_REVIEW_PHOTO,
    WAITING_FOR_PUBLICATION_SCREENSHOT,
    WAITING_FOR_CONFIRMATION
) = range(7)

# Словарь с описаниями состояний
STATE_DESCRIPTIONS = {
    WAITING_FOR_ARTICLE: "ожидание артикула",
    WAITING_FOR_PHONE: "ожидание телефона",
    WAITING_FOR_REVIEW_DATE: "ожидание даты отзыва",
    WAITING_FOR_PURCHASE_PHOTO: "ожидание скриншота покупки",
    WAITING_FOR_REVIEW_PHOTO: "ожидание скриншота отзыва",
    WAITING_FOR_PUBLICATION_SCREENSHOT: "ожидание скриншота публикации",
    WAITING_FOR_CONFIRMATION: "ожидание подтверждения"
}

def get_state_name(state: int) -> str:
    """
    Возвращает название состояния по его номеру
    """
    return STATE_DESCRIPTIONS.get(state, f"неизвестное состояние ({state})")