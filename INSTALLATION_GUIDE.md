# Руководство по установке СТЭККОМ

## Обзор системы

СТЭККОМ - система спутниковой связи с интеграцией MediaWiki для управления базой знаний.

### Компоненты системы:
- **FastAPI Backend** - REST API для доступа к данным
- **Streamlit Frontend** - веб-интерфейс пользователя
- **MediaWiki** - корпоративная вики для базы знаний
- **SQLite Database** - основная база данных
- **Docker** - контейнеризация MediaWiki

## Требования

### Системные требования:
- Ubuntu 24.04+ (или другая Linux система)
- Python 3.10+
- Docker и Docker Compose
- 4GB RAM минимум
- 10GB свободного места

### Порты:
- **8000** - FastAPI Backend
- **8080** - MediaWiki
- **8501** - Streamlit (если запускается отдельно)

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd steccom
```

### 2. Установка Docker

```bash
# Обновление пакетов
sudo apt update

# Установка Docker
sudo apt install -y docker.io docker-compose

# Запуск Docker daemon
sudo systemctl start docker
sudo systemctl enable docker

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниться или выполнить:
newgrp docker
```

### 3. Настройка виртуального окружения

```bash
# Создание виртуального окружения
python3 -m venv .venv

# Активация
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements-api.txt
pip install streamlit plotly openai pandas sqlalchemy
```

### 4. Запуск MediaWiki

```bash
# Загрузка образа MediaWiki
sudo docker pull mediawiki:1.39

# Запуск MediaWiki контейнера
sudo docker run -d \
    --name steccom-mediawiki \
    -p 8080:80 \
    -v "$(pwd)/mediawiki_data:/var/www/html/images" \
    --restart unless-stopped \
    mediawiki:1.39
```

### 5. Настройка MediaWiki

1. Откройте http://localhost:8080 в браузере
2. Выберите язык (Русский)
3. Настройте базу данных:
   - Тип: SQLite
   - Имя базы: mediawiki
4. Создайте администратора:
   - Имя пользователя: admin
   - Пароль: admin123
5. Завершите установку

### 6. Запуск API

```bash
# Активация виртуального окружения
source .venv/bin/activate

# Запуск API сервера
python3 api/main.py
```

API будет доступен на http://localhost:8000

### 7. Запуск Streamlit (опционально)

```bash
# В новом терминале
source .venv/bin/activate
streamlit run app.py
```

## Конфигурация

### Настройки MediaWiki

Файл `mediawiki/LocalSettings.php` содержит основные настройки:

```php
$wgSitename = "СТЭККОМ Wiki";
$wgScriptPath = "";  // Корневой путь (без /w)
$wgServer = "http://localhost:8080";
$wgLanguageCode = "ru";
```

### Настройки API

Основные настройки в `config/settings.py`:

```python
DATABASE_URL = "sqlite:///satellite_billing.db"
JWT_SECRET_KEY = "your-secret-key"
```

## Проверка установки

### 1. Проверка API

```bash
curl http://localhost:8000/health
# Ожидаемый ответ: {"status":"healthy","database":"connected"}
```

### 2. Проверка MediaWiki

```bash
curl -I http://localhost:8080/
# Ожидаемый ответ: HTTP/1.1 200 OK
```

### 3. Проверка API документации

Откройте http://localhost:8000/docs в браузере

## Публикация базы знаний

### Через API

```bash
# Получение токена
python3 get_token.py

# Публикация KB в MediaWiki
TOKEN="your_token" ./wiki.bash publish \
  --user admin --pass admin123 \
  --glob "docs/kb/*.json"
```

### Через Streamlit интерфейс

1. Откройте Streamlit приложение
2. Перейдите в "🔧 Админ-панель"
3. Выберите "MediaWiki Integration"
4. Настройте подключение:
   - URL: http://localhost:8080/api.php
   - Пользователь: admin
   - Пароль: admin123
5. Нажмите "📚 Публиковать все KB"

## Управление сервисами

### Запуск/остановка MediaWiki

```bash
# Запуск
sudo docker start steccom-mediawiki

# Остановка
sudo docker stop steccom-mediawiki

# Перезапуск
sudo docker restart steccom-mediawiki

# Удаление
sudo docker rm -f steccom-mediawiki
```

### Просмотр логов

```bash
# Логи MediaWiki
sudo docker logs steccom-mediawiki

# Логи API (если запущен в фоне)
tail -f logs/app.log
```

## Устранение неполадок

### Проблемы с Docker

```bash
# Проверка статуса Docker
sudo systemctl status docker

# Перезапуск Docker
sudo systemctl restart docker

# Проверка прав доступа
sudo chmod 666 /var/run/docker.sock
```

### Проблемы с MediaWiki

```bash
# Проверка контейнера
sudo docker ps | grep mediawiki

# Проверка логов
sudo docker logs steccom-mediawiki

# Пересоздание контейнера
sudo docker rm -f steccom-mediawiki
sudo docker run -d --name steccom-mediawiki -p 8080:80 mediawiki:1.39
```

### Проблемы с API

```bash
# Проверка зависимостей
source .venv/bin/activate
pip list

# Проверка базы данных
sqlite3 satellite_billing.db ".tables"

# Перезапуск API
pkill -f "python.*main.py"
python3 api/main.py
```

## Безопасность

### Рекомендации для продакшена:

1. **Измените пароли по умолчанию**
2. **Используйте HTTPS**
3. **Настройте файрвол**
4. **Регулярно обновляйте зависимости**
5. **Настройте резервное копирование**

### Изменение паролей:

```bash
# MediaWiki админ
# Войдите в MediaWiki и измените пароль через Special:ChangePassword

# API JWT секрет
export JWT_SECRET_KEY="your-strong-secret-key"
```

## Резервное копирование

### База данных

```bash
# Создание бэкапа
cp satellite_billing.db backup_$(date +%Y%m%d).db

# Восстановление
cp backup_20250120.db satellite_billing.db
```

### MediaWiki

```bash
# Бэкап базы данных MediaWiki
sudo docker exec steccom-mediawiki sqlite3 /var/www/html/data/mediawiki.sqlite ".backup /var/www/html/backup.sqlite"

# Бэкап файлов
sudo docker cp steccom-mediawiki:/var/www/html/data ./mediawiki_backup_$(date +%Y%m%d)
```

## Обновление

### Обновление кода

```bash
git pull origin main
source .venv/bin/activate
pip install -r requirements-api.txt
```

### Обновление MediaWiki

```bash
sudo docker pull mediawiki:1.39
sudo docker stop steccom-mediawiki
sudo docker rm steccom-mediawiki
# Запустить новый контейнер по инструкции выше
```

## Поддержка

При возникновении проблем:

1. Проверьте логи сервисов
2. Убедитесь, что все порты свободны
3. Проверьте права доступа к файлам
4. Обратитесь к документации компонентов

---

**Версия документации:** 1.0  
**Дата обновления:** 2025-01-20  
**Автор:** СТЭККОМ Development Team
