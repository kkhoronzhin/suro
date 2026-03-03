# -*- coding: utf-8 -*-
"""
Flask веб-приложение для админ-панели
"""

import os
from flask import Flask, render_template, send_from_directory, jsonify
from flask_login import LoginManager
from flask_jwt_extended import JWTManager

from config import SECRET_KEY, FLASK_HOST, FLASK_PORT
from web.auth import auth_bp
from web.api import api_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['JWT_SECRET_KEY'] = SECRET_KEY

# Инициализация расширений
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

jwt = JWTManager(app)

# Регистрация blueprint'ов
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)

# Статические файлы
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Основные маршруты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/users')
def users_page():
    return render_template('users.html')

@app.route('/admin/users/<int:user_id>')
def user_info_page(user_id):
    return render_template('user_info.html', user_id=user_id)

@app.route('/admin/contests')
def contests_page():
    return render_template('contests.html')

@app.route('/admin/contests/100')
def contest_100_page():
    return render_template('contest_100.html')

@app.route('/admin/contests/150')
def contest_150_page():
    return render_template('contest_150.html')

@app.route('/admin/contests/250')
def contest_250_page():
    return render_template('contest_250.html')

@app.route('/admin/contests/5000')
def contest_5000_page():
    return render_template('contest_5000.html')

@app.route('/admin/applications')
def applications_page():
    return render_template('applications.html')

@app.route('/admin/support')
def support_page():
    return render_template('support.html')

@app.route('/admin/logs')
def logs_page():
    return render_template('logs.html')

# Обработчики ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(401)
def unauthorized_error(error):
    return render_template('401.html'), 401