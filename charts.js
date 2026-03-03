/**
 * SURO Admin Panel - Charts and Graphs
 * Использует Chart.js для визуализации данных
 */

class ChartsManager {
    constructor() {
        this.charts = {};
    }

    /**
     * Инициализация графика пользователей
     */
    initUsersChart(canvasId, data) {
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        this.charts.users = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Новые пользователи',
                    data: data.users || [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: '#334155',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    },
                    y: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            stepSize: 1
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Инициализация графика заявок по типам
     */
    initApplicationsPieChart(canvasId, data) {
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

        this.charts.applicationsPie = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: colors.slice(0, data.labels?.length || 0),
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f1f5f9',
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: '#334155',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    /**
     * Инициализация графика заявок по дням
     */
    initApplicationsChart(canvasId, data) {
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        this.charts.applications = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Всего заявок',
                        data: data.total || [],
                        backgroundColor: '#3b82f6',
                        borderRadius: 4
                    },
                    {
                        label: 'Одобрено',
                        data: data.approved || [],
                        backgroundColor: '#10b981',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f1f5f9'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: '#334155',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    },
                    y: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            stepSize: 1
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Инициализация графика выплат
     */
    initPaymentsChart(canvasId, data) {
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        this.charts.payments = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Выплаты (₽)',
                    data: data.amounts || [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#94a3b8',
                        borderColor: '#334155',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `Выплачено: ${context.raw.toLocaleString()}₽`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    },
                    y: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) {
                                return value.toLocaleString() + '₽';
                            }
                        },
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Обновление данных графика
     */
    updateChart(chartName, newData) {
        const chart = this.charts[chartName];
        if (!chart) return;

        if (newData.labels) {
            chart.data.labels = newData.labels;
        }

        if (newData.datasets) {
            chart.data.datasets = newData.datasets;
        }

        chart.update();
    }

    /**
     * Загрузка данных с API и обновление графиков
     */
    async refreshAllCharts() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();

            if (!data.success) return;

            // Обновляем график пользователей
            if (this.charts.users && data.data.users_by_day) {
                this.updateChart('users', {
                    labels: data.data.users_by_day.labels,
                    datasets: [{
                        ...this.charts.users.data.datasets[0],
                        data: data.data.users_by_day.values
                    }]
                });
            }

            // Обновляем график заявок по типам
            if (this.charts.applicationsPie && data.data.by_type) {
                this.updateChart('applicationsPie', {
                    labels: data.data.by_type.map(t => t.type + '₽'),
                    datasets: [{
                        ...this.charts.applicationsPie.data.datasets[0],
                        data: data.data.by_type.map(t => t.total)
                    }]
                });
            }

        } catch (error) {
            console.error('Error refreshing charts:', error);
        }
    }

    /**
     * Создание спарклайна (маленького графика)
     */
    createSparkline(elementId, data, color = '#3b82f6') {
        const canvas = document.getElementById(elementId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);

        if (!data || data.length < 2) return;

        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;

        const points = data.map((value, index) => {
            const x = (index / (data.length - 1)) * width;
            const y = height - ((value - min) / range) * height;
            return { x, y };
        });

        // Рисуем линию
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.moveTo(points[0].x, points[0].y);

        for (let i = 1; i < points.length; i++) {
            ctx.lineTo(points[i].x, points[i].y);
        }

        ctx.stroke();

        // Рисуем точки
        ctx.fillStyle = color;
        points.forEach(point => {
            ctx.beginPath();
            ctx.arc(point.x, point.y, 2, 0, Math.PI * 2);
            ctx.fill();
        });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.chartsManager = new ChartsManager();

    // Если есть графики на странице, загружаем данные
    if (document.getElementById('usersChart') || 
        document.getElementById('applicationsChart') ||
        document.getElementById('paymentsChart')) {
        
        fetch('/api/stats')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // Инициализируем графики с полученными данными
                    if (document.getElementById('usersChart')) {
                        window.chartsManager.initUsersChart('usersChart', {
                            labels: data.data.users_by_day?.labels || [],
                            users: data.data.users_by_day?.values || []
                        });
                    }

                    if (document.getElementById('applicationsPieChart') && data.data.by_type) {
                        window.chartsManager.initApplicationsPieChart('applicationsPieChart', {
                            labels: data.data.by_type.map(t => t.type + '₽'),
                            values: data.data.by_type.map(t => t.total)
                        });
                    }

                    if (document.getElementById('paymentsChart') && data.data.payments_by_day) {
                        window.chartsManager.initPaymentsChart('paymentsChart', {
                            labels: data.data.payments_by_day.labels,
                            amounts: data.data.payments_by_day.values
                        });
                    }
                }
            });

        // Обновляем каждые 5 минут
        setInterval(() => {
            window.chartsManager?.refreshAllCharts();
        }, 300000);
    }
});