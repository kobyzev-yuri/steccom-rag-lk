# Настройка базы знаний MediaWiki

## Обзор

Этот документ описывает процесс настройки и управления базой знаний в MediaWiki для системы СТЭККОМ.

## Компоненты базы знаний

### 1. Существующие KB файлы
- **docs/kb/ui_*.json** - документация пользовательского интерфейса
- **docs/kb/legacy_reglament_*.json** - регламенты и процедуры

### 2. Скрипты управления
- **scripts/upload_kb_to_mediawiki.py** - загрузка KB в MediaWiki
- **scripts/generate_knowledge_base.py** - экспорт из MediaWiki
- **scripts/publish_kb_to_wiki.py** - публикация отдельных файлов

## Настройка MediaWiki

### 1. Первоначальная настройка

После запуска MediaWiki контейнера:

1. Откройте http://localhost:8080
2. Выберите язык: **Русский**
3. Настройте базу данных:
   - Тип: **SQLite**
   - Имя: **mediawiki**
4. Создайте администратора:
   - Имя: **admin**
   - Пароль: **admin123**
5. Завершите установку

### 2. Настройка пространства имен

1. Войдите как администратор
2. Перейдите в **Special:AllMessages**
3. Найдите **Namespace:СТЭККОМ**
4. Установите значение: **СТЭККОМ**

## Загрузка базы знаний

### Вариант 1: Через скрипт (рекомендуется)

```bash
# Активация виртуального окружения
source .venv/bin/activate

# Загрузка всех KB файлов
python3 scripts/upload_kb_to_mediawiki.py \
  --wiki-url http://localhost:8080/api.php \
  --username admin \
  --password admin123 \
  --create-index

# Загрузка конкретного файла
python3 scripts/upload_kb_to_mediawiki.py \
  --wiki-url http://localhost:8080/api.php \
  --username admin \
  --password admin123 \
  --kb-file docs/kb/ui_capabilities.json
```

### Вариант 2: Через API

```bash
# Получение токена
python3 get_token.py

# Публикация через API
TOKEN="your_token" ./wiki.bash publish \
  --user admin --pass admin123 \
  --glob "docs/kb/*.json"
```

### Вариант 3: Через Streamlit интерфейс

1. Откройте Streamlit приложение
2. Перейдите в **🔧 Админ-панель**
3. Выберите **MediaWiki Integration**
4. Настройте подключение:
   - URL: `http://localhost:8080/api.php`
   - Пользователь: `admin`
   - Пароль: `admin123`
5. Нажмите **📚 Публиковать все KB**

## Структура базы знаний в MediaWiki

### Пространство имен: СТЭККОМ

```
СТЭККОМ:База знаний (индексная страница)
├── СТЭККОМ:Возможности интерфейса личного кабинета
├── СТЭККОМ:Руководство пользователя
├── СТЭККОМ:Примеры использования
├── СТЭККОМ:Техническая документация
├── СТЭККОМ:Устранение неполадок
├── СТЭККОМ:Регламент GPS-трекинга
├── СТЭККОМ:Регламент мониторинга
├── СТЭККОМ:Регламент SBD (русский)
└── СТЭККОМ:Регламент SBD (английский)
```

### Формат страниц

Каждая страница содержит:
- **Метаданные**: аудитория, область, статус
- **Источник**: файл, указатель
- **Содержимое**: структурированные секции
- **Информация о публикации**: дата, источник

## Управление базой знаний

### Добавление новых документов

1. **Создайте KB файл** в формате JSON:
```json
[
  {
    "title": "Название документа",
    "audience": ["user", "admin"],
    "scope": ["billing", "reports"],
    "status": "reference",
    "content": [
      {
        "title": "Раздел 1",
        "text": "Содержимое раздела..."
      }
    ]
  }
]
```

2. **Загрузите в MediaWiki**:
```bash
python3 scripts/upload_kb_to_mediawiki.py \
  --wiki-url http://localhost:8080/api.php \
  --username admin --password admin123 \
  --kb-file path/to/new_document.json
```

### Обновление существующих документов

1. **Отредактируйте KB файл**
2. **Перезагрузите в MediaWiki** (скрипт автоматически обновит страницу)

### Экспорт из MediaWiki

```bash
# Экспорт всей базы знаний
python3 scripts/generate_knowledge_base.py \
  --wiki-url http://localhost:8080/api.php \
  --username admin --password admin123 \
  --output docs/kb/exported_knowledge_base.json

# Экспорт конкретных страниц
python3 scripts/generate_knowledge_base.py \
  --wiki-url http://localhost:8080/api.php \
  --username admin --password admin123 \
  --pages "СТЭККОМ:Руководство пользователя" "СТЭККОМ:Техническая документация"
```

## Интеграция с системой

### API Endpoints

- **POST /wiki/publish** - публикация KB в MediaWiki
- **GET /wiki/test-connection** - тест подключения к MediaWiki

### Использование в коде

```python
from modules.integrations import MediaWikiClient, KBToWikiPublisher

# Подключение к MediaWiki
client = MediaWikiClient(
    wiki_url="http://localhost:8080/api.php",
    username="admin",
    password="admin123"
)

# Публикация KB
publisher = KBToWikiPublisher(client)
results = publisher.publish_all_kb_files("docs/kb", "СТЭККОМ")
```

## Мониторинг и обслуживание

### Проверка статуса

```bash
# Проверка MediaWiki
curl -I http://localhost:8080/

# Проверка API
curl http://localhost:8080/api.php

# Проверка базы данных
sudo docker exec steccom-mediawiki sqlite3 /var/www/html/data/mediawiki.sqlite ".tables"
```

### Резервное копирование

```bash
# Бэкап базы данных MediaWiki
sudo docker exec steccom-mediawiki sqlite3 /var/www/html/data/mediawiki.sqlite ".backup /var/www/html/backup.sqlite"

# Бэкап KB файлов
tar -czf kb_backup_$(date +%Y%m%d).tar.gz docs/kb/
```

### Очистка и пересоздание

```bash
# Остановка MediaWiki
sudo docker stop steccom-mediawiki

# Удаление контейнера
sudo docker rm steccom-mediawiki

# Пересоздание (по инструкции установки)
sudo docker run -d --name steccom-mediawiki -p 8080:80 mediawiki:1.39
```

## Устранение неполадок

### Проблемы с аутентификацией

```bash
# Проверка подключения
curl "http://localhost:8080/api.php?action=query&meta=siteinfo&format=json"

# Проверка пользователя
curl "http://localhost:8080/api.php?action=query&list=users&ususers=admin&format=json"
```

### Проблемы с правами доступа

```bash
# Исправление прав в контейнере
sudo docker exec steccom-mediawiki chown -R www-data:www-data /var/www/html/data
sudo docker exec steccom-mediawiki chmod -R 755 /var/www/html/data
```

### Проблемы с базой данных

```bash
# Проверка базы данных
sudo docker exec steccom-mediawiki sqlite3 /var/www/html/data/mediawiki.sqlite ".schema"

# Восстановление из бэкапа
sudo docker cp backup.sqlite steccom-mediawiki:/var/www/html/data/mediawiki.sqlite
```

## Рекомендации

### Безопасность
- Измените пароль администратора по умолчанию
- Используйте HTTPS в продакшене
- Регулярно обновляйте MediaWiki

### Производительность
- Настройте кэширование
- Используйте CDN для статических файлов
- Регулярно очищайте старые версии страниц

### Содержимое
- Следите за актуальностью информации
- Используйте категории для организации
- Регулярно обновляйте индексную страницу

---

**Версия документации:** 1.0  
**Дата обновления:** 2025-01-20  
**Автор:** СТЭККОМ Development Team
