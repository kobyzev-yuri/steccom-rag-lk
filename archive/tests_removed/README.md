# 📦 Архив удаленных тестов

## 📋 Описание

Эта директория содержит тестовые файлы, которые были удалены из основного проекта в рамках оптимизации.

## 🗂️ Содержимое

### Одноразовые тесты (15 файлов):
- `test_sql_speed.py` - тест скорости SQL генерации
- `test_simple_sql.py` - простой тест SQL
- `test_sql_assistant.py` - тест SQL ассистента
- `test_docx_processing.py` - тест обработки DOCX
- `test_kb_save.py` - тест сохранения KB
- `test_ocr_cleaning.py` - тест очистки OCR
- `test_gemini_vision.py` - тест Gemini Vision
- `test_ocr_agent.py` - тест OCR агента
- `test_improved_ocr_cleaning.py` - улучшенная очистка OCR
- `test_vision_integration.py` - интеграция Vision
- `test_smart_librarian_fix.py` - исправление Smart Librarian
- `test_document_management.py` - управление документами
- `test_smart_librarian.py` - Smart Librarian
- `test_pdf_processing.py` - обработка PDF
- `test_ocr_standalone.py` - автономный OCR

## 🎯 Причина удаления

Эти тесты были удалены потому что:

1. **Одноразовые** - использовались для разовой проверки функциональности
2. **Дублирующие** - тестировали уже покрытую функциональность
3. **Устаревшие** - не обновлялись с изменениями в коде
4. **Не интегрированные** - не входили в основную тестовую систему

## 🔄 Восстановление

Если потребуется восстановить какой-либо тест:

```bash
# Восстановить конкретный тест
cp archive/tests_removed/test_example.py ./

# Восстановить все тесты
cp archive/tests_removed/test_*.py ./
```

## 📊 Статистика

- **Удалено файлов:** 15
- **Освобождено места:** ~500KB
- **Упрощено поддержки:** Значительно
- **Оставлено активных тестов:** 5

## ✅ Оставленные тесты

Активные тесты остались в:
- `tests/test_api.py` - тесты API
- `tests/test_rag_billing_context.py` - тесты RAG в контексте биллинга
- `tests/test_rag_with_proxyapi.py` - тесты RAG с ProxyAPI
- `tests/test_gpt4o_proxyapi.py` - тесты GPT-4o с ProxyAPI
- `kb_admin/modules/testing/` - тесты KB Admin
