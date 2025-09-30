## MediaWiki: запуск и управление

Используйте единый скрипт `wiki-compose.bash`. Он автоматически:
- определяет доступность `docker compose`/`docker-compose` и при необходимости использует fallback на обычный `docker`;
- гарантирует наличие и права каталогов `mediawiki_db_persistent` и `mediawiki_data`;
- применяет конфигурацию из `docker-compose.yml` (при наличии compose).

### Быстрый старт

```bash
bash wiki-compose.bash start
```

Откройте:
- Веб-интерфейс: http://localhost:8080/
- API: http://localhost:8080/api.php

### Основные команды

```bash
# Статус (покажет состояние контейнера и проверит статику)
bash wiki-compose.bash status

# Остановить / Перезапустить
bash wiki-compose.bash stop
bash wiki-compose.bash restart

# Логи
bash wiki-compose.bash logs

# Очистка кэша (purge) и обновление главной
bash wiki-compose.bash purge

# Резервное копирование (backup) в каталог backups/YYYmmdd_HHMMSS
bash wiki-compose.bash backup

# Восстановление из бэкапа
bash wiki-compose.bash restore backups/20250101_120000
```

### Публикация KB в MediaWiki через FastAPI

```bash
export TOKEN="<jwt_token>"
bash wiki-compose.bash publish \
  --user admin \
  --pass Admin123456789 \
  --glob "docs/kb/*.json"
```

Скрипт отправит POST-запрос на `http://localhost:8000/wiki/publish` с параметрами доступа к MediaWiki (`/api.php`).

### Примечания
- Данные MediaWiki (SQLite) монтируются из `./mediawiki_db_persistent` в `/var/www/html/data`.
- Загруженные файлы монтируются из `./mediawiki_data` в `/var/www/html/images`.
- Конфигурация `LocalSettings.php` монтируется read-only из `./mediawiki/LocalSettings.php`.



