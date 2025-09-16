#!/bin/bash

# Скрипт для мониторинга логов Streamlit в реальном времени

echo "🔍 Мониторинг логов Streamlit..."
echo "📁 Логи: logs/streamlit.log"
echo "🌐 Приложение: http://localhost:8501"
echo "⏹️  Для остановки нажмите Ctrl+C"
echo ""

# Функция для проверки ошибок
check_errors() {
    local log_file="$1"
    if [ -f "$log_file" ]; then
        # Проверяем на критические ошибки
        if grep -q "ERROR\|CRITICAL\|Exception\|Traceback" "$log_file"; then
            echo "❌ ОБНАРУЖЕНЫ ОШИБКИ:"
            grep -n "ERROR\|CRITICAL\|Exception\|Traceback" "$log_file" | tail -5
            echo ""
        fi
        
        # Проверяем на предупреждения
        if grep -q "WARNING\|DeprecationWarning" "$log_file"; then
            echo "⚠️  ПРЕДУПРЕЖДЕНИЯ:"
            grep -n "WARNING\|DeprecationWarning" "$log_file" | tail -3
            echo ""
        fi
    fi
}

# Основной цикл мониторинга
while true; do
    # Проверяем логи на ошибки
    check_errors "logs/streamlit.log"
    
    # Показываем последние 5 строк логов
    if [ -f "logs/streamlit.log" ]; then
        echo "📝 Последние логи:"
        tail -5 logs/streamlit.log
        echo ""
    fi
    
    # Ждем 5 секунд
    sleep 5
done


