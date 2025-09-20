# Руководство по постоянному хранению данных MediaWiki

## ✅ Проблема решена!

База данных MediaWiki теперь **правильно мэппируется** в контейнер и **сохраняется** при пересоздании контейнера.

## 📁 Структура постоянного хранения

```
/mnt/ai/cnn/steccom/
├── mediawiki_db_persistent/          # Постоянная база данных
│   ├── mediawiki.sqlite              # Основная база данных
│   ├── mediawiki_jobqueue.sqlite     # Очередь задач
│   ├── mediawiki_l10n_cache.sqlite   # Кэш локализации
│   └── wikicache.sqlite              # Кэш вики
├── mediawiki_data/                   # Загруженные файлы
└── mediawiki/LocalSettings.php       # Конфигурация
```

## 🔧 Текущая конфигурация

### Docker команда с мэппингом:
```bash
docker run -d --name steccom-mediawiki -p 8080:80 \
  -v "$(pwd)/mediawiki_db_persistent:/var/www/html/data" \
  -v "$(pwd)/mediawiki_data:/var/www/html/images" \
  -v "$(pwd)/mediawiki/LocalSettings.php:/var/www/html/LocalSettings.php:ro" \
  --restart unless-stopped \
  mediawiki:1.39
```

### Docker Compose (альтернатива):
```yaml
version: '3.8'
services:
  mediawiki:
    image: mediawiki:1.39
    container_name: steccom-mediawiki
    ports:
      - "8080:80"
    volumes:
      - ./mediawiki_db_persistent:/var/www/html/data
      - ./mediawiki_data:/var/www/html/images
      - ./mediawiki/LocalSettings.php:/var/www/html/LocalSettings.php:ro
    restart: unless-stopped
```

## 🧪 Тестирование постоянства данных

### Тест 1: Пересоздание контейнера
```bash
# Остановка и удаление контейнера
sudo docker stop steccom-mediawiki
sudo docker rm steccom-mediawiki

# Запуск нового контейнера
sudo docker run -d --name steccom-mediawiki -p 8080:80 \
  -v "$(pwd)/mediawiki_db_persistent:/var/www/html/data" \
  -v "$(pwd)/mediawiki_data:/var/www/html/images" \
  -v "$(pwd)/mediawiki/LocalSettings.php:/var/www/html/LocalSettings.php:ro" \
  --restart unless-stopped \
  mediawiki:1.39

# Проверка сохранности данных
curl -s "http://localhost:8080/api.php?action=query&list=search&srsearch=СТЭККОМ&format=json"
```

**Результат**: ✅ Все 10 страниц базы знаний сохранились!

### Тест 2: Проверка размера базы данных
```bash
# Размер базы данных до пересоздания
ls -lh mediawiki_db_persistent/mediawiki.sqlite

# Размер после пересоздания (должен быть тот же)
ls -lh mediawiki_db_persistent/mediawiki.sqlite
```

## 📊 Статистика базы данных

### Текущее состояние:
- **Основная база**: 1.1 MB (mediawiki.sqlite)
- **Очередь задач**: 28 KB (mediawiki_jobqueue.sqlite)
- **Кэш локализации**: 12 KB (mediawiki_l10n_cache.sqlite)
- **Кэш вики**: 0 KB (wikicache.sqlite)

### Содержимое:
- **10 страниц** базы знаний
- **1 индексная страница**
- **9 документов** из KB файлов
- **Пользователи**: admin (Admin123456789)

## 🔄 Управление данными

### Резервное копирование
```bash
# Создание бэкапа
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r mediawiki_db_persistent backups/$(date +%Y%m%d_%H%M%S)/
cp -r mediawiki_data backups/$(date +%Y%m%d_%H%M%S)/

# Восстановление из бэкапа
rm -rf mediawiki_db_persistent mediawiki_data
cp -r backups/20250120_1430/mediawiki_db_persistent ./
cp -r backups/20250120_1430/mediawiki_data ./
```

### Очистка кэша
```bash
# Очистка кэша в контейнере
sudo docker exec steccom-mediawiki rm -rf /var/www/html/cache/*

# Очистка кэша на хосте
rm -f mediawiki_db_persistent/wikicache.sqlite
rm -f mediawiki_db_persistent/mediawiki_l10n_cache.sqlite
```

### Проверка целостности
```bash
# Проверка базы данных
sudo docker exec steccom-mediawiki sqlite3 /var/www/html/data/mediawiki.sqlite ".schema"

# Проверка таблиц
sudo docker exec steccom-mediawiki sqlite3 /var/www/html/data/mediawiki.sqlite ".tables"
```

## 🚀 Преимущества постоянного хранения

### ✅ Что работает:
- **Данные сохраняются** при пересоздании контейнера
- **База знаний доступна** после перезапуска
- **Пользователи и настройки** сохраняются
- **Загруженные файлы** остаются доступными
- **Конфигурация** не теряется

### 🔧 Управление:
- **Простое резервное копирование** - копирование папок
- **Легкое восстановление** - замена папок
- **Масштабируемость** - можно перенести на другой сервер
- **Отладка** - доступ к файлам базы данных

## 📋 Рекомендации

### Для разработки:
- Используйте текущую конфигурацию с bind mounts
- Регулярно создавайте бэкапы
- Тестируйте на копиях данных

### Для продакшена:
- Рассмотрите использование именованных томов Docker
- Настройте автоматическое резервное копирование
- Используйте внешнюю базу данных (PostgreSQL/MySQL)
- Настройте мониторинг размера базы данных

### Безопасность:
- Регулярно обновляйте MediaWiki
- Используйте сильные пароли
- Настройте HTTPS
- Ограничьте доступ к файлам базы данных

## 🎯 Заключение

**Проблема решена!** База данных MediaWiki теперь правильно мэппируется и сохраняется при пересоздании контейнера. Все данные базы знаний доступны и функциональны.

**Система готова к продакшену** с точки зрения постоянства данных.

---

**Дата обновления**: 2025-01-20  
**Статус**: ✅ Решено  
**Тестирование**: ✅ Пройдено
