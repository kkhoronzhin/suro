/**
 * SURO Admin Panel 2025 - Main JavaScript
 */

// Глобальные функции для уведомлений
const Notifications = {
    show(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notification-container');
        if (!container) {
            this.createContainer();
        }
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.innerHTML = `
            <i class="fas ${this.getIcon(type)}"></i>
            <span>${message}</span>
            <button class="close-btn" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        document.getElementById('notification-container').appendChild(notification);
        
        if (duration > 0) {
            setTimeout(() => {
                notification.remove();
            }, duration);
        }
    },
    
    success(message, duration = 5000) {
        this.show(message, 'success', duration);
    },
    
    error(message, duration = 5000) {
        this.show(message, 'danger', duration);
    },
    
    warning(message, duration = 5000) {
        this.show(message, 'warning', duration);
    },
    
    info(message, duration = 5000) {
        this.show(message, 'info', duration);
    },
    
    createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 350px;
        `;
        document.body.appendChild(container);
    },
    
    getIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            danger: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
};

// Загрузка данных с API
const API = {
    baseUrl: '/api',
    
    async get(endpoint, params = {}) {
        const url = new URL(this.baseUrl + endpoint, window.location.origin);
        Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
        
        try {
            const response = await fetch(url);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Unknown error');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            Notifications.error('Ошибка загрузки данных');
            throw error;
        }
    },
    
    async post(endpoint, data = {}) {
        try {
            const response = await fetch(this.baseUrl + endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Unknown error');
            }
            
            return result;
        } catch (error) {
            console.error('API Error:', error);
            Notifications.error('Ошибка отправки данных');
            throw error;
        }
    },
    
    async delete(endpoint) {
        try {
            const response = await fetch(this.baseUrl + endpoint, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Unknown error');
            }
            
            return result;
        } catch (error) {
            console.error('API Error:', error);
            Notifications.error('Ошибка удаления');
            throw error;
        }
    }
};

// Форматирование дат
const DateFormatter = {
    format(date, format = 'short') {
        const d = new Date(date);
        
        if (isNaN(d.getTime())) {
            return 'Invalid date';
        }
        
        const formats = {
            short: d.toLocaleDateString('ru-RU'),
            long: d.toLocaleString('ru-RU'),
            time: d.toLocaleTimeString('ru-RU'),
            datetime: d.toLocaleString('ru-RU')
        };
        
        return formats[format] || formats.short;
    },
    
    relative(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) return `${days} дн. назад`;
        if (hours > 0) return `${hours} ч. назад`;
        if (minutes > 0) return `${minutes} мин. назад`;
        return 'только что';
    }
};

// Работа с модальными окнами
const Modal = {
    show(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },
    
    hide(id) {
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    },
    
    showConfirm(options) {
        const {
            title = 'Подтверждение',
            message = 'Вы уверены?',
            onConfirm = () => {},
            onCancel = () => {}
        } = options;
        
        const modalId = 'confirm-modal-' + Date.now();
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">${title}</h3>
                    <button class="modal-close" onclick="Modal.hide('${modalId}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-actions">
                    <button class="btn" onclick="Modal.hide('${modalId}'); onCancel();">Отмена</button>
                    <button class="btn btn-danger" onclick="Modal.hide('${modalId}'); onConfirm();">Подтвердить</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('active'), 10);
    }
};

// Копирование в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        Notifications.success('Скопировано в буфер обмена');
    }).catch(() => {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        Notifications.success('Скопировано в буфер обмена');
    });
}

// Дебаунс для поиска
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    
    // Мобильное меню
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }
    
    // Закрытие модалок по клику вне
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Автоматическое скрытие уведомлений
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
    
    console.log('SURO Admin Panel initialized');
});