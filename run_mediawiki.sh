#!/bin/bash

echo "🚀 Запуск MediaWiki для СТЭККОМ..."

# Проверяем, запущен ли Docker daemon
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon не запущен. Запускаем..."
    sudo systemctl start docker
    sleep 3
fi

# Проверяем, есть ли образ MediaWiki
if ! docker images | grep -q mediawiki; then
    echo "📦 Загружаем образ MediaWiki..."
    docker pull mediawiki:1.39
fi

# Создаём директорию для данных MediaWiki
mkdir -p ./mediawiki_data

# Запускаем MediaWiki контейнер
echo "🌐 Запускаем MediaWiki на порту 8080..."
docker run -d \
    --name steccom-mediawiki \
    -p 8080:80 \
    -v "$(pwd)/mediawiki_data:/var/www/html/images" \
    -v "$(pwd)/mediawiki/LocalSettings.php:/var/www/html/LocalSettings.php:ro" \
    -e MEDIAWIKI_DB_TYPE=sqlite \
    -e MEDIAWIKI_DB_NAME=mediawiki \
    -e MEDIAWIKI_SITE_NAME="СТЭККОМ Wiki" \
    -e MEDIAWIKI_SITE_LANG=ru \
    -e MEDIAWIKI_ADMIN_USER=admin \
    -e MEDIAWIKI_ADMIN_PASS=admin123 \
    --restart unless-stopped \
    mediawiki:1.39

echo "✅ MediaWiki запущен!"
echo "🌐 Доступен по адресу: http://localhost:8080"
echo "👤 Админ: admin / admin123"
echo "📖 API: http://localhost:8080/w/api.php"
echo ""
echo "Для остановки: docker stop steccom-mediawiki"
echo "Для удаления: docker rm steccom-mediawiki"
