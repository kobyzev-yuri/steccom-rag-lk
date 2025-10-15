#!/bin/bash
# KB Admin Launcher
# Удобный скрипт для запуска системы управления базами знаний

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Заголовок
echo -e "${BLUE}"
echo "🧠 KB Admin - Система управления базами знаний"
echo "=============================================="
echo -e "${NC}"

# Переходим в корневую директорию проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info "Рабочая директория: $(pwd)"

# Проверка виртуального окружения
if [ ! -d ".venv" ]; then
    log_error "Виртуальное окружение не найдено в .venv"
    log_info "Создаю виртуальное окружение..."
    python3 -m venv .venv
    log_success "Виртуальное окружение создано"
fi

# Активация виртуального окружения
log_info "Активация виртуального окружения..."
source .venv/bin/activate

# Проверка установки зависимостей
if [ ! -f ".venv/.deps_installed" ]; then
    log_info "Установка зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch .venv/.deps_installed
    log_success "Зависимости установлены"
else
    log_info "Зависимости уже установлены"
fi

# Проверка существования app.py
if [ ! -f "kb_admin/app.py" ]; then
    log_error "Файл kb_admin/app.py не найден!"
    exit 1
fi

# Создание директорий для логов
mkdir -p logs

# Проверка занятости порта 8502
if lsof -Pi :8502 -sTCP:LISTEN -t >/dev/null 2>&1; then
    log_warning "Порт 8502 уже занят"
    log_info "Попытка остановить существующий процесс..."
    pkill -f "streamlit.*kb_admin/app.py" || true
    sleep 2
    if lsof -Pi :8502 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "Не удалось освободить порт 8502"
        log_info "Попробуйте: sudo lsof -ti:8502 | xargs kill -9"
        exit 1
    fi
fi

# Установка PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"

# Очистка старых логов (опционально)
if [ "$1" = "--clean-logs" ]; then
    log_info "Очистка старых логов..."
    > logs/kb_admin.log
fi

# Запуск приложения
log_info "Запуск KB Admin на порту 8502..."

# Проверяем режим запуска
if [ "$1" = "--foreground" ] || [ "$1" = "-f" ]; then
    log_info "Запуск в режиме переднего плана..."
    streamlit run kb_admin/app.py --server.port 8502 --server.address 0.0.0.0
else
    log_info "Запуск в фоновом режиме..."
    nohup streamlit run kb_admin/app.py --server.port 8502 --server.address 0.0.0.0 --server.headless true > logs/kb_admin.log 2>&1 &
    KB_PID=$!
    echo $KB_PID > .kb_admin.pid
    
    # Ждем запуска
    log_info "Ожидание запуска сервиса..."
    for i in {1..10}; do
        if curl -s http://localhost:8502/_stcore/health >/dev/null 2>&1; then
            log_success "KB Admin успешно запущен!"
            log_success "PID: $KB_PID"
            log_success "URL: http://localhost:8502"
            log_info "Логи: tail -f logs/kb_admin.log"
            log_info "Остановка: kill $KB_PID"
            exit 0
        fi
        sleep 1
    done
    
    log_error "Не удалось запустить KB Admin"
    log_info "Проверьте логи: tail -n 50 logs/kb_admin.log"
    exit 1
fi
