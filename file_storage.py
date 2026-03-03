# -*- coding: utf-8 -*-
"""
Сервис для сохранения файлов (фото, видео)
"""

import os
import aiofiles
from datetime import datetime
from typing import Optional
import logging
from telegram import PhotoSize

from config import MEDIA_PATH

logger = logging.getLogger(__name__)

async def save_photo(photo: PhotoSize, user_id: int, prefix: str = "photo") -> Optional[str]:
    """
    Сохраняет фото из Telegram и возвращает путь к файлу
    
    Args:
        photo: Объект PhotoSize из Telegram
        user_id: ID пользователя
        prefix: Префикс для имени файла
    
    Returns:
        str: Путь к сохраненному файлу или None при ошибке
    """
    try:
        # Создаем папку по дате
        date_folder = datetime.now().strftime("%Y/%m/%d")
        full_path = os.path.join(MEDIA_PATH, date_folder)
        os.makedirs(full_path, exist_ok=True)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{user_id}_{timestamp}.jpg"
        filepath = os.path.join(full_path, filename)
        
        # Скачиваем файл
        file = await photo.get_file()
        await file.download_to_drive(filepath)
        
        # Возвращаем относительный путь для БД
        relative_path = os.path.join(date_folder, filename)
        logger.info(f"Photo saved: {relative_path}")
        
        return relative_path
        
    except Exception as e:
        logger.error(f"Error saving photo: {e}")
        return None

async def save_document(document, user_id: int, prefix: str = "doc") -> Optional[str]:
    """
    Сохраняет документ из Telegram
    """
    try:
        date_folder = datetime.now().strftime("%Y/%m/%d")
        full_path = os.path.join(MEDIA_PATH, date_folder)
        os.makedirs(full_path, exist_ok=True)
        
        # Получаем расширение файла
        filename = document.file_name
        ext = os.path.splitext(filename)[1]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{prefix}_{user_id}_{timestamp}{ext}"
        filepath = os.path.join(full_path, new_filename)
        
        file = await document.get_file()
        await file.download_to_drive(filepath)
        
        relative_path = os.path.join(date_folder, new_filename)
        logger.info(f"Document saved: {relative_path}")
        
        return relative_path
        
    except Exception as e:
        logger.error(f"Error saving document: {e}")
        return None

async def get_file_url(file_path: str) -> str:
    """
    Возвращает публичный URL для файла
    """
    from config import PUBLIC_URL
    return f"{PUBLIC_URL}/media/{file_path}"

async def delete_file(file_path: str) -> bool:
    """
    Удаляет файл
    """
    try:
        full_path = os.path.join(MEDIA_PATH, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"File deleted: {file_path}")
            return True
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
    
    return False

def get_file_size(file_path: str) -> int:
    """
    Возвращает размер файла в байтах
    """
    full_path = os.path.join(MEDIA_PATH, file_path)
    if os.path.exists(full_path):
        return os.path.getsize(full_path)
    return 0

def get_file_info(file_path: str) -> dict:
    """
    Возвращает информацию о файле
    """
    full_path = os.path.join(MEDIA_PATH, file_path)
    if os.path.exists(full_path):
        stat = os.stat(full_path)
        return {
            'path': file_path,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    return {}