#!/bin/bash
# Скрипт для установки и настройки LLaVA в Ollama

echo "🚀 Настройка LLaVA для анализа изображений..."

# Проверяем, что Ollama запущен
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama не запущен. Запустите Ollama: ollama serve"
    exit 1
fi

echo "✅ Ollama запущен"

# Список доступных моделей LLaVA
LLAVA_MODELS=(
    "llava-phi3:latest"
    "llava:7b"
    "llava:13b" 
    "llava:34b"
    "llava:7b-v1.6"
    "llava:13b-v1.6"
    "llava:34b-v1.6"
)

echo "📋 Доступные модели LLaVA:"
for i in "${!LLAVA_MODELS[@]}"; do
    echo "  $((i+1)). ${LLAVA_MODELS[$i]}"
done

# Выбор модели
echo ""
read -p "Выберите модель LLaVA (1-${#LLAVA_MODELS[@]}) или нажмите Enter для llava-phi3:latest: " choice

if [[ -z "$choice" ]]; then
    selected_model="llava-phi3:latest"
else
    if [[ "$choice" -ge 1 && "$choice" -le "${#LLAVA_MODELS[@]}" ]]; then
        selected_model="${LLAVA_MODELS[$((choice-1))]}"
    else
        echo "❌ Неверный выбор. Используется llava-phi3:latest"
        selected_model="llava-phi3:latest"
    fi
fi

echo "📥 Загружаем модель: $selected_model"
echo "⏳ Это может занять несколько минут..."

# Загружаем модель
if ollama pull "$selected_model"; then
    echo "✅ Модель $selected_model успешно загружена"
else
    echo "❌ Ошибка загрузки модели $selected_model"
    exit 1
fi

# Проверяем, что модель доступна
echo "🔍 Проверяем доступность модели..."
if curl -s http://localhost:11434/api/tags | grep -q "$selected_model"; then
    echo "✅ Модель $selected_model доступна"
else
    echo "❌ Модель $selected_model не найдена"
    exit 1
fi

# Тестируем модель
echo "🧪 Тестируем модель..."
test_response=$(curl -s -X POST http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{
        "model": "'$selected_model'",
        "prompt": "Привет! Можешь ли ты анализировать изображения?",
        "stream": false
    }' | jq -r '.response' 2>/dev/null)

if [[ -n "$test_response" ]]; then
    echo "✅ Модель отвечает корректно"
    echo "📝 Ответ модели: $test_response"
else
    echo "⚠️ Модель загружена, но тест не прошел"
fi

echo ""
echo "🎉 Настройка LLaVA завершена!"
echo "📋 Информация:"
echo "   Модель: $selected_model"
echo "   API: http://localhost:11434"
echo "   Статус: Готова к использованию"
echo ""
echo "💡 Теперь вы можете:"
echo "   1. Анализировать изображения в KB Admin"
echo "   2. Извлекать изображения из PDF"
echo "   3. Получать описания изображений с помощью LLaVA"
echo ""
echo "🔧 Для изменения модели отредактируйте:"
echo "   kb_admin/modules/core/llava_analyzer.py"
echo "   Строка: self.model_name = \"$selected_model\""
