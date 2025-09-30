#!/usr/bin/env python3
"""
KB Admin - Универсальная система управления базами знаний
Knowledge Base Administration System

Главный файл приложения для управления базами знаний
"""

import streamlit as st
import os
import sys
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kb_admin.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Добавляем путь к модулям
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def main():
    """Главная функция приложения"""
    try:
        logger.info("Запуск KB Admin...")
        
        # Импорт главного интерфейса
        from modules.ui.main_interface import KBAdminInterface
        
        # Создание и запуск интерфейса
        interface = KBAdminInterface()
        interface.render_main_page()
        
        logger.info("KB Admin успешно запущен")
        
    except ImportError as e:
        st.error(f"Ошибка импорта модулей: {e}")
        logger.error(f"Import error: {e}")
        
        # Показываем информацию о проблеме
        st.markdown("""
        ## 🔧 Устранение неполадок
        
        Если вы видите эту ошибку, проверьте:
        
        1. **Установлены ли зависимости:**
           ```bash
           pip install -r requirements.txt
           ```
        
        2. **Правильно ли настроена структура проекта:**
           ```
           kb_admin/
           ├── modules/
           │   ├── core/
           │   ├── ui/
           │   ├── testing/
           │   └── ...
           ```
        
        3. **Доступны ли необходимые файлы:**
           - `modules/ui/main_interface.py`
           - `modules/core/kb_manager.py`
           - И другие модули
        
        **Для получения помощи обратитесь к администратору системы.**
        """)
        
    except Exception as e:
        st.error(f"Критическая ошибка: {e}")
        logger.error(f"Critical error: {e}")
        
        # Показываем информацию об ошибке
        st.markdown("""
        ## ❌ Критическая ошибка
        
        Произошла непредвиденная ошибка. Пожалуйста:
        
        1. **Проверьте логи** в файле `kb_admin.log`
        2. **Перезапустите приложение**
        3. **Обратитесь к администратору** если проблема повторяется
        
        **Детали ошибки:** `{error}`
        """.format(error=str(e)))

if __name__ == "__main__":
    main()
