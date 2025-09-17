## MediaWiki: быстрый старт и публикация KB

Этот документ описывает, как запустить MediaWiki в Docker (без docker-compose), проверить корректную загрузку стилей/картинок и опубликовать KB-документы через FastAPI. Все операции автоматизированы скриптом `wiki.bash`.

### Требования
- Docker установлен и демон работает (`docker ps` не должен падать)
- Порт 8080 свободен
- Репозиторий склонирован, рабочая директория — корень проекта

### Быстрый старт
1) Сделать скрипт исполняемым:
```bash
chmod +x wiki.bash
```
2) Запустить контейнер:
```bash
./wiki.bash start
```
3) Проверить состояние и заголовки контента:
```bash
./wiki.bash status
```
4) Открыть в браузере: `http://localhost:8080/`

Если главная открывается (200 OK), стили отдаются как `text/css`, а картинки как `image/png` — всё корректно.

### Публикация KB через FastAPI
1) Получите JWT-токен (см. `README_API.md` или `get_token.py`).
2) Выполните:
```bash
TOKEN="<ваш токен>" ./wiki.bash publish \
  --user admin --pass Admin123456789 \
  --glob "docs/kb/*.json"
```
Это вызовет POST к вашему FastAPI (`/wiki/publish`) и опубликует все KB-файлы, подходящие под glob.

### Команды скрипта
```bash
./wiki.bash start     # запуск контейнера mediawiki:1.39 (корневой путь, без /w)
./wiki.bash status    # проверка контейнера и ключевых URL (CSS/картинки)
./wiki.bash purge     # очистка кэша Wiki и purge главной страницы
./wiki.bash publish   # публикация KB: требует TOKEN в окружении
./wiki.bash restart   # перезапуск контейнера
./wiki.bash stop      # остановка и удаление контейнера
```

### Что делает start
- Поднимает контейнер `steccom-mediawiki` на порту 8080
- Монтирует:
  - `mediawiki_data` → `/var/www/html/images` (загрузки)
  - `mediawiki/LocalSettings.php` (только чтение)
- После старта выполняет `purge` главной страницы и печатает статус

### Типовые неисправности и быстрые решения
- 500 Internal Server Error на `/`:
  - Причина: повреждена/пустая БД SQLite (нет таблиц `page`, `l10n_cache`).
  - Решение: пересоздать БД через установщик (см. ниже «Полная переустановка»).

- Стили не грузятся, `Content-Type: text/html` для CSS:
  - Проверьте корневые пути в `mediawiki/LocalSettings.php`:
    - `$wgScriptPath = "";`
    - `$wgResourceBasePath = "";`
    - `$wgLoadScript = "/load.php";`
    - `$wgStylePath  = "/skins";`
    - `$wgUsePathInfo = true;`
    - `$wgArticlePath = "/index.php/$1";`
  - Выполните `./wiki.bash purge` и перезагрузите страницу с очисткой кэша (Ctrl+Shift+R).

- Ошибка локализации `l10n_cache`:
  - Включите файловый кэш локализации в `mediawiki/LocalSettings.php`:
    ```php
    $wgLocalisationCacheConf['store'] = 'cdb';
    $wgLocalisationCacheConf['storeDirectory'] = "$IP/cache/l10n";
    $wgLocalisationCacheConf['manualRecache'] = false;
    ```
  - В контейнере выполните:
    ```bash
    docker exec steccom-mediawiki bash -lc 'mkdir -p /var/www/html/cache/l10n && chown -R www-data:www-data /var/www/html/{cache,images}'
    docker exec steccom-mediawiki php maintenance/rebuildLocalisationCache.php --force --lang=ru
    ```

### Полная переустановка (если «сломали всё»)
1) Остановить/удалить контейнер:
```bash
docker rm -f steccom-mediawiki
```
2) Запустить без монтирования `LocalSettings.php` (создать новую БД):
```bash
docker run -d \
  --name steccom-mediawiki \
  -p 8080:80 \
  -v "$(pwd)/mediawiki_data:/var/www/html/images" \
  --restart unless-stopped \
  mediawiki:1.39
```
3) Установить MediaWiki через CLI:
```bash
docker exec steccom-mediawiki php maintenance/install.php \
  --dbtype=sqlite --dbname=mediawiki \
  --server=http://localhost:8080 --scriptpath="" \
  --lang=ru --pass=Admin123456789 "СТЭККОМ Wiki" admin
```
4) Скопировать сгенерированный `LocalSettings.php` в репозиторий и поправить пути (как выше):
```bash
docker cp steccom-mediawiki:/var/www/html/LocalSettings.php mediawiki/LocalSettings.php
```
5) Перезапустить уже со своим `LocalSettings.php`:
```bash
./wiki.bash restart
```

### Полезные ссылки
- MediaWiki Manual: `https://www.mediawiki.org/wiki/Manual:Contents`
- Конфигурация: `https://www.mediawiki.org/wiki/Manual:Configuration_settings`

# MediaWiki Integration для СТЭККОМ

## Описание
Интеграция с корпоративной MediaWiki для автоматической публикации базы знаний из системы СТЭККОМ.

## Возможности
- Автоматическая публикация KB в MediaWiki
- Конвертация JSON KB в формат MediaWiki
- Поддержка метаданных (аудитория, область, статус)
- Создание/обновление страниц через API
- Настраиваемые пространства имен

## Установка MediaWiki

### Вариант 1: Docker (рекомендуется)
```bash
# Запуск MediaWiki
docker-compose -f docker-compose.mediawiki.yml up -d

# Проверка
curl http://localhost:8080
```

### Вариант 2: Ручная установка
1. Скачайте MediaWiki с https://www.mediawiki.org/wiki/Download
2. Настройте веб-сервер (Apache/Nginx)
3. Создайте базу данных
4. Запустите установщик

## Настройка

### 1. Создание пользователя API
1. Зайдите в MediaWiki как администратор
2. Создайте пользователя для API (например, `steccom-api`)
3. Назначьте права: `bot`, `editor`, `api`

### 2. Настройка в СТЭККОМ
1. Откройте "🔧 Админ-панель → MediaWiki Integration"
2. Заполните настройки:
   - URL: `http://your-wiki.com/w/api.php`
   - Имя пользователя: `steccom-api`
   - Пароль: `password`
   - Префикс: `СТЭККОМ`

### 3. Тест подключения
Нажмите "🔗 Тест подключения" для проверки.

## Использование

### Публикация всех KB
1. В админ-панели нажмите "📚 Публиковать все KB"
2. Система автоматически:
   - Прочитает все файлы из `docs/kb/*.json`
   - Конвертирует в формат MediaWiki
   - Создаст/обновит страницы в пространстве имен "СТЭККОМ"

### Публикация отдельных файлов
1. Выберите файл в "Публикация отдельных файлов"
2. Нажмите "📤 Публиковать выбранный файл"

### Формат публикации
Каждая страница в MediaWiki будет содержать:
- Заголовок из KB
- Метаданные (аудитория, область, статус)
- Источник (файл, указатель)
- Содержимое с форматированием
- Информацию о публикации

## API Endpoints

### Основные методы
- `create_or_update_page(title, content, summary)` - создание/обновление страницы
- `delete_page(title, reason)` - удаление страницы
- `search_pages(query, namespace, limit)` - поиск страниц
- `page_exists(title)` - проверка существования

### Публикация KB
- `publish_kb_item(kb_data, namespace_prefix)` - публикация одного элемента
- `publish_kb_file(kb_file_path, namespace_prefix)` - публикация файла
- `publish_all_kb_files(kb_directory, namespace_prefix)` - публикация всех файлов

## Примеры

### Публикация через код
```python
from modules.integrations import MediaWikiClient, KBToWikiPublisher

# Подключение
client = MediaWikiClient(
    wiki_url="http://localhost:8080/w/api.php",
    username="steccom-api",
    password="password"
)

# Публикация
publisher = KBToWikiPublisher(client)
results = publisher.publish_all_kb_files("docs/kb", "СТЭККОМ")

# Результаты
for kb_file, file_results in results.items():
    for success, message in file_results:
        print(f"{kb_file}: {message}")
```

### Структура страницы в MediaWiki
```
= Услуга детализированного отчёта =

== Метаданные ==
* '''Аудитория:''' user, admin
* '''Область:''' legacy_billing
* '''Статус:''' reference

== Источник ==
* '''Файл:''' data/uploads/reg_07032015.pdf
* '''Указатель:''' п.9

== Содержимое ==
Согласно п.9 Регламента...

----
''Опубликовано из системы СТЭККОМ: 2025-01-17 15:30:00''
```

## Troubleshooting

### Ошибки подключения
- Проверьте URL MediaWiki
- Убедитесь, что пользователь существует и имеет права
- Проверьте доступность API: `curl http://your-wiki.com/w/api.php`

### Ошибки публикации
- Проверьте права пользователя на создание/редактирование
- Убедитесь, что пространство имен существует
- Проверьте формат JSON в KB файлах

### Логи
Ошибки отображаются в интерфейсе админ-панели. Для детальной диагностики проверьте логи MediaWiki.

## Безопасность
- Используйте отдельного пользователя для API
- Ограничьте права доступа
- Регулярно обновляйте MediaWiki
- Используйте HTTPS в продакшене
