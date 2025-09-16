#!/bin/bash

# Продвинутый мониторинг логов в реальном времени

echo "🚀 Запуск мониторинга логов Streamlit..."
echo "📊 Статус: $(date)"
echo ""

# Цвета для вывода
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для цветного вывода
print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
}

# Проверяем, запущен ли Streamlit
check_streamlit() {
    if pgrep -f "streamlit run app.py" > /dev/null; then
        print_success "Streamlit запущен (PID: $(pgrep -f 'streamlit run app.py'))"
        return 0
    else
        print_error "Streamlit НЕ запущен!"
        return 1
    fi
}

# Основной мониторинг
monitor_logs() {
    local log_file="logs/streamlit.log"
    
    if [ ! -f "$log_file" ]; then
        print_error "Файл логов не найден: $log_file"
        return 1
    fi
    
    print_info "Мониторинг файла: $log_file"
    print_info "Для остановки нажмите Ctrl+C"
    echo ""
    
    # Используем tail -f для мониторинга в реальном времени
    tail -f "$log_file" | while read line; do
        timestamp=$(date '+%H:%M:%S')
        
        # Проверяем тип сообщения
        if echo "$line" | grep -qi "error\|exception\|traceback"; then
            print_error "[$timestamp] $line"
        elif echo "$line" | grep -qi "warning\|deprecation"; then
            print_warning "[$timestamp] $line"
        elif echo "$line" | grep -qi "success\|initialized\|ready"; then
            print_success "[$timestamp] $line"
        else
            echo -e "${BLUE}[$timestamp]${NC} $line"
        fi
    done
}

# Запуск мониторинга
echo "🔍 Проверка статуса Streamlit..."
if check_streamlit; then
    echo ""
    monitor_logs
else
    echo "💡 Запустите Streamlit командой: streamlit run app.py"
    exit 1
fi


