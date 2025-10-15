#!/usr/bin/env python3
"""
KB Admin - Универсальная система управления базами знаний
Knowledge Base Administration System

Главный файл приложения для управления базами знаний
"""

# Загружаем переменные окружения из config.env ПЕРЕД ВСЕМИ импортами
import os
import sys
from pathlib import Path

# Загружаем переменные окружения из config.env
# Сначала пробуем локальный конфиг KB Admin
config_file = Path(__file__).parent / "config.env"
print(f"🔍 Ищем config.env по пути: {config_file}")

if config_file.exists():
    print("✅ Найден локальный config.env для KB Admin, загружаем переменные...")
    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
                print(f"✅ Загружена переменная: {key.strip()}")
else:
    print("❌ Локальный config.env не найден!")
    # Попробуем общий конфиг
    alt_config = Path(__file__).parent.parent / "config.env"
    print(f"🔍 Пробуем общий config.env: {alt_config}")
    if alt_config.exists():
        print("✅ Найден общий config.env, загружаем переменные...")
        with open(alt_config, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    print(f"✅ Загружена переменная: {key.strip()}")
    else:
        print("❌ config.env не найден ни локально, ни в общем!")

# Убеждаемся, что переменные загружены
print(f"🔧 USE_PROXYAPI: {os.getenv('USE_PROXYAPI')}")
print(f"🔧 PROXYAPI_API_KEY: {os.getenv('PROXYAPI_API_KEY', 'НЕ НАЙДЕН')[:10]}...")
print(f"🔧 PROXYAPI_CHAT_MODEL: {os.getenv('PROXYAPI_CHAT_MODEL')}")
print(f"🔧 PROXYAPI_BASE_URL: {os.getenv('PROXYAPI_BASE_URL')}")

import streamlit as st
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
sys.path.insert(0, str(current_dir))
# Добавляем путь к модулям KB Admin
sys.path.insert(0, str(current_dir / "modules"))
# Добавляем путь к корневым модулям проекта (для совместимости)
sys.path.insert(0, str(current_dir.parent.parent))
# Добавляем путь к корневым модулям
sys.path.insert(0, str(current_dir.parent))

def main():
    """Главная функция приложения"""
    try:
        logger.info("Запуск KB Admin...")
        
        # Импорт и запуск главного интерфейса
        from modules.ui.main_interface import KBAdminInterface
        
        # Создаем и запускаем интерфейс
        interface = KBAdminInterface()
        interface.render_main_page()
        
        logger.info("KB Admin успешно запущен")
        
    except Exception as e:
        st.error(f"Критическая ошибка: {e}")
        logger.error(f"Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()