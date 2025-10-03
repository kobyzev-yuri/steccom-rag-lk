# 🛰️ СТЭККОМ - Система спутниковой связи

## 📁 Структура проекта

```
steccom/
├── app.py                    # 🚀 Главный файл приложения
├── api/                      # 🌐 REST API сервер
│   ├── run_api.py           # 🚀 FastAPI сервер
│   └── __init__.py
├── modules/                  # 📦 Все модули системы
│   ├── core/                # ⚙️ Основные модули
│   │   ├── database.py      # 🗄️ Работа с БД
│   │   ├── queries.py       # 📊 SQL запросы
│   │   ├── rag.py          # 🤖 RAG функции
│   │   └── utils.py        # 🔧 Утилиты
│   ├── ui/                  # 🎨 UI компоненты
│   │   └── ui_components.py
│   ├── admin/               # 👨‍💼 Админ функции
│   ├── documents/           # 📄 Обработка документов
│   └── rag/                # 🧠 Расширенные RAG
├── config/                  # ⚙️ Конфигурация
├── data/                    # 📁 Данные и файлы
├── docs/                    # 📚 Документация
├── logs/                    # 📝 Логи
├── scripts/                 # 🔧 Скрипты
├── run_api_server.py        # 🚀 Скрипт запуска API
├── test_api.py              # 🧪 Тестирование API
└── requirements.txt         # 📋 Зависимости
```

## 🚀 Запуск

### Веб-интерфейс (Streamlit)
```bash
streamlit run app.py
```

### REST API сервер
```bash
# Вариант 1: Прямой запуск
python api/run_api.py

# Вариант 2: Через скрипт
python run_api_server.py

# Вариант 3: Через uvicorn
uvicorn api.run_api:app --host 0.0.0.0 --port 8000 --reload
```

**API будет доступен по адресу**: http://localhost:8000  
**Документация API**: http://localhost:8000/docs

## 📚 Документация

- [Структура модулей](docs/README_STRUCTURE.md)
- [Схема БД](docs/DATABASE_SCHEMA.md)
- [Модули](docs/README_MODULES.md)
- [API документация](docs/API_DOCUMENTATION.md)

## 🎯 Основные функции

- 📊 **Стандартные отчеты** - готовые отчеты по трафику
- 📝 **Пользовательские запросы** - SQL из естественного языка
- 🤖 **Умный помощник** - RAG система для документации
- 👨‍💼 **Админ-панель** - управление системой
- 🌐 **REST API** - программный доступ к функциям системы

## 🔧 Технологии

- **Streamlit** - веб-интерфейс
- **FastAPI** - REST API сервер
- **SQLite** - база данных
- **OpenAI** - генерация SQL
- **RAG** - поиск по документации
- **Plotly** - графики и диаграммы
