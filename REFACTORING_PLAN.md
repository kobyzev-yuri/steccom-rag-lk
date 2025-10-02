# 🔧 План рефакторинга проекта STECCOM

## 📊 Анализ дублирования

### 🔍 Обнаруженные проблемы:

#### 1. **Дублированные модули:**
- `modules/rag/multi_kb_rag.py` ↔ `kb_admin/modules/rag/multi_kb_rag.py`
- `modules/rag/rag_helper.py` ↔ `kb_admin/modules/rag/rag_helper.py`
- `modules/integrations/mediawiki_client.py` ↔ `kb_admin/modules/integrations/mediawiki_client.py`
- `modules/admin/admin_panel.py` ↔ `kb_admin/modules/admin/admin_panel.py`
- `modules/admin/knowledge_manager.py` ↔ `kb_admin/modules/admin/knowledge_manager.py`
- `modules/documents/pdf_processor.py` ↔ `kb_admin/modules/documents/pdf_processor.py`
- `modules/documents/ocr_processor.py` ↔ `kb_admin/modules/documents/ocr_processor.py`
- `modules/documents/vision_processor.py` ↔ `kb_admin/modules/documents/vision_processor.py`

#### 2. **Дублированные тесты:**
- `tests/test_kb_effectiveness.py` ↔ `kb_admin/modules/testing/test_kb_effectiveness.py`
- `tests/kb_test_protocol.py` ↔ `kb_admin/modules/testing/kb_test_protocol.py`

#### 3. **Множественные тестовые файлы (21 файл):**
- Много одноразовых тестов в корне проекта
- Дублирование тестовой функциональности

## 🎯 План оптимизации

### Этап 1: Консолидация модулей
1. **Оставить единые модули в `modules/`**
2. **Удалить дублированные модули из `kb_admin/modules/`**
3. **Обновить импорты в KB Admin**

### Этап 2: Очистка тестов
1. **Оставить только существенные тесты:**
   - `tests/test_api.py` - тесты API
   - `tests/test_rag_billing_context.py` - тесты RAG в контексте биллинга
   - `tests/test_rag_with_proxyapi.py` - тесты RAG с ProxyAPI
   - `kb_admin/modules/testing/kb_test_protocol.py` - протокол тестирования KB
   - `kb_admin/modules/testing/test_kb_effectiveness.py` - тесты эффективности KB

2. **Удалить одноразовые тесты:**
   - `test_*.py` в корне проекта (кроме критических)
   - Дублированные тесты

### Этап 3: Оптимизация импортов
1. **Создать единую систему импортов**
2. **Убрать дублирующиеся зависимости**
3. **Оптимизировать requirements.txt**

## 📁 Новая структура

```
steccom/
├── modules/                    # Единые модули
│   ├── core/                  # Основные модули
│   ├── rag/                   # RAG система
│   ├── documents/             # Обработка документов
│   ├── integrations/          # Интеграции
│   ├── admin/                 # Админ функции
│   └── ui/                    # UI компоненты
├── ai_billing/                # AI Billing (использует modules/)
├── kb_admin/                  # KB Admin (использует modules/)
│   ├── modules/               # Только специфичные для KB Admin
│   │   ├── core/              # Специфичные модули KB Admin
│   │   ├── testing/           # Тестирование KB
│   │   └── ui/                # UI KB Admin
│   └── app.py
├── tests/                     # Единые тесты
│   ├── test_api.py
│   ├── test_rag_billing_context.py
│   └── test_rag_with_proxyapi.py
└── requirements.txt           # Единые зависимости
```

## 🚀 Преимущества

1. **Устранение дублирования** - один модуль вместо двух
2. **Упрощение поддержки** - изменения в одном месте
3. **Снижение размера проекта** - меньше файлов
4. **Улучшение производительности** - меньше импортов
5. **Упрощение тестирования** - меньше тестов для поддержки
