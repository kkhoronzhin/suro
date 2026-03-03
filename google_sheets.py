# -*- coding: utf-8 -*-
"""
Интеграция с Google Sheets (асинхронная)
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from config import GOOGLE_SHEETS_KEY, GOOGLE_CREDENTIALS_PATH
from bot.services.logger import bot_logger

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Сервис для работы с Google Sheets"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self._init_client()
    
    def _init_client(self):
        """Инициализация клиента (синхронно)"""
        try:
            if not GOOGLE_CREDENTIALS_PATH or not os.path.exists(GOOGLE_CREDENTIALS_PATH):
                logger.warning("Google Sheets credentials not found, skipping initialization")
                return
            
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                GOOGLE_CREDENTIALS_PATH, scope
            )
            
            self.client = gspread.authorize(credentials)
            
            if GOOGLE_SHEETS_KEY:
                self.spreadsheet = self.client.open_by_key(GOOGLE_SHEETS_KEY)
                logger.info("Google Sheets client initialized")
            
        except Exception as e:
            logger.error(f"Error initializing Google Sheets: {e}")
    
    async def log_user_start(self, user_id: int, username: Optional[str] = None):
        """Логирует запуск бота пользователем"""
        if not self.spreadsheet:
            return
        
        try:
            loop = asyncio.get_event_loop()
            sheet = self.spreadsheet.worksheet("Переходы")
            
            await loop.run_in_executor(None, sheet.append_row, [
                str(user_id),
                username or "",
                datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            ])
            
        except Exception as e:
            logger.error(f"Error logging user start to Google Sheets: {e}")
    
    async def log_application(self, data: Dict[str, Any]):
        """Логирует заявку в Google Sheets"""
        if not self.spreadsheet:
            return
        
        try:
            loop = asyncio.get_event_loop()
            sheet = self.spreadsheet.worksheet("Заявки")
            
            row = [
                str(data.get('user_id', '')),
                data.get('username', ''),
                data.get('type', ''),
                str(data.get('amount', '')),
                data.get('article', ''),
                data.get('phone', ''),
                data.get('review_date', ''),
                data.get('review_photo', ''),
                data.get('purchase_photo', ''),
                data.get('publication_photo', ''),
                datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                data.get('status', '0')
            ]
            
            await loop.run_in_executor(None, sheet.append_row, row)
            
        except Exception as e:
            logger.error(f"Error logging application to Google Sheets: {e}")
    
    async def log_error(self, error_data: Dict[str, Any]):
        """Логирует ошибку"""
        if not self.spreadsheet:
            return
        
        try:
            loop = asyncio.get_event_loop()
            sheet = self.spreadsheet.worksheet("Ошибки")
            
            row = [
                str(error_data.get('user_id', '')),
                error_data.get('username', ''),
                error_data.get('error', ''),
                error_data.get('details', ''),
                datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            ]
            
            await loop.run_in_executor(None, sheet.append_row, row)
            
        except Exception as e:
            logger.error(f"Error logging error to Google Sheets: {e}")
    
    async def ensure_worksheets(self):
        """Создает необходимые листы, если их нет"""
        if not self.spreadsheet:
            return
        
        try:
            loop = asyncio.get_event_loop()
            required_worksheets = ["Переходы", "Заявки", "Ошибки"]
            
            existing = [ws.title for ws in self.spreadsheet.worksheets()]
            
            for ws_name in required_worksheets:
                if ws_name not in existing:
                    await loop.run_in_executor(
                        None, 
                        self.spreadsheet.add_worksheet,
                        ws_name, 1000, 20
                    )
                    
                    # Добавляем заголовки
                    ws = self.spreadsheet.worksheet(ws_name)
                    
                    if ws_name == "Переходы":
                        headers = ["User ID", "Username", "Timestamp"]
                    elif ws_name == "Заявки":
                        headers = [
                            "User ID", "Username", "Type", "Amount", "Article",
                            "Phone", "Review Date", "Review Photo", "Purchase Photo",
                            "Publication Photo", "Created At", "Status"
                        ]
                    elif ws_name == "Ошибки":
                        headers = ["User ID", "Username", "Error", "Details", "Timestamp"]
                    
                    await loop.run_in_executor(None, ws.append_row, headers)
                    
        except Exception as e:
            logger.error(f"Error ensuring worksheets: {e}")

# Глобальный экземпляр
google_sheets = GoogleSheetsService()

# Удобные функции
async def log_user_start(user_id: int, username: str = None):
    await google_sheets.log_user_start(user_id, username)

async def log_application(data: Dict[str, Any]):
    await google_sheets.log_application(data)

async def log_error(error_data: Dict[str, Any]):
    await google_sheets.log_error(error_data)