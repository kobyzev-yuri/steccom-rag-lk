# 🚀 Быстрый старт STECCOM API

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск API сервера

```bash
# Простой способ
python run_api_server.py

# Или напрямую
python api/run_api.py
```

## Проверка работы

1. **Откройте браузер**: http://localhost:8000
2. **Документация API**: http://localhost:8000/docs
3. **Health check**: http://localhost:8000/health

## Тестирование

```bash
python test_api.py
```

## Основные эндпоинты

- `GET /` - информация о сервере
- `GET /health` - проверка состояния
- `POST /auth/login` - аутентификация
- `GET /database/schema` - схема БД
- `POST /sql/generate` - генерация SQL
- `POST /sql/execute` - выполнение SQL
- `POST /rag/query` - RAG запросы
- `GET /rag/knowledge-bases` - список БЗ

## Пример использования

```python
import requests

# Аутентификация
response = requests.post("http://localhost:8000/auth/login", json={
    "username": "admin",
    "password": "admin123"
})

# Генерация SQL
response = requests.post("http://localhost:8000/sql/generate", json={
    "question": "Покажи все устройства",
    "username": "admin"
})
sql = response.json()["sql_query"]

# Выполнение запроса
response = requests.post(f"http://localhost:8000/sql/execute?sql_query={sql}&username=admin")
data = response.json()["data"]
```

## Логи

Логи API сохраняются в файл: `logs/api.log`
