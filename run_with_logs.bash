#!/bin/bash

# Активируем виртуальное окружение
source .venv/bin/activate

# Создаем директорию для логов если её нет
mkdir -p logs

# Запускаем Streamlit с логированием
streamlit run app.py 2>&1 | tee logs/streamlit.log
