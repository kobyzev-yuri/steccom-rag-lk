# KB API Documentation

## Обзор

KB API предоставляет полный набор REST endpoints для управления базами знаний, тестирования релевантности и интеграции с RAG системой. API интегрирован в основной СТЭККОМ API сервер.

## Базовый URL

```
http://localhost:8000
```

## Аутентификация

API использует JWT токены для аутентификации. Получите токен через `/auth/login` и передавайте его в заголовке:

```
Authorization: Bearer <your_jwt_token>
```

## Основные группы endpoints

### 1. Управление базами знаний (`/kb-management`)

#### Получение списка БЗ
```http
GET /kb-management/knowledge-bases?active_only=true
```

#### Создание новой БЗ
```http
POST /kb-management/knowledge-bases
Content-Type: application/json

{
    "name": "Новая база знаний",
    "description": "Описание БЗ",
    "category": "Техническая документация",
    "created_by": "admin"
}
```

#### Получение конкретной БЗ
```http
GET /kb-management/knowledge-bases/{kb_id}
```

#### Обновление БЗ
```http
PUT /kb-management/knowledge-bases/{kb_id}
Content-Type: application/json

{
    "name": "Обновленное название",
    "description": "Новое описание",
    "is_active": true
}
```

#### Удаление БЗ
```http
DELETE /kb-management/knowledge-bases/{kb_id}
```

### 2. Управление документами

#### Получение документов БЗ
```http
GET /kb-management/knowledge-bases/{kb_id}/documents
```

#### Загрузка документа в БЗ
```http
POST /kb-management/knowledge-bases/{kb_id}/documents
Content-Type: multipart/form-data

file: <file>
created_by: admin
```

### 3. Метаданные БЗ

#### Получение метаданных
```http
GET /kb-management/knowledge-bases/{kb_id}/metadata?metadata_key=relevance_test_questions
```

#### Обновление метаданных
```http
POST /kb-management/knowledge-bases/{kb_id}/metadata
Content-Type: application/json

{
    "metadata_key": "relevance_test_questions",
    "metadata_value": "{\"questions\": [...], \"version\": \"1.0\"}"
}
```

### 4. Статистика

#### Статистика конкретной БЗ
```http
GET /kb-management/knowledge-bases/{kb_id}/stats
```

#### Общая статистика системы
```http
GET /kb-management/stats/overview
```

### 5. Тестовые вопросы (`/kb-test-questions`)

#### Получение тестовых вопросов для БЗ
```http
GET /kb-test-questions/{kb_id}
```

#### Список БЗ с тестовыми вопросами
```http
GET /kb-test-questions/
```

#### Быстрое тестирование релевантности
```http
POST /kb-test-questions/{kb_id}/test?question=Как рассчитывается трафик?&expected_keywords=пропорционально,дни
```

### 6. RAG система (`/rag`)

#### Статус RAG системы
```http
GET /rag/status
```

#### Поиск в БЗ
```http
POST /rag/search
Content-Type: application/json

{
    "query": "поисковый запрос",
    "kb_names": ["БЗ1", "БЗ2"],
    "limit": 5
}
```

#### Задать вопрос RAG системе
```http
POST /rag/ask
Content-Type: application/json

{
    "question": "Как рассчитывается включенный трафик?",
    "kb_names": ["Биллинг"]
}
```

#### Список доступных БЗ
```http
GET /rag/knowledge-bases
```

#### Загрузка всех БЗ
```http
POST /rag/load-all
```

## Примеры использования

### Python клиент

```python
import requests

# Аутентификация
login_data = {"username": "admin", "password": "password"}
response = requests.post("http://localhost:8000/auth/login", json=login_data)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Создание БЗ
kb_data = {
    "name": "Техническая документация",
    "description": "Документы по техническим вопросам",
    "category": "Техническая",
    "created_by": "admin"
}
response = requests.post("http://localhost:8000/kb-management/knowledge-bases", 
                        json=kb_data, headers=headers)
kb_id = response.json()["id"]

# Загрузка документа
with open("document.pdf", "rb") as f:
    files = {"file": f}
    data = {"created_by": "admin"}
    response = requests.post(f"http://localhost:8000/kb-management/knowledge-bases/{kb_id}/documents",
                           files=files, data=data, headers=headers)

# Получение тестовых вопросов
response = requests.get(f"http://localhost:8000/kb-test-questions/{kb_id}", headers=headers)
test_questions = response.json()["questions"]

# Тестирование релевантности
for question in test_questions:
    response = requests.post(f"http://localhost:8000/kb-test-questions/{kb_id}/test",
                           params={
                               "question": question["question"],
                               "expected_keywords": ",".join(question["expected_keywords"])
                           }, headers=headers)
    result = response.json()
    print(f"Релевантность: {result['relevance_score']}%")

# Поиск в RAG
search_data = {
    "query": "как рассчитывается трафик",
    "limit": 5
}
response = requests.post("http://localhost:8000/rag/search", json=search_data, headers=headers)
results = response.json()["results"]
```

### JavaScript клиент

```javascript
// Аутентификация
const loginResponse = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'admin', password: 'password'})
});
const {access_token} = await loginResponse.json();

const headers = {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
};

// Создание БЗ
const kbResponse = await fetch('http://localhost:8000/kb-management/knowledge-bases', {
    method: 'POST',
    headers,
    body: JSON.stringify({
        name: 'Техническая документация',
        description: 'Документы по техническим вопросам',
        category: 'Техническая',
        created_by: 'admin'
    })
});
const kb = await kbResponse.json();

// Поиск в RAG
const searchResponse = await fetch('http://localhost:8000/rag/search', {
    method: 'POST',
    headers,
    body: JSON.stringify({
        query: 'как рассчитывается трафик',
        limit: 5
    })
});
const searchResults = await searchResponse.json();
```

## Коды ответов

- `200` - Успешный запрос
- `201` - Ресурс создан
- `400` - Неверный запрос
- `401` - Не авторизован
- `403` - Доступ запрещен
- `404` - Ресурс не найден
- `500` - Внутренняя ошибка сервера

## Интерактивная документация

После запуска API сервера доступна интерактивная документация:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Запуск API сервера

```bash
cd /mnt/ai/cnn/steccom
source .venv/bin/activate
python3 api/run_api.py
```

## Интеграция с другими системами

API предназначен для интеграции с:

- **ai_billing** - получение тестовых вопросов и тестирование релевантности БЗ
- **MediaWiki** - публикация БЗ в вики
- **Внешние системы** - доступ к RAG функциональности через HTTP API
- **Мобильные приложения** - доступ к документам и поиску
- **Веб-интерфейсы** - управление БЗ через REST API
