щддф# СТЭККОМ API - Быстрая справка

## 🚀 Запуск
```bash
# Запуск API
source .venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Документация
http://localhost:8000/docs
```

## 🔑 Получение токена
```bash
# Через скрипт (рекомендуется)
python get_token.py staff1

# Через curl
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "staff1", "password": "10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6"}'
```

## 📋 Основные команды
```bash
# Переменная с токеном
TOKEN="YOUR_TOKEN_HERE"

# Информация о пользователе
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me

# Текущие договоры
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/agreements/current

# Список устройств
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/devices

# Доступные отчёты
curl http://localhost:8000/reports/available

# Получение отчёта
curl -X POST "http://localhost:8000/reports/standard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "my_devices"}'
```

## 👥 Пользователи
- **staff1** - admin (полный доступ)
- **arctic_user** - user (только свои данные)
- **desert_user** - user (только свои данные)

## 🔧 Пароли (хеши)
- staff1: `10176e7b7b24d317acfcf8d2064cfd2f24e154f7b5a96603077d5ef813d6a6b6`
- arctic_user: `хеш_пароля_arctic`
- desert_user: `хеш_пароля_desert`

## ⏰ Важно
- Токен действителен 30 минут
- После истечения получите новый через `/auth/login`
- Формат заголовка: `Authorization: Bearer TOKEN`

## 🧪 Тестирование
```bash
# Запуск тестов
pytest tests/test_api.py -v

# Проверка здоровья
curl http://localhost:8000/health
```

## 📖 Документация
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🧠 Умный помощник (RAG) и SQL‑агент
- **Умный помощник (RAG)**:
  - Доступен и в пользовательском кабинете, и в админ‑панели (вкладка «🤖 Умный помощник»).
  - Отвечает по документации/KB, не выполняет SQL.
  - Ролевая модель сейчас одинакова по функционалу; в будущем возможны ограничения по корпоративным секретам.
- **SQL‑агент**:
  - Для пользователя: раздел «Пользовательский запрос» — генерирует SQL и выполняет его для данных своей компании.
  - Для администратора: «AI Query Assistant» в админ‑панели — генерирует SQL и выполняет его по выбранной компании или по всем компаниям.
  - RAG‑контент не смешивается с SQL‑агентом, чтобы избежать путаницы.
  - Фильтры доступа: админ видит все компании (или может выбрать конкретную), пользователь — только свою.

### Примечания по данным и UI
- Кнопка «Скачать CSV» находится под таблицей результатов.
- DEBUG‑сообщения в UI отключены.
- Генерация тестовых VSAT_VOICE сессий вынесена в скрипт:
  ```bash
  python /mnt/ai/cnn/steccom/scripts/generate_vsat_voice_data.py
  ```
