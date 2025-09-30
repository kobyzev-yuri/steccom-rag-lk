#!/bin/bash
# Скрипт для настройки анализатора изображений

echo "🚀 Настройка анализатора изображений..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python3"
    exit 1
fi

# Устанавливаем зависимости для работы с изображениями
echo "📦 Устанавливаем зависимости для работы с изображениями..."
pip install -r requirements-images.txt

# Создаем файл .env для конфигурации
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Создаем файл конфигурации .env..."
    cat > "$ENV_FILE" << EOF
# Настройки анализатора изображений

# Ollama настройки
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLAVA_MODEL=llava:7b

# ProxyAPI настройки (опционально)
USE_PROXY_API=false
PROXY_API_KEY=your_api_key_here
PROXY_API_PROVIDER=openai

# Модели для разных провайдеров
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-7-sonnet-20250219
GEMINI_MODEL=gemini-1.5-pro

# Настройки анализа
MAX_IMAGE_SIZE_MB=20
ANALYSIS_TIMEOUT=60
ANALYSIS_TEMPERATURE=0.1
ANALYSIS_MAX_TOKENS=1000

# Настройки извлечения изображений
EXTRACT_IMAGES_FROM_PDF=true
MAX_IMAGES_PER_DOCUMENT=10

# Директории
IMAGES_DIR=data/extracted_images
TEMP_DIR=data/temp
EOF
    echo "✅ Файл .env создан"
else
    echo "✅ Файл .env уже существует"
fi

# Создаем директории
echo "📁 Создаем необходимые директории..."
mkdir -p data/extracted_images
mkdir -p data/temp
mkdir -p kb_admin/config

echo ""
echo "🎯 Выберите провайдера для анализа изображений:"
echo "1. Ollama (локальный, бесплатный)"
echo "2. ProxyAPI OpenAI (облачный, платный)"
echo "3. ProxyAPI Anthropic (облачный, платный)"
echo "4. ProxyAPI Gemini (облачный, платный)"
echo "5. Пропустить настройку"

read -p "Выберите вариант (1-5): " choice

case $choice in
    1)
        echo "🔧 Настраиваем Ollama..."
        echo "USE_PROXY_API=false" >> "$ENV_FILE"
        echo ""
        echo "📋 Для завершения настройки Ollama:"
        echo "1. Убедитесь, что Ollama запущен: ollama serve"
        echo "2. Загрузите модель LLaVA: ollama pull llava:7b"
        echo "3. Или запустите: ./setup_llava.sh"
        ;;
    2)
        echo "🔧 Настраиваем ProxyAPI OpenAI..."
        read -p "Введите API ключ ProxyAPI: " api_key
        if [ -n "$api_key" ]; then
            sed -i "s/USE_PROXY_API=false/USE_PROXY_API=true/" "$ENV_FILE"
            sed -i "s/PROXY_API_KEY=your_api_key_here/PROXY_API_KEY=$api_key/" "$ENV_FILE"
            sed -i "s/PROXY_API_PROVIDER=openai/PROXY_API_PROVIDER=openai/" "$ENV_FILE"
            echo "✅ ProxyAPI OpenAI настроен"
        else
            echo "❌ API ключ не введен"
        fi
        ;;
    3)
        echo "🔧 Настраиваем ProxyAPI Anthropic..."
        read -p "Введите API ключ ProxyAPI: " api_key
        if [ -n "$api_key" ]; then
            sed -i "s/USE_PROXY_API=false/USE_PROXY_API=true/" "$ENV_FILE"
            sed -i "s/PROXY_API_KEY=your_api_key_here/PROXY_API_KEY=$api_key/" "$ENV_FILE"
            sed -i "s/PROXY_API_PROVIDER=openai/PROXY_API_PROVIDER=anthropic/" "$ENV_FILE"
            echo "✅ ProxyAPI Anthropic настроен"
        else
            echo "❌ API ключ не введен"
        fi
        ;;
    4)
        echo "🔧 Настраиваем ProxyAPI Gemini..."
        read -p "Введите API ключ ProxyAPI: " api_key
        if [ -n "$api_key" ]; then
            sed -i "s/USE_PROXY_API=false/USE_PROXY_API=true/" "$ENV_FILE"
            sed -i "s/PROXY_API_KEY=your_api_key_here/PROXY_API_KEY=$api_key/" "$ENV_FILE"
            sed -i "s/PROXY_API_PROVIDER=openai/PROXY_API_PROVIDER=gemini/" "$ENV_FILE"
            echo "✅ ProxyAPI Gemini настроен"
        else
            echo "❌ API ключ не введен"
        fi
        ;;
    5)
        echo "⏭️ Настройка пропущена"
        ;;
    *)
        echo "❌ Неверный выбор"
        ;;
esac

echo ""
echo "🎉 Настройка анализатора изображений завершена!"
echo ""
echo "📋 Что было сделано:"
echo "   ✅ Установлены зависимости для работы с изображениями"
echo "   ✅ Создан файл конфигурации .env"
echo "   ✅ Созданы необходимые директории"
echo ""
echo "💡 Следующие шаги:"
echo "   1. Отредактируйте .env файл при необходимости"
echo "   2. Запустите KB Admin для тестирования"
echo "   3. Загрузите PDF с изображениями для анализа"
echo ""
echo "🔗 Полезные ссылки:"
echo "   📖 ProxyAPI: https://proxyapi.ru"
echo "   🦙 Ollama: https://ollama.ai"
echo "   📚 LLaVA: https://github.com/haotian-liu/LLaVA"
