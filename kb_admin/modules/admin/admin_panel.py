"""
Admin Panel for Knowledge Base Management
Админ-панель для управления базами знаний
"""

import streamlit as st
import os
import sqlite3
from datetime import datetime
from typing import List, Dict
import sys
from pathlib import Path

# Добавляем путь к модулям KB Admin
sys.path.append(str(Path(__file__).parent.parent))

from modules.core.knowledge_manager import KnowledgeBaseManager
from modules.core.pdf_processor import PDFProcessor
from modules.rag.multi_kb_rag import MultiKBRAG
from modules.admin.simple_kb_assistant import SimpleKBAssistant
from modules.admin.kb_workflow import KBWorkflow

class AdminPanel:
    def __init__(self):
        self.kb_manager = KnowledgeBaseManager()
        self.pdf_processor = PDFProcessor()
        # Persist RAG system across reruns using session_state
        if 'admin_rag_system' not in st.session_state:
            st.session_state.admin_rag_system = MultiKBRAG()
        self.rag_system = st.session_state.admin_rag_system
        try:
            self.kb_assistant = SimpleKBAssistant(self.kb_manager, self.pdf_processor)
            self.kb_workflow = KBWorkflow()
        except Exception as e:
            st.error(f"Ошибка инициализации ассистента: {e}")
            self.kb_assistant = None
            self.kb_workflow = None
    
    def render_main_panel(self):
        """Render main admin panel"""
        st.title("🔧 Админ-панель: Управление базами знаний")
        
        # Sidebar navigation
        st.sidebar.title("Навигация")
        page = st.sidebar.selectbox(
            "Выберите раздел:",
            [
                "📊 Обзор",
                "📋 Алгоритм работы с БЗ",
                "🤖 Ассистент создания БЗ",
                "📚 Управление БЗ",
                "📄 Загрузка документов",
                "🔍 Поиск и тестирование",
                "⚙️ Настройки"
            ]
        )
        
        if page == "📊 Обзор":
            self.render_overview()
        elif page == "📋 Алгоритм работы с БЗ":
            if self.kb_workflow:
                self.kb_workflow.render_workflow_guide()
            else:
                st.error("Алгоритм недоступен. Проверьте логи ошибок.")
        elif page == "🤖 Ассистент создания БЗ":
            if self.kb_assistant:
                self.kb_assistant.render_assistant()
            else:
                st.error("Ассистент недоступен. Проверьте логи ошибок.")
        elif page == "📚 Управление БЗ":
            self.render_kb_management()
        elif page == "📄 Загрузка документов":
            self.render_document_upload()
        elif page == "🔍 Поиск и тестирование":
            self.render_search_testing()
        elif page == "⚙️ Настройки":
            self.render_settings()
    
    def render_overview(self):
        """Render overview dashboard"""
        st.header("📊 Обзор системы")
        
        # Load statistics
        stats = self.kb_manager.get_statistics()
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Базы знаний",
                value=stats['total_knowledge_bases'],
                delta=None
            )
        
        with col2:
            st.metric(
                label="Документы",
                value=stats['total_documents'],
                delta=None
            )
        
        with col3:
            st.metric(
                label="Обработано",
                value=stats['processed_documents'],
                delta=None
            )
        
        with col4:
            st.metric(
                label="Процент обработки",
                value=f"{stats['processing_rate']:.1f}%",
                delta=None
            )
        
        # Documents by category
        st.subheader("📈 Документы по категориям")
        if stats['documents_by_category']:
            import pandas as pd
            df = pd.DataFrame(
                list(stats['documents_by_category'].items()),
                columns=['Категория', 'Количество документов']
            )
            st.bar_chart(df.set_index('Категория'))
        else:
            st.info("Нет документов для отображения")
        
        # Recent knowledge bases
        st.subheader("📚 Последние базы знаний")
        kbs = self.kb_manager.get_knowledge_bases()
        
        if kbs:
            for kb in kbs[:5]:  # Show last 5
                with st.expander(f"{kb['name']} ({kb['category']})"):
                    st.write(f"**Описание:** {kb['description']}")
                    st.write(f"**Создано:** {kb['created_at']}")
                    st.write(f"**Автор:** {kb['created_by']}")
                    
                    # Show document count
                    docs = self.kb_manager.get_documents(kb['id'])
                    st.write(f"**Документов:** {len(docs)}")
        else:
            st.info("Нет созданных баз знаний")
    
    def render_kb_management(self):
        """Render knowledge base management"""
        st.header("📚 Управление базами знаний")
        
        # Create new KB
        st.subheader("➕ Создать новую базу знаний")
        
        with st.form("create_kb_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                kb_name = st.text_input("Название БЗ*", placeholder="Технические регламенты")
                kb_category = st.selectbox(
                    "Категория*",
                    ["Технические регламенты", "Пользовательские инструкции", 
                     "Политики безопасности", "Процедуры биллинга", "Другое"]
                )
            
            with col2:
                kb_description = st.text_area("Описание", placeholder="Описание базы знаний")
                created_by = st.text_input("Автор*", value=st.session_state.get('username', 'admin'))
            
            submitted = st.form_submit_button("Создать базу знаний")
            
            if submitted:
                if kb_name and kb_category and created_by:
                    try:
                        kb_id = self.kb_manager.create_knowledge_base(
                            kb_name, kb_description, kb_category, created_by
                        )
                        st.success(f"База знаний '{kb_name}' создана с ID: {kb_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка создания БЗ: {e}")
                else:
                    st.error("Заполните все обязательные поля")
        
        # Manage existing KBs
        st.subheader("📋 Существующие базы знаний")
        
        kbs = self.kb_manager.get_knowledge_bases()
        
        if kbs:
            for kb in kbs:
                with st.expander(f"🗂️ {kb['name']} (ID: {kb['id']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Категория:** {kb['category']}")
                        st.write(f"**Описание:** {kb['description']}")
                        st.write(f"**Создано:** {kb['created_at']}")
                        st.write(f"**Автор:** {kb['created_by']}")
                        
                        # Show documents
                        docs = self.kb_manager.get_documents(kb['id'])
                        st.write(f"**Документов:** {len(docs)}")
                        
                        if docs:
                            st.write("**Документы:**")
                            for doc in docs:
                                status_icon = "✅" if doc['processed'] else "⏳"
                                st.write(f"{status_icon} {doc['title']} ({doc['processing_status']})")
                    
                    with col2:
                        if st.button(f"🗑️ Удалить", key=f"delete_{kb['id']}"):
                            if self.kb_manager.delete_knowledge_base(kb['id']):
                                st.success("База знаний удалена")
                                st.rerun()
                            else:
                                st.error("Ошибка удаления")
                        
                        if st.button(f"🔄 Перезагрузить", key=f"reload_{kb['id']}"):
                            if self.rag_system.reload_kb(kb['id']):
                                st.success("База знаний перезагружена")
                            else:
                                st.error("Ошибка перезагрузки")
        else:
            st.info("Нет созданных баз знаний")
    
    def render_document_upload(self):
        """Render document upload interface"""
        st.header("📄 Загрузка документов")
        
        # Select knowledge base
        kbs = self.kb_manager.get_knowledge_bases()
        
        if not kbs:
            st.warning("Сначала создайте базу знаний в разделе 'Управление БЗ'")
            return
        
        kb_options = {f"{kb['name']} ({kb['category']})": kb['id'] for kb in kbs}
        selected_kb_name = st.selectbox("Выберите базу знаний:", list(kb_options.keys()))
        selected_kb_id = kb_options[selected_kb_name]
        
        # Upload form
        st.subheader("📤 Загрузить PDF документ")
        
        uploaded_file = st.file_uploader(
            "Выберите PDF файл",
            type=['pdf'],
            help="Поддерживаются только PDF файлы"
        )
        
        if uploaded_file:
            # Show file info
            st.write(f"**Файл:** {uploaded_file.name}")
            st.write(f"**Размер:** {uploaded_file.size / 1024:.1f} KB")
            
            # Process file
            if st.button("Обработать документ"):
                with st.spinner("Обработка документа..."):
                    result = self.pdf_processor.process_pdf(
                        uploaded_file, 
                        selected_kb_id, 
                        uploaded_file.name
                    )
                    
                    if result['success']:
                        # Add to database
                        doc_id = self.kb_manager.add_document(
                            selected_kb_id,
                            result['title'],
                            result['file_path'],
                            result['content_type'],
                            result['file_size'],
                            result['metadata']
                        )
                        
                        # Mark as processed
                        self.kb_manager.update_document_status(doc_id, True, 'completed')
                        
                        st.success(f"Документ успешно обработан! ID: {doc_id}")
                        
                        # Show extracted text preview
                        with st.expander("Предварительный просмотр текста"):
                            text_preview = result['text_content'][:1000]
                            st.text(text_preview)
                            if len(result['text_content']) > 1000:
                                st.write("... (текст обрезан)")
                        
                        # Show metadata
                        with st.expander("Метаданные документа"):
                            st.json(result['metadata'])
                    else:
                        st.error(f"Ошибка обработки: {result['error']}")
    
    def render_search_testing(self):
        """Render search and testing interface"""
        st.header("🔍 Поиск и тестирование")
        
        # Auto-load active KBs on first visit (persist across reruns)
        if 'admin_kbs_loaded' not in st.session_state:
            with st.spinner("Автозагрузка активных баз знаний..."):
                loaded_count = self.rag_system.load_all_active_kbs()
                st.session_state.admin_kbs_loaded = True
                st.session_state.admin_loaded_kb_count = loaded_count
                if loaded_count > 0:
                    st.success(f"✅ Автоматически загружено {loaded_count} активных баз знаний")
                else:
                    st.info("ℹ️ Активные базы знаний не найдены")
        
        # Show loaded KBs
        loaded_kbs = self.rag_system.get_available_kbs()
        
        # Debug info
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🔍 Отладка:**")
        st.sidebar.write(f"Загружено БЗ (session): {st.session_state.get('admin_loaded_kb_count', 0)} | (live): {len(loaded_kbs)}")
        if loaded_kbs:
            for kb in loaded_kbs:
                st.sidebar.write(f"• {kb['name']}")
        
        if loaded_kbs:
            st.subheader("📚 Доступные базы знаний")
            
            for kb in loaded_kbs:
                st.write(f"• **{kb['name']}** ({kb['category']}) - {kb['doc_count']} документов, {kb['chunk_count']} фрагментов")
            
            st.markdown("---")
            
            # Search interface with clear instructions
            st.subheader("🔍 Тестовый поиск")
            
            # AI Assistant for generating test questions
            st.markdown("**🤖 Ассистент тестирования БЗ**")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                test_category = st.selectbox(
                    "Выберите категорию для тестирования:",
                    [
                        "Технические требования",
                        "Процедуры настройки", 
                        "Параметры конфигурации",
                        "Требования безопасности",
                        "Стандарты и регламенты",
                        "Случайные вопросы"
                    ]
                )
            
            with col2:
                if st.button("🎯 Сгенерировать вопрос", type="secondary"):
                    # Ensure KBs are loaded before generating question
                    if not loaded_kbs:
                        with st.spinner("Загружаю базы знаний..."):
                            loaded_count = self.rag_system.load_all_active_kbs()
                            if loaded_count > 0:
                                st.success(f"Загружено {loaded_count} баз знаний")
                                loaded_kbs = self.rag_system.get_available_kbs()
                                st.rerun()
                            else:
                                st.error("Не удалось загрузить базы знаний")
                                return
                    
                    # Generate test question based on category and KB content
                    test_question = self._generate_test_question(test_category, loaded_kbs)
                    st.session_state.generated_question = test_question
            
            # Show generated question
            if st.session_state.get('generated_question'):
                st.info(f"**Сгенерированный вопрос:** {st.session_state.generated_question}")
                if st.button("✅ Использовать этот вопрос"):
                    st.session_state.current_test_query = st.session_state.generated_question
            
            st.markdown("---")
            
            st.markdown("""
            **💡 Что можно искать:**
            - Технические требования к оборудованию
            - Процедуры настройки спутниковой связи
            - Параметры конфигурации
            - Требования к безопасности
            - Стандарты и регламенты
            """)
            
            query = st.text_input(
                "Введите ваш вопрос:",
                value=st.session_state.get('current_test_query', ''),
                placeholder="Например: какие требования к антенне для спутниковой связи?"
            )
            
            if query:
                if st.button("🔍 Найти ответ", type="primary"):
                    # Ensure KBs are loaded before searching
                    if not loaded_kbs:
                        with st.spinner("Загружаю базы знаний..."):
                            loaded_count = self.rag_system.load_all_active_kbs()
                            if loaded_count > 0:
                                st.success(f"Загружено {loaded_count} баз знаний")
                                loaded_kbs = self.rag_system.get_available_kbs()
                            else:
                                st.error("Не удалось загрузить базы знаний")
                                return
                    
                    with st.spinner("Ищу информацию..."):
                        # Search across all loaded KBs
                        results = self.rag_system.search_across_kbs(query, k=5)
                        
                        if results:
                            st.subheader("📄 Найденные документы:")
                            
                            for i, doc in enumerate(results, 1):
                                with st.expander(f"📄 {doc.metadata.get('title', 'Документ')} (релевантность: {i})"):
                                    st.write("**Содержимое:**")
                                    st.write(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                                    
                                    st.write("**Источник:**", doc.metadata.get('source', 'Неизвестно'))
                                    st.write("**Категория:**", doc.metadata.get('category', 'Неизвестно'))
                            
                            # Generate AI response
                            st.subheader("🤖 Ответ ИИ:")
                            ai_response = self.rag_system.get_response_with_context(query)
                            st.write(ai_response)
                        else:
                            st.warning("По вашему запросу ничего не найдено. Попробуйте переформулировать вопрос.")
        else:
            st.warning("Нет загруженных баз знаний для поиска.")
            
            if st.button("🔄 Загрузить базы знаний"):
                with st.spinner("Загрузка баз знаний..."):
                    loaded_count = self.rag_system.load_all_active_kbs()
                    if loaded_count > 0:
                        st.success(f"Загружено {loaded_count} баз знаний")
                        st.rerun()
                    else:
                        st.error("Не удалось загрузить базы знаний")
    
    def _generate_test_question(self, category: str, loaded_kbs: list) -> str:
        """Generate test question based on category and KB content"""
        
        # Base questions for each category
        question_templates = {
            "Технические требования": [
                "Какие технические требования к антенне для спутниковой связи?",
                "Какие параметры мощности передатчика требуются?",
                "Какие требования к частотному диапазону?",
                "Какие технические характеристики приемника нужны?",
                "Какие требования к точности позиционирования?"
            ],
            "Процедуры настройки": [
                "Как настроить GPS трекинг устройство?",
                "Какие шаги для настройки спутниковой связи?",
                "Как провести калибровку антенны?",
                "Какая последовательность настройки передатчика?",
                "Как настроить параметры безопасности?"
            ],
            "Параметры конфигурации": [
                "Какие параметры конфигурации для спутниковой связи?",
                "Какие настройки частоты нужно установить?",
                "Какие параметры мощности передатчика?",
                "Какие настройки протокола связи?",
                "Какие параметры буферизации данных?"
            ],
            "Требования безопасности": [
                "Какие требования к шифрованию данных?",
                "Какие стандарты безопасности для спутниковой связи?",
                "Какие требования к аутентификации?",
                "Какие меры защиты от перехвата?",
                "Какие требования к логированию событий?"
            ],
            "Стандарты и регламенты": [
                "Какие стандарты применяются к спутниковой связи?",
                "Какие регламенты по использованию частот?",
                "Какие требования к сертификации оборудования?",
                "Какие стандарты качества связи?",
                "Какие регламенты по электромагнитной совместимости?"
            ],
            "Случайные вопросы": [
                "Что такое спутниковая связь?",
                "Как работает GPS позиционирование?",
                "Какие типы антенн используются?",
                "Что такое SBD протокол?",
                "Как измеряется качество связи?"
            ]
        }
        
        # Get questions for the selected category
        questions = question_templates.get(category, question_templates["Случайные вопросы"])
        
        # If we have KB content, try to make questions more specific
        if loaded_kbs:
            kb_names = [kb['name'] for kb in loaded_kbs]
            kb_categories = [kb['category'] for kb in loaded_kbs]
            
            # Add KB-specific context to questions
            if "Технические регламенты" in kb_categories:
                questions.extend([
                    "Какие требования из технических регламентов к антенне?",
                    "Что говорится в регламентах о мощности передатчика?",
                    "Какие стандарты указаны в технических регламентах?"
                ])
            
            if "Документация СТЭККОМ" in kb_names:
                questions.extend([
                    "Какие требования СТЭККОМ к оборудованию?",
                    "Что указано в документации СТЭККОМ о настройке?",
                    "Какие стандарты СТЭККОМ применяются?"
                ])
        
        # Return a random question from the list
        import random
        return random.choice(questions)
    
    def render_settings(self):
        """Render settings panel"""
        st.header("⚙️ Настройки системы")
        
        st.subheader("🔧 Настройки RAG")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Модели Ollama:**")
            st.write("• all-minilm (embeddings)")
            st.write("• qwen3:8b (chat)")
            
            if st.button("🔄 Перезагрузить RAG систему"):
                self.rag_system.clear_all()
                st.success("RAG система очищена")
        
        with col2:
            st.write("**Провайдер и модель чата:**")
            provider = st.selectbox(
                "Провайдер LLM",
                options=["ollama", "proxyapi", "openai"],
                index=0
            )
            if provider == "ollama":
                model = st.text_input("Модель Ollama", value=os.getenv("OLLAMA_CHAT_MODEL", "qwen3:8b"))
                if st.button("✅ Применить модель", key="apply_ollama_model"):
                    self.rag_system.set_chat_backend(provider="ollama", model=model)
                    st.success(f"Установлена модель Ollama: {model}")
            elif provider == "proxyapi":
                proxy_model = st.text_input("Модель proxyapi", value=os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o"))
                proxy_base = st.text_input("Базовый URL", value=os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1"))
                proxy_key = st.text_input("API ключ", type="password", value=os.getenv("PROXYAPI_API_KEY", os.getenv("OPEN_AI_API_KEY", "")))
                temp = st.slider("Temperature", 0.0, 1.0, float(os.getenv("PROXYAPI_TEMPERATURE", "0.2")), 0.05)
                if st.button("✅ Применить модель", key="apply_proxy_model"):
                    self.rag_system.set_chat_backend(
                        provider="proxyapi", model=proxy_model,
                        base_url=proxy_base, api_key=proxy_key, temperature=temp
                    )
                    st.success(f"Установлена модель proxyapi: {proxy_model}")
            else:
                openai_model = st.text_input("Модель OpenAI", value=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"))
                openai_key = st.text_input("OPENAI_API_KEY", type="password", value=os.getenv("OPENAI_API_KEY", ""))
                temp = st.slider("Temperature", 0.0, 1.0, float(os.getenv("OPENAI_TEMPERATURE", "0.2")), 0.05, key="openai_temp")
                if st.button("✅ Применить модель", key="apply_openai_model"):
                    self.rag_system.set_chat_backend(
                        provider="openai", model=openai_model,
                        api_key=openai_key, temperature=temp
                    )
                    st.success(f"Установлена модель OpenAI: {openai_model}")

            st.markdown("---")
            st.write("**Статистика загруженных БЗ:**")
            stats = self.rag_system.get_kb_statistics()
            st.write(f"• Загружено БЗ: {stats['loaded_kbs']}")
            st.write(f"• Всего документов: {stats['total_documents']}")
            st.write(f"• Всего фрагментов: {stats['total_chunks']}")
        
        # Token usage dashboard
        st.subheader("📊 Потребление токенов")
        try:
            conn = sqlite3.connect("satellite_billing.db")
            c = conn.cursor()
            # Ensure table exists (in case first run without RAG calls)
            c.execute("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    prompt_tokens INTEGER,
                    completion_tokens INTEGER,
                    total_tokens INTEGER,
                    question TEXT,
                    response_length INTEGER
                )
            """)
            # Totals by provider/model
            c.execute(
                """
                SELECT COALESCE(provider, 'unknown') AS prov,
                       COALESCE(model, 'unknown') AS mdl,
                       COALESCE(SUM(prompt_tokens),0),
                       COALESCE(SUM(completion_tokens),0),
                       COALESCE(SUM(total_tokens),0),
                       COUNT(*)
                FROM llm_usage
                GROUP BY prov, mdl
                ORDER BY SUM(total_tokens) DESC
                """
            )
            rows = c.fetchall()
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows, columns=[
                    'Провайдер','Модель','Промпт токены','Ответ токены','Всего токенов','Запросов'
                ])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Пока нет данных по потреблению токенов")

            # Recent usage
            st.markdown("**Последние операции (20):**")
            c.execute(
                """
                SELECT timestamp, provider, model,
                       COALESCE(prompt_tokens,0), COALESCE(completion_tokens,0), COALESCE(total_tokens,0)
                FROM llm_usage
                ORDER BY id DESC LIMIT 20
                """
            )
            recent = c.fetchall()
            if recent:
                import pandas as pd
                df2 = pd.DataFrame(recent, columns=[
                    'Время','Провайдер','Модель','Промпт','Ответ','Всего'
                ])
                st.table(df2)
            conn.close()
        except Exception as e:
            st.error(f"Не удалось загрузить статистику токенов: {e}")

        st.subheader("📁 Файловая система")
        
        # Show upload directory
        upload_dir = self.pdf_processor.upload_dir
        if upload_dir.exists():
            files = list(upload_dir.glob("*.pdf"))
            st.write(f"**Загруженные файлы:** {len(files)}")
            
            if files:
                with st.expander("Список файлов"):
                    for file in files[:10]:  # Show first 10
                        st.write(f"• {file.name} ({file.stat().st_size / 1024:.1f} KB)")
                    if len(files) > 10:
                        st.write(f"... и еще {len(files) - 10} файлов")
        else:
            st.write("Директория загрузок не найдена")
