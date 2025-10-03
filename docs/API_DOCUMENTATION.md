# 🚀 STECCOM API Documentation

## Обзор

STECCOM API предоставляет REST API для работы с системой спутниковой связи. API построен на FastAPI и предоставляет следующие возможности:

- 🔐 Аутентификация пользователей
- 🗄️ Работа с базой данных (схема, выполнение запросов)
- 🤖 Генерация SQL из естественного языка
- 🧠 RAG система для работы с документацией
- 📊 Управление базой знаний

## Запуск API сервера

### Вариант 1: Прямой запуск
```bash
python api/run_api.py
```

### Вариант 2: Через скрипт
```bash
python run_api_server.py
```

### Вариант 3: Через uvicorn
```bash
uvicorn api.run_api:app --host 0.0.0.0 --port 8000 --reload
```

## Базовый URL
```
http://localhost:8000
```

## Документация API
После запуска сервера документация доступна по адресу:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Эндпоинты

### 🔍 Системные

#### GET /
**Описание**: Корневой эндпоинт  
**Ответ**:
```json
{
  "message": "STECCOM API Server",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2025-01-27T10:00:00"
}
```

#### GET /health
**Описание**: Проверка состояния системы  
**Ответ**:
```json
{
  "status": "healthy",
  "database": "connected",
  "rag_available": true,
  "timestamp": "2025-01-27T10:00:00"
}
```

### 🔐 Аутентификация

#### POST /auth/login
**Описание**: Аутентификация пользователя  
**Тело запроса**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```
**Ответ**:
```json
{
  "success": true,
  "user": {
    "username": "admin",
    "company": "СТЭККОМ",
    "role": "staff"
  }
}
```

### 🗄️ База данных

#### GET /database/schema
**Описание**: Получение схемы базы данных  
**Ответ**:
```json
{
  "success": true,
  "schema": "Database Schema:\n\nTable: users\nColumns:\n..."
}
```

#### POST /sql/generate
**Описание**: Генерация SQL запроса из естественного языка  
**Тело запроса**:
```json
{
  "question": "Покажи все устройства",
  "company": "СТЭККОМ",
  "username": "admin"
}
```
**Ответ**:
```json
{
  "success": true,
  "sql_query": "SELECT * FROM devices WHERE user_id IN (SELECT id FROM users WHERE company = 'СТЭККОМ')",
  "question": "Покажи все устройства",
  "company": "СТЭККОМ"
}
```

#### POST /sql/execute
**Описание**: Выполнение SQL запроса  
**Параметры**:
- `sql_query` (query): SQL запрос
- `username` (query): Имя пользователя

**Ответ**:
```json
{
  "success": true,
  "data": [
    {
      "imei": "123456789012345",
      "device_type": "VSAT",
      "model": "SkyEdge II"
    }
  ],
  "sql_query": "SELECT * FROM devices LIMIT 10",
  "company": "СТЭККОМ",
  "row_count": 1
}
```

### 🧠 RAG система

#### POST /rag/query
**Описание**: Запрос к RAG системе  
**Тело запроса**:
```json
{
  "question": "Как работает система биллинга?",
  "kb_id": 1,
  "role": "user"
}
```
**Ответ**:
```json
{
  "success": true,
  "answer": "Система биллинга СТЭККОМ работает следующим образом...",
  "sources": [
    {
      "source": "docs/kb/legacy_reglament_sbd.json",
      "relevance": 0.95
    }
  ],
  "question": "Как работает система биллинга?",
  "kb_id": 1,
  "role": "user"
}
```

#### GET /rag/knowledge-bases
**Описание**: Список доступных баз знаний  
**Ответ**:
```json
{
  "success": true,
  "knowledge_bases": [
    {
      "id": 1,
      "name": "Legacy Regulations",
      "description": "Устаревшие регламенты",
      "document_count": 15
    }
  ]
}
```

### 👤 Пользователи

#### GET /users/{username}/company
**Описание**: Получение информации о компании пользователя  
**Параметры**:
- `username` (path): Имя пользователя

**Ответ**:
```json
{
  "success": true,
  "username": "admin",
  "company": "СТЭККОМ"
}
```

### 📋 Стандартные отчеты

#### GET /reports/standard
**Описание**: Получение списка доступных стандартных отчетов  
**Ответ**:
```json
{
  "success": true,
  "reports": [
    "My monthly traffic",
    "My devices", 
    "Current month usage",
    "Sessions last 30 days"
  ],
  "quick_questions": [
    "Покажи статистику трафика за последний месяц",
    "Какие устройства потребляют больше всего трафика?"
  ]
}
```

#### GET /reports/standard/{report_type}
**Описание**: Выполнение стандартного отчета  
**Параметры**:
- `report_type` (path): Тип отчета
- `username` (query): Имя пользователя

**Ответ**:
```json
{
  "success": true,
  "data": [
    {
      "month": "2025-01",
      "service_type": "SBD",
      "total_usage": 1500,
      "total_amount": 750.50
    }
  ],
  "report_type": "My monthly traffic",
  "company": "СТЭККОМ",
  "row_count": 1
}
```

### 📥 Экспорт данных

#### GET /export/csv
**Описание**: Экспорт данных в CSV формате  
**Параметры**:
- `sql_query` (query): SQL запрос
- `filename` (query): Имя файла (по умолчанию: export.csv)
- `username` (query): Имя пользователя

**Ответ**: CSV файл для скачивания

### 📊 Визуализация

#### POST /charts/create
**Описание**: Создание графика из данных  
**Тело запроса**:
```json
{
  "data": [
    {"month": "2025-01", "usage": 100},
    {"month": "2025-02", "usage": 150}
  ],
  "chart_type": "line",
  "title": "Динамика трафика"
}
```
**Ответ**:
```json
{
  "success": true,
  "chart_info": {
    "chart_type": "line",
    "title": "Динамика трафика",
    "data_points": 2,
    "columns": ["month", "usage"],
    "sample_data": [
      {"month": "2025-01", "usage": 100},
      {"month": "2025-02", "usage": 150}
    ]
  },
  "message": "Chart created with 2 data points"
}
```

### 💾 Управление состоянием

#### GET /session/state
**Описание**: Получение состояния сессии пользователя  
**Параметры**:
- `username` (query): Имя пользователя

**Ответ**:
```json
{
  "success": true,
  "username": "admin",
  "session_data": {
    "last_query": null,
    "favorite_reports": [],
    "preferences": {}
  },
  "message": "Session state placeholder - implement actual storage"
}
```

#### POST /session/state
**Описание**: Сохранение состояния сессии пользователя  
**Тело запроса**:
```json
{
  "last_query": "SELECT * FROM users",
  "favorite_reports": ["My monthly traffic"],
  "preferences": {"theme": "dark"}
}
```
**Ответ**:
```json
{
  "success": true,
  "username": "admin",
  "message": "Session state saved (placeholder - implement actual storage)"
}
```

## Коды ошибок

- **200**: Успешный запрос
- **400**: Неверный запрос
- **401**: Не авторизован
- **404**: Ресурс не найден
- **500**: Внутренняя ошибка сервера
- **503**: Сервис недоступен

## Примеры использования

### Python
```python
import requests

# Аутентификация
response = requests.post("http://localhost:8000/auth/login", json={
    "username": "admin",
    "password": "admin123"
})
token = response.json()["user"]

# Генерация SQL
response = requests.post("http://localhost:8000/sql/generate", json={
    "question": "Покажи трафик за последний месяц",
    "username": "admin"
})
sql_query = response.json()["sql_query"]

# Выполнение запроса
response = requests.post(f"http://localhost:8000/sql/execute?sql_query={sql_query}&username=admin")
data = response.json()["data"]
```

### JavaScript
```javascript
// Аутентификация
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin123'
  })
});
const user = await loginResponse.json();

// RAG запрос
const ragResponse = await fetch('http://localhost:8000/rag/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'Как настроить VSAT?',
    role: 'user'
  })
});
const answer = await ragResponse.json();
```

## Тестирование

Для тестирования API используйте скрипт:
```bash
python test_api.py
```

## Безопасность

- API использует простую аутентификацию по имени пользователя
- Все SQL запросы фильтруются по компании пользователя
- Логирование всех операций в файл `logs/api.log`
- CORS настроен для всех источников (в продакшене следует ограничить)

## Мониторинг

- Логи API: `logs/api.log`
- Health check: `GET /health`
- Метрики доступны через Swagger UI

## Развертывание

### Docker (рекомендуется)
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "api.run_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Systemd service
```ini
[Unit]
Description=STECCOM API Server
After=network.target

[Service]
Type=simple
User=steccom
WorkingDirectory=/opt/steccom
ExecStart=/opt/steccom/.venv/bin/python api/run_api.py
Restart=always

[Install]
WantedBy=multi-user.target
```
