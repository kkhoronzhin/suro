# -*- coding: utf-8 -*-
"""
REST API для админ-панели
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import sqlite3

from bot.services.database import db
from bot.services.logger import api_logger
from bot.services.subscription import _subscription_cache

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/stats')
@login_required
def get_stats():
    """Получение статистики"""
    
    try:
        # Общая статистика
        total_users = db.get_total_users()
        total_applications = db.get_total_applications()
        total_paid = db.get_total_paid()
        
        # Статистика за сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        today_users = db.get_users_by_date(today)
        today_applications = db.get_applications_by_date(today)
        
        # Распределение по типам
        by_type = db.get_applications_by_type()
        
        # Активные диалоги поддержки
        active_support = db.get_active_support_requests()
        
        return jsonify({
            'success': True,
            'data': {
                'total': {
                    'users': total_users,
                    'applications': total_applications,
                    'paid': total_paid
                },
                'today': {
                    'users': today_users,
                    'applications': today_applications
                },
                'by_type': by_type,
                'support': {
                    'active': active_support
                }
            }
        })
    except Exception as e:
        api_logger.error(f"Error in get_stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/applications')
@login_required
def get_applications():
    """Получение заявок с фильтрацией"""
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        status = request.args.get('status')
        app_type = request.args.get('type')
        user_id = request.args.get('user_id')
        
        applications = db.get_applications_filtered(
            page=page,
            per_page=per_page,
            status=status,
            type=app_type,
            user_id=user_id
        )
        
        total = db.count_applications_filtered(
            status=status,
            type=app_type,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'data': {
                'applications': applications,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        api_logger.error(f"Error in get_applications: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/applications/<int:app_id>/status', methods=['POST'])
@login_required
def update_application_status(app_id):
    """Обновление статуса заявки"""
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in [0, 1, 2]:  # 0 - новая, 1 - одобрена, 2 - отклонена
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        db.update_application_status(app_id, new_status)
        
        api_logger.info(
            f"Admin {current_user.id} updated application {app_id} to status {new_status}"
        )
        
        return jsonify({'success': True})
    except Exception as e:
        api_logger.error(f"Error updating application {app_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/users')
@login_required
def get_users():
    """Получение списка пользователей"""
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search')
        
        users = db.get_users_filtered(
            page=page,
            per_page=per_page,
            search=search
        )
        
        total = db.count_users_filtered(search=search)
        
        return jsonify({
            'success': True,
            'data': {
                'users': users,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        api_logger.error(f"Error in get_users: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/users/<int:user_id>')
@login_required
def get_user_details(user_id):
    """Детальная информация о пользователе"""
    
    try:
        user = db.get_user_by_id(user_id)
        applications = db.get_user_applications(user_id)
        support_requests = db.get_user_support_requests(user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'applications': applications,
                'support_requests': support_requests
            }
        })
    except Exception as e:
        api_logger.error(f"Error getting user {user_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/support/requests')
@login_required
def get_support_requests():
    """Получение обращений в поддержку"""
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        status = request.args.get('status')  # active, closed
        
        requests = db.get_support_requests_filtered(
            page=page,
            per_page=per_page,
            status=status
        )
        
        total = db.count_support_requests_filtered(status=status)
        
        return jsonify({
            'success': True,
            'data': {
                'requests': requests,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        api_logger.error(f"Error in get_support_requests: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """Очистка кэша (только для админов)"""
    
    try:
        # Проверяем права
        if current_user.admin_level < 2:
            return jsonify({'success': False, 'error': 'Insufficient permissions'}), 403
        
        from bot.services.subscription import clear_subscription_cache
        clear_subscription_cache()
        
        return jsonify({'success': True})
    except Exception as e:
        api_logger.error(f"Error clearing cache: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/logs/<log_type>')
@login_required
def get_logs(log_type):
    """Получение логов"""
    
    try:
        lines = int(request.args.get('lines', 100))
        
        log_files = {
            'bot': 'logs/bot.log',
            'errors': 'logs/bot_errors.log',
            'api': 'logs/api.log'
        }
        
        if log_type not in log_files:
            return jsonify({'success': False, 'error': 'Invalid log type'}), 400
        
        log_path = log_files[log_type]
        
        if not os.path.exists(log_path):
            return jsonify({'success': True, 'data': {'logs': []}})
        
        # Читаем последние N строк
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': last_lines,
                'total': len(all_lines)
            }
        })
    except Exception as e:
        api_logger.error(f"Error getting logs: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    api_logger.error(f"Internal server error: {error}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500