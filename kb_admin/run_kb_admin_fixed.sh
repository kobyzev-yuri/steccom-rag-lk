#!/bin/bash

# KB Admin запуск с правильными путями
echo "🚀 Запуск KB Admin с исправленными путями..."

# Активируем виртуальное окружение
source ../.venv/bin/activate

# Устанавливаем PYTHONPATH для доступа к корневым модулям
export PYTHONPATH="../:$PYTHONPATH"

# Переходим в корневую директорию и запускаем KB Admin
cd ..
streamlit run kb_admin/app.py --server.port 8502 --server.headless true
