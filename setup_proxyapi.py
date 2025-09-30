#!/usr/bin/env python3
"""
Скрипт для настройки ProxyAPI ключей
"""

import os

def setup_proxyapi():
    """Настройка ProxyAPI ключей"""
    print("🔧 Настройка ProxyAPI для AI Billing System")
    print("=" * 50)
    
    # Получаем текущие настройки
    config_file = 'config.env'
    
    # Читаем существующий файл
    config = {}
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    # Запрашиваем настройки у пользователя
    print("\n📝 Введите настройки ProxyAPI:")
    
    base_url = input(f"Base URL [{config.get('PROXYAPI_BASE_URL', 'https://api.proxyapi.ru/openai/v1')}]: ").strip()
    if not base_url:
        base_url = config.get('PROXYAPI_BASE_URL', 'https://api.proxyapi.ru/openai/v1')
    
    api_key = input(f"API Key [{config.get('PROXYAPI_API_KEY', 'your_api_key_here')}]: ").strip()
    if not api_key:
        api_key = config.get('PROXYAPI_API_KEY', 'your_api_key_here')
    
    model = input(f"Model [{config.get('PROXYAPI_CHAT_MODEL', 'gpt-4o')}]: ").strip()
    if not model:
        model = config.get('PROXYAPI_CHAT_MODEL', 'gpt-4o')
    
    use_proxyapi = input(f"Use ProxyAPI? (y/n) [{'y' if config.get('USE_PROXYAPI', 'true') == 'true' else 'n'}]: ").strip().lower()
    if not use_proxyapi:
        use_proxyapi = 'y' if config.get('USE_PROXYAPI', 'true') == 'true' else 'n'
    
    # Обновляем конфигурацию
    config.update({
        'PROXYAPI_BASE_URL': base_url,
        'PROXYAPI_API_KEY': api_key,
        'PROXYAPI_CHAT_MODEL': model,
        'USE_PROXYAPI': 'true' if use_proxyapi in ['y', 'yes', 'true'] else 'false',
        'OLLAMA_BASE_URL': config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    })
    
    # Записываем в файл
    with open(config_file, 'w') as f:
        f.write("# ProxyAPI Configuration\n")
        f.write(f"PROXYAPI_BASE_URL={config['PROXYAPI_BASE_URL']}\n")
        f.write(f"PROXYAPI_API_KEY={config['PROXYAPI_API_KEY']}\n")
        f.write(f"PROXYAPI_CHAT_MODEL={config['PROXYAPI_CHAT_MODEL']}\n")
        f.write(f"USE_PROXYAPI={config['USE_PROXYAPI']}\n")
        f.write("\n# Ollama Configuration\n")
        f.write(f"OLLAMA_BASE_URL={config['OLLAMA_BASE_URL']}\n")
    
    print(f"\n✅ Настройки сохранены в {config_file}")
    print("\n📋 Текущие настройки:")
    print(f"   Base URL: {config['PROXYAPI_BASE_URL']}")
    print(f"   API Key: {'*' * len(config['PROXYAPI_API_KEY']) if config['PROXYAPI_API_KEY'] != 'your_api_key_here' else 'НЕ УСТАНОВЛЕН'}")
    print(f"   Model: {config['PROXYAPI_CHAT_MODEL']}")
    print(f"   Use ProxyAPI: {config['USE_PROXYAPI']}")
    
    if config['PROXYAPI_API_KEY'] == 'your_api_key_here':
        print("\n⚠️  ВНИМАНИЕ: API Key не установлен!")
        print("   Замените 'your_api_key_here' на ваш реальный ключ ProxyAPI")
    
    print("\n🚀 Теперь можно запускать AI Billing System:")
    print("   streamlit run ai_billing/app.py --server.port 8501")

if __name__ == "__main__":
    setup_proxyapi()
