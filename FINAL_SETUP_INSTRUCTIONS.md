# Финальные инструкции по настройке

## 🎯 Текущий статус

✅ **Готово:**
- Docker установлен и работает
- MediaWiki контейнер запущен
- API работает на http://localhost:8000
- Все скрипты и документация созданы
- KB файлы готовы к загрузке

⚠️ **Требует завершения:**
- Настройка MediaWiki через веб-интерфейс
- Загрузка базы знаний

## 🚀 Шаги для завершения настройки

### 1. Настройка MediaWiki

1. **Откройте браузер** и перейдите на http://localhost:8080
2. **Нажмите "set up the wiki"** или перейдите на http://localhost:8080/mw-config/
3. **Выберите язык**: Русский
4. **Настройте базу данных**:
   - Тип: **SQLite**
   - Имя базы: **mediawiki**
5. **Создайте администратора**:
   - Имя пользователя: **admin**
   - Пароль: **admin123**
   - Email: admin@steccom.local
6. **Завершите установку**

### 2. Загрузка базы знаний

После завершения настройки MediaWiki выполните:

```bash
# Активация виртуального окружения
cd /mnt/ai/cnn/steccom
source .venv/bin/activate

# Загрузка всех KB файлов в MediaWiki
python3 scripts/upload_kb_to_mediawiki.py \
  --wiki-url http://localhost:8080/api.php \
  --username admin \
  --password admin123 \
  --create-index
```

### 3. Проверка работы

```bash
# Проверка API
curl http://localhost:8000/health

# Проверка MediaWiki
curl http://localhost:8080/

# Проверка API MediaWiki
curl "http://localhost:8080/api.php?action=query&meta=siteinfo&format=json"
```

## 📋 Альтернативные способы загрузки KB

### Через API (если есть токен)

```bash
# Получение токена
python3 get_token.py

# Публикация через API
TOKEN="your_token" ./wiki.bash publish \
  --user admin --pass admin123 \
  --glob "docs/kb/*.json"
```

### Через Streamlit интерфейс

1. Запустите Streamlit: `streamlit run app.py`
2. Перейдите в "🔧 Админ-панель"
3. Выберите "MediaWiki Integration"
4. Настройте подключение и загрузите KB

## 🔧 Управление системой

### Запуск/остановка сервисов

```bash
# MediaWiki
sudo docker start steccom-mediawiki
sudo docker stop steccom-mediawiki

# API
source .venv/bin/activate
python3 api/main.py
```

### Просмотр логов

```bash
# MediaWiki
sudo docker logs steccom-mediawiki

# API (если в фоне)
tail -f logs/app.log
```

## 📊 Ожидаемый результат

После завершения настройки у вас будет:

- **MediaWiki** с 9 страницами базы знаний
- **Индексная страница** с навигацией
- **API интеграция** для управления KB
- **Полная документация** по системе

## 🆘 Если что-то не работает

### MediaWiki не настраивается
```bash
# Пересоздание контейнера
sudo docker rm -f steccom-mediawiki
sudo docker run -d --name steccom-mediawiki -p 8080:80 mediawiki:1.39
```

### Ошибки загрузки KB
```bash
# Проверка подключения
curl "http://localhost:8080/api.php?action=query&meta=siteinfo&format=json"

# Проверка аутентификации
curl "http://localhost:8080/api.php?action=query&meta=tokens&type=login&format=json"
```

### Проблемы с API
```bash
# Перезапуск API
pkill -f "python.*main.py"
source .venv/bin/activate
python3 api/main.py
```

## 🎉 После завершения

Система будет полностью готова к использованию:

1. **MediaWiki**: http://localhost:8080 - корпоративная база знаний
2. **API**: http://localhost:8000 - REST API для интеграций
3. **API Docs**: http://localhost:8000/docs - документация API
4. **Streamlit**: http://localhost:8501 - веб-интерфейс (если запущен)

---

**Время на завершение**: ~10 минут  
**Сложность**: Простая (только веб-интерфейс)  
**Результат**: Полностью рабочая система СТЭККОМ
