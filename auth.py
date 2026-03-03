# -*- coding: utf-8 -*-
"""
Аутентификация для веб-интерфейса
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from bot.services.database import db

auth_bp = Blueprint('auth', __name__)

class User:
    """Класс пользователя для Flask-Login"""
    
    def __init__(self, user_id, username, is_admin=False):
        self.id = user_id
        self.username = username
        self.is_admin = is_admin
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('login')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Здесь должна быть проверка пароля
        # В реальном проекте используйте хеширование
        
        # Для демо используем простую проверку
        if username == 'admin' and password == 'admin123':
            user = User(1, username, is_admin=True)
            login_user(user, remember=remember)
            
            # Логируем вход
            from bot.services.logger import web_logger
            web_logger.info(f"Admin {username} logged in")
            
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Профиль пользователя"""
    return render_template('profile.html')

# Загрузчик пользователя для Flask-Login
@auth_bp.record_once
def on_load(state):
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(state.app)
    
    @login_manager.user_loader
    def load_user(user_id):
        # Здесь должна быть загрузка из БД
        # Для демо возвращаем тестового пользователя
        if user_id == '1':
            return User(1, 'admin', is_admin=True)
        return None