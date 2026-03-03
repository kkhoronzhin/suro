# -*- coding: utf-8 -*-
"""
Улучшенное логирование для бота
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Any, Dict
from config import LOG_LEVEL, LOG_FORMAT, LOG_MAX_BYTES, LOG_BACKUP_COUNT

class BotLogger:
    """
    Класс для логирования с поддержкой разных уровней и форматов
    """
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Создаем логгер
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Убираем дублирование
        self.logger.handlers = []
        
        # Форматтер
        formatter = logging.Formatter(LOG_FORMAT)
        
        # Файловый обработчик для всех логов
        file_handler = RotatingFileHandler(
            self.log_dir / f"{name}.log",
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Файловый обработчик только для ошибок
        error_handler = RotatingFileHandler(
            self.log_dir / f"{name}_errors.log",
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # Консольный вывод
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: str, extra: Dict[str, Any] = None):
        self.logger.debug(self._format(msg, extra))
    
    def info(self, msg: str, extra: Dict[str, Any] = None):
        self.logger.info(self._format(msg, extra))
    
    def warning(self, msg: str, extra: Dict[str, Any] = None):
        self.logger.warning(self._format(msg, extra))
    
    def error(self, msg: str, extra: Dict[str, Any] = None, exc_info=False):
        self.logger.error(self._format(msg, extra), exc_info=exc_info)
    
    def critical(self, msg: str, extra: Dict[str, Any] = None, exc_info=False):
        self.logger.critical(self._format(msg, extra), exc_info=exc_info)
    
    def _format(self, msg: str, extra: Dict[str, Any] = None) -> str:
        """Форматирует сообщение с дополнительными данными"""
        if extra:
            return f"{msg} | {json.dumps(extra, ensure_ascii=False)}"
        return msg
    
    def log_user_action(self, user_id: int, action: str, details: Dict[str, Any] = None):
        """Логирует действие пользователя"""
        extra = {
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            extra.update(details)
        
        self.info(f"User action: {action}", extra)
    
    def log_error_with_user(self, user_id: int, error: str, details: Dict[str, Any] = None):
        """Логирует ошибку с информацией о пользователе"""
        extra = {
            "user_id": user_id,
            "error_type": error,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            extra.update(details)
        
        self.error(f"Error for user {user_id}: {error}", extra)

# Создаем экземпляры логгеров для разных компонентов
bot_logger = BotLogger("bot")
web_logger = BotLogger("web")
api_logger = BotLogger("api")
db_logger = BotLogger("database")