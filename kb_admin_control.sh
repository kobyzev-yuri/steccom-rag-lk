#!/bin/bash
# KB Admin Control Script
# Управление системой KB Admin

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Переходим в корень проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Функции
check_status() {
    if [ -f ".kb_admin.pid" ]; then
        local pid=$(cat .kb_admin.pid)
        if ps -p $pid > /dev/null 2>&1; then
            if curl -s http://localhost:8502/_stcore/health >/dev/null 2>&1; then
                log_success "KB Admin запущен (PID: $pid)"
                log_info "URL: http://localhost:8502"
                return 0
            else
                log_warning "Процесс существует, но сервис не отвечает"
                return 1
            fi
        else
            log_warning "PID файл существует, но процесс не найден"
            rm -f .kb_admin.pid
            return 1
        fi
    else
        log_info "KB Admin не запущен"
        return 1
    fi
}

stop_kb_admin() {
    log_info "Остановка KB Admin..."
    
    if [ -f ".kb_admin.pid" ]; then
        local pid=$(cat .kb_admin.pid)
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                log_warning "Принудительная остановка..."
                kill -9 $pid
            fi
            log_success "KB Admin остановлен"
        else
            log_warning "Процесс уже не существует"
        fi
        rm -f .kb_admin.pid
    else
        log_info "PID файл не найден, попытка остановить по имени процесса..."
        pkill -f "streamlit.*kb_admin/app.py" || log_info "Процессы не найдены"
    fi
}

restart_kb_admin() {
    log_info "Перезапуск KB Admin..."
    stop_kb_admin
    sleep 2
    ./start_kb_admin.sh
}

show_logs() {
    if [ -f "logs/kb_admin.log" ]; then
        log_info "Последние 50 строк логов:"
        echo "----------------------------------------"
        tail -n 50 logs/kb_admin.log
        echo "----------------------------------------"
        log_info "Для отслеживания логов в реальном времени: tail -f logs/kb_admin.log"
    else
        log_warning "Файл логов не найден"
    fi
}

# Основная логика
case "${1:-status}" in
    "start")
        if check_status >/dev/null 2>&1; then
            log_warning "KB Admin уже запущен"
        else
            ./start_kb_admin.sh
        fi
        ;;
    "stop")
        stop_kb_admin
        ;;
    "restart")
        restart_kb_admin
        ;;
    "status")
        check_status
        ;;
    "logs")
        show_logs
        ;;
    "foreground"|"fg")
        log_info "Запуск в режиме переднего плана..."
        ./start_kb_admin.sh --foreground
        ;;
    "clean")
        log_info "Очистка логов и перезапуск..."
        ./start_kb_admin.sh --clean-logs
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|foreground|clean}"
        echo ""
        echo "Команды:"
        echo "  start     - Запустить KB Admin в фоне"
        echo "  stop      - Остановить KB Admin"
        echo "  restart   - Перезапустить KB Admin"
        echo "  status    - Показать статус (по умолчанию)"
        echo "  logs      - Показать последние логи"
        echo "  foreground - Запустить в режиме переднего плана"
        echo "  clean     - Очистить логи и перезапустить"
        exit 1
        ;;
esac




