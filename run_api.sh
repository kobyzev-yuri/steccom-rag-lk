#!/bin/bash
# Запуск FastAPI сервера для СТЭККОМ Billing API

echo "🚀 Запуск СТЭККОМ Billing API..."

# Активируем виртуальное окружение
source .venv/bin/activate

# Устанавливаем зависимости API если нужно
if [ ! -f ".api_deps_installed" ]; then
    echo "📦 Установка зависимостей API..."
    pip install -r requirements-api.txt
    touch .api_deps_installed
fi

# Запускаем API сервер
echo "🌐 API будет доступен на:"
echo "   📖 Документация: http://localhost:8000/docs"
echo "   🔧 ReDoc: http://localhost:8000/redoc"
echo "   💚 Health check: http://localhost:8000/health"
echo ""

python api/run_api.py
