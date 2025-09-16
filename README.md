# steccom-rag-lk

Streamlit‑приложение: личный кабинет + админка для управления базами знаний и RAG.

Основное:
- Мультиязычные эмбеддинги (HuggingFace `intfloat/multilingual-e5-base`) + FAISS
- Провайдеры LLM: Ollama / proxyapi / OpenAI (переключение в админ‑настройках)
- Надёжная обработка PDF (PyPDF2 → PyMuPDF → плейсхолдер)
- Гибридный поиск: векторный + ключевой
- Учёт токенов в SQLite (`llm_usage`) и статистика в админке

## Установка
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ENV (минимум для эмбеддингов)
```bash
export EMBEDDING_PROVIDER=hf
export EMBEDDING_MODEL="intfloat/multilingual-e5-base"
# при необходимости
export HUGGINGFACE_HUB_TOKEN="hf_..."
```
Провайдеры чата (опционально):
- Ollama (дефолт)
```bash
export OLLAMA_CHAT_MODEL="qwen3:8b"
```
- proxyapi
```bash
export USE_PROXYAPI=true
export PROXYAPI_BASE_URL="https://api.proxyapi.ru/openai/v1"
export PROXYAPI_API_KEY="..."     # или OPEN_AI_API_KEY
export PROXYAPI_CHAT_MODEL="gpt-4o"
```
- OpenAI
```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_CHAT_MODEL="gpt-4o-mini"
```

## Запуск
```bash
source .venv/bin/activate
streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
```

## Архитектура
- `modules/rag/multi_kb_rag.py` — Multi‑KB RAG, загрузка активных БЗ, FAISS, гибридный поиск, ответ с контекстом
- `modules/admin/admin_panel.py` — админка: управление БЗ, загрузка PDF, тестирование, выбор провайдера, статистика токенов
- `modules/documents/pdf_processor.py` — парсинг PDF, фоллбеки
- `rag_helper.py` — облегчённый RAG (HF‑эмбеддинги), для совместимости части UI
- `satellite_billing.db` — SQLite (метаданные БЗ, токены, и др.)

## Примечания
- Пересборка индекса при перезагрузке БЗ/системы в админке
- Русские документы лучше работают с HF‑эмбеддером

