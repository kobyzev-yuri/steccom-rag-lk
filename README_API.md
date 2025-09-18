# СТЭККОМ Billing API

REST API для системы спутниковой связи СТЭККОМ с интеграцией MediaWiki.

## Возможности

- 🔐 JWT аутентификация с ролями (user/admin)
- 📊 REST эндпоинты для договоров, устройств, отчётов
- 📚 Интеграция с MediaWiki для публикации KB
- 📖 Автоматическая OpenAPI документация
- 🧪 Unit тесты для всех эндпоинтов
- 🔄 CORS поддержка для Streamlit UI

## Быстрый старт

### 1. Запуск API сервера
```bash
# Через скрипт
./run_api.sh

# Или напрямую
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Документация
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 3. Быстрое тестирование
```bash
# Проверка работы API
curl http://localhost:8000/health

# Получение токена
python get_token.py staff1

# Тест с токеном (замените YOUR_TOKEN)
TOKEN="YOUR_TOKEN_HERE"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me
```

## Аутентификация

### Получение JWT токена

#### 1. Через curl (командная строка)
```bash
# Получение токена
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "staff1", "password": "10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6"}'

# Ответ:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_info": {
    "id": 1,
    "username": "staff1",
    "company": "Admin",
    "role": "staff",
    "is_staff": true
  }
}
```

#### 2. Через Python скрипт (рекомендуется)
```bash
# Запуск скрипта для получения токена
python get_token.py staff1

# Вывод:
✅ Успешная аутентификация!
👤 Пользователь: staff1 (staff)
🏢 Компания: Admin
⏰ Токен действителен: 1800 секунд

🔑 JWT Token:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdGFmZjEiLCJjb21wYW55IjoiQWRtaW4iLCJyb2xlIjoic3RhZmYiLCJpc19zdGFmZiI6dHJ1ZSwiZXhwIjoxNzU4MTEwMDU0fQ.jDtjv6v5xOO48eNR3XN20IVgn_e8d_tYqeYPCcEup4g
```

#### 3. Через Swagger UI (интерактивно)
1. Откройте http://localhost:8000/docs
2. Найдите эндпоинт `POST /auth/login`
3. Нажмите "Try it out"
4. Введите данные:
   ```json
   {
     "username": "staff1",
     "password": "10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6"
   }
   ```
5. Нажмите "Execute"
6. Скопируйте `access_token` из ответа

### Использование токена

#### В curl запросах
```bash
# Сохранение токена в переменную
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Использование токена
curl -X GET "http://localhost:8000/agreements/current" \
  -H "Authorization: Bearer $TOKEN"
```

#### В Swagger UI
1. Нажмите кнопку **"Authorize"** (🔒) в правом верхнем углу
2. Введите: `Bearer YOUR_TOKEN_HERE`
3. Нажмите "Authorize"
4. Теперь все защищённые эндпоинты будут работать автоматически

#### В Python коде
```python
import requests

# Получение токена
login_response = requests.post("http://localhost:8000/auth/login", json={
    "username": "staff1",
    "password": "10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6"
})
token = login_response.json()["access_token"]

# Использование токена
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/agreements/current", headers=headers)
agreements = response.json()
```

### Доступные пользователи
- **staff1** (admin) - полный доступ ко всем функциям
- **arctic_user** (user) - доступ только к данным своей компании
- **desert_user** (user) - доступ только к данным своей компании

### Важные моменты
- Токен действителен **30 минут** (1800 секунд)
- После истечения нужно получить новый токен
- Токен содержит информацию о роли пользователя
- Staff пользователи имеют доступ к административным функциям

## Основные эндпоинты

### Аутентификация
- `POST /auth/login` - Вход в систему
- `GET /auth/me` - Информация о текущем пользователе

### Договоры
- `GET /agreements/current` - Текущие активные договоры
- `GET /agreements/history` - История всех договоров

### Устройства
- `GET /devices` - Список устройств компании

### Отчёты
- `GET /reports/available` - Доступные типы отчётов
- `POST /reports/standard` - Получение стандартного отчёта

### Wiki интеграция (только для staff)
- `GET /wiki/test-connection` - Тест подключения к MediaWiki
- `POST /wiki/publish` - Публикация KB в MediaWiki

## Примеры использования

### Получение текущих договоров
```python
import requests

# Аутентификация
login_response = requests.post("http://localhost:8000/auth/login", json={
    "username": "staff1",
    "password": "10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6"
})
token = login_response.json()["access_token"]

# Получение договоров
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/agreements/current", headers=headers)
agreements = response.json()

print(f"Найдено договоров: {len(agreements)}")
for agreement in agreements:
    print(f"- {agreement['tariff_name']} ({agreement['status']})")
```

### Получение списка устройств
```python
import requests

# Используем уже полученный токен
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/devices", headers=headers)
devices = response.json()

print(f"Найдено устройств: {len(devices)}")
for device in devices:
    print(f"- {device['imei']}: {device['device_type']} {device['model']}")
```

### Получение стандартного отчёта
```python
import requests

# Получение отчёта по устройствам
report_data = {"report_type": "my_devices"}
response = requests.post(
    "http://localhost:8000/reports/standard",
    json=report_data,
    headers={"Authorization": f"Bearer {token}"}
)
report = response.json()

print(f"Отчёт: {report['report_type']}")
print(f"Записей: {report['total_records']}")
for record in report['data']:
    print(f"- {record}")
```

### Полный пример с обработкой ошибок
```python
import requests
import json

def get_api_token(username, password):
    """Получить JWT токен"""
    try:
        response = requests.post("http://localhost:8000/auth/login", json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"Ошибка аутентификации: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None

def api_request(endpoint, token, method="GET", data=None):
    """Выполнить API запрос"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"http://localhost:8000{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

# Использование
token = get_api_token("staff1", "10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6")

if token:
    # Получение информации о пользователе
    user_info = api_request("/auth/me", token)
    print(f"Пользователь: {user_info['username']} ({user_info['role']})")
    
    # Получение договоров
    agreements = api_request("/agreements/current", token)
    print(f"Договоров: {len(agreements)}")
    
    # Получение устройств
    devices = api_request("/devices", token)
    print(f"Устройств: {len(devices)}")
```

### Публикация в MediaWiki
```python
# Публикация всех KB файлов
wiki_data = {
    "wiki_url": "http://localhost:8080/w/api.php",
    "username": "admin",
    "password": "admin123",
    "namespace_prefix": "СТЭККОМ"
}

response = httpx.post(
    "http://localhost:8000/wiki/publish",
    json=wiki_data,
    headers={"Authorization": f"Bearer {token}"}
)
```

### Получение отчёта
```python
# Получение отчёта по устройствам
report_data = {"report_type": "my_devices"}
response = httpx.post(
    "http://localhost:8000/reports/standard",
    json=report_data,
    headers={"Authorization": f"Bearer {token}"}
)
report = response.json()
```

## Тестирование

### Запуск тестов
```bash
# Все тесты
pytest tests/test_api.py -v

# Конкретный тест
pytest tests/test_api.py::TestAuthentication::test_login_success -v
```

### Тестовые пользователи
- **Staff**: `staff1` / `staff123`
- **User**: `user1` / `user123`

## Роли и права доступа

### User (обычный пользователь)
- Просмотр своих договоров и устройств
- Получение отчётов по своей компании
- Доступ только к данным своей компании

### Staff (администратор)
- Все права пользователя
- Доступ к данным всех компаний
- Управление Wiki интеграцией
- Административные функции

## Интеграция с Streamlit

API настроен для работы с Streamlit UI:
- CORS разрешён для `localhost:8501`
- Эндпоинты совместимы с существующими запросами
- JWT токены можно использовать в Streamlit сессиях

## Конфигурация

### Переменные окружения
```bash
export JWT_SECRET_KEY="your-secret-key"
export DATABASE_URL="sqlite:///satellite_billing.db"
```

### Настройки CORS
В `api/main.py` можно настроить разрешённые домены:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   FastAPI API   │    │   MediaWiki     │
│   (Port 8501)   │◄──►│   (Port 8000)   │◄──►│   (Port 8080)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │   (Billing)     │
                       └─────────────────┘
```

## Разработка

### Структура проекта
```
api/
├── main.py              # Основное приложение FastAPI
└── run_api.py           # Скрипт запуска

tests/
└── test_api.py          # Unit тесты

requirements-api.txt     # Зависимости API
run_api.sh              # Скрипт запуска
```

### Добавление новых эндпоинтов
1. Добавьте Pydantic модели в `api/main.py`
2. Создайте эндпоинт с декоратором `@app.get()` или `@app.post()`
3. Добавьте тесты в `tests/test_api.py`
4. Обновите документацию

## Troubleshooting

### Ошибки аутентификации
```bash
# Проверка доступных пользователей
python -c "
import sqlite3
conn = sqlite3.connect('satellite_billing.db')
c = conn.cursor()
c.execute('SELECT username, role FROM users')
users = c.fetchall()
print('Доступные пользователи:')
for user in users:
    print(f'  {user[0]} ({user[1]})')
conn.close()
"

# Проверка пароля пользователя
python -c "
import sqlite3
conn = sqlite3.connect('satellite_billing.db')
c = conn.cursor()
c.execute('SELECT username, password FROM users WHERE username = \"staff1\"')
user = c.fetchone()
print(f'staff1 password hash: {user[1]}')
conn.close()
"
```

**Частые проблемы:**
- Неправильный пароль (используйте хеш из БД)
- Истёкший токен (получите новый через `/auth/login`)
- Неправильный формат заголовка: `Authorization: Bearer TOKEN`

### Ошибки базы данных
```bash
# Проверка существования БД
ls -la satellite_billing.db

# Инициализация БД если нужно
python -c "from modules.core.database import init_db; init_db()"

# Проверка подключения
curl http://localhost:8000/health
```

### Ошибки Wiki интеграции
```bash
# Проверка доступности MediaWiki
curl http://localhost:8080/w/api.php

# Тест подключения через API
curl -X GET "http://localhost:8000/wiki/test-connection" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G -d "wiki_url=http://localhost:8080/w/api.php" \
  -d "username=admin" \
  -d "password=admin123"
```

### Отладка API запросов
```bash
# Включение подробных логов
curl -v -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "staff1", "password": "хеш_пароля"}'

# Проверка статуса сервера
curl -I http://localhost:8000/health

# Проверка CORS (для браузера)
curl -H "Origin: http://localhost:8501" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization" \
  -X OPTIONS http://localhost:8000/agreements/current
```

### Логи сервера
```bash
# Просмотр логов uvicorn
# Логи отображаются в терминале где запущен сервер

# Пример логов:
# INFO: 127.0.0.1:12345 - "POST /auth/login HTTP/1.1" 200 OK
# INFO: 127.0.0.1:12345 - "GET /agreements/current HTTP/1.1" 200 OK
# INFO: 127.0.0.1:12345 - "GET /devices HTTP/1.1" 200 OK
```

### Восстановление после ошибок
```bash
# Перезапуск API сервера
pkill -f uvicorn
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Очистка кэша Python
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Переустановка зависимостей
pip install --force-reinstall fastapi uvicorn PyJWT
```
