"""
Main Interface for KB Admin
Главный интерфейс системы управления базами знаний
"""

import streamlit as st
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Добавляем путь к модулям KB Admin
sys.path.append(str(Path(__file__).parent.parent))

from modules.core.knowledge_manager import KnowledgeBaseManager
from modules.core.text_analyzer import TextAnalyzer
from modules.core.chunk_optimizer import ChunkOptimizer
from modules.rag.multi_kb_rag import MultiKBRAG
from modules.documents.pdf_processor import PDFProcessor
from modules.testing.kb_test_protocol import KBTestProtocol
from modules.integrations.mediawiki_client import MediaWikiClient
from modules.admin.admin_panel import AdminPanel
from modules.ui.pdf_upload_interface import PDFUploadInterface
from modules.core.smart_document_agent import SmartLibrarian
from modules.ui.settings_page import render_settings_page
from modules.ui.agent_model_manager import AgentModelManager


class KBAdminInterface:
    """Главный интерфейс KB Admin"""
    
    def __init__(self):
        self.kb_manager = KnowledgeBaseManager()
        self.text_analyzer = TextAnalyzer()
        self.chunk_optimizer = ChunkOptimizer()
        self.pdf_processor = PDFProcessor()
        self.protocol = KBTestProtocol()
        self.admin_panel = AdminPanel()
        self.pdf_upload_interface = PDFUploadInterface(self.kb_manager, self.pdf_processor)
        self.smart_librarian = SmartLibrarian(self.kb_manager, self.pdf_processor)
        self.model_manager = AgentModelManager()
        
        # Инициализация RAG системы
        if 'kb_admin_rag' not in st.session_state:
            st.session_state.kb_admin_rag = MultiKBRAG()
        self.rag = st.session_state.kb_admin_rag
        
        # Инициализация MediaWiki клиента
        try:
            self.mediawiki_client = MediaWikiClient(
                "http://localhost:8080/api.php",
                username="admin",
                password="Admin123456789"
            )
        except Exception as e:
            print(f"Ошибка инициализации MediaWiki клиента: {e}")
            self.mediawiki_client = None
    
    def render_main_page(self):
        """Рендер главной страницы"""
        st.set_page_config(
            page_title="KB Admin - Управление базами знаний",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Заголовок
        st.title("🧠 KB Admin - Управление базами знаний")
        st.markdown("---")
        
        # Боковая панель навигации
        self._render_sidebar()
        
        # Основной контент
        self._render_main_content()
    
    def _render_sidebar(self):
        """Рендер боковой панели"""
        with st.sidebar:
            st.header("🧭 Навигация")
            
            # Выбор страницы
            page_options = [
                "📊 Обзор системы",
                "📚 Умный библиотекарь",
                "🔧 Админ-панель (AI Billing)",
                "📚 Управление KB",
                "🤖 Управление моделями",
                "⚙️ Настройки"
            ]
            
            # Инициализируем текущую страницу если её нет
            if 'current_page' not in st.session_state:
                st.session_state.current_page = "📊 Обзор системы"
            
            # Находим индекс текущей страницы
            current_index = page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0
            
            page = st.selectbox(
                "Выберите раздел:",
                page_options,
                index=current_index
            )
            
            # Обновляем только если страница изменилась
            if page != st.session_state.current_page:
                st.session_state.current_page = page
            
            # Статистика
            st.markdown("---")
            st.header("📊 Статистика")
            self._render_sidebar_stats()
            
            # Быстрые действия
            st.markdown("---")
            st.header("⚡ Быстрые действия")
            self._render_quick_actions()
    
    def _render_sidebar_stats(self):
        """Рендер статистики в боковой панели"""
        try:
            # Кэшируем статистику, чтобы избежать мигания
            if 'kb_stats_cache' not in st.session_state:
                st.session_state.kb_stats_cache = self.kb_manager.get_statistics()
            
            stats = st.session_state.kb_stats_cache
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Базы знаний", stats['total_knowledge_bases'])
                st.metric("Документы", stats['total_documents'])
            
            with col2:
                st.metric("Обработано", stats['processed_documents'])
                st.metric("Процент", f"{stats['processing_rate']:.1f}%")
            
        except Exception as e:
            st.error(f"Ошибка загрузки статистики: {e}")
    
    def _render_quick_actions(self):
        """Рендер быстрых действий"""
        if st.button("🔄 Обновить RAG", key="refresh_rag_btn"):
            try:
                self.rag.load_all_active_kbs()
                st.success("RAG система обновлена!")
            except Exception as e:
                st.error(f"Ошибка обновления: {e}")
        
        if st.button("📊 Запустить тесты", key="run_tests_btn"):
            st.session_state.run_tests = True
        
        if st.button("🧹 Очистить кэш", key="clear_cache_btn"):
            if 'kb_admin_rag' in st.session_state:
                del st.session_state.kb_admin_rag
            if 'kb_stats_cache' in st.session_state:
                del st.session_state.kb_stats_cache
            st.success("Кэш очищен!")
        
        if st.button("📊 Обновить статистику", key="refresh_stats_btn"):
            if 'kb_stats_cache' in st.session_state:
                del st.session_state.kb_stats_cache
            st.success("Статистика обновлена!")
    
    def _render_main_content(self):
        """Рендер основного контента"""
        page = st.session_state.get('current_page', '📊 Обзор системы')
        
        if page == "📊 Обзор системы":
            self._render_overview()
        elif page == "📚 Умный библиотекарь":
            self._render_smart_librarian()
        elif page == "🔧 Админ-панель (AI Billing)":
            self._render_admin_panel()
        elif page == "📚 Управление KB":
            self._render_kb_management()
        # Создание/расширение БЗ теперь входит в поток "Умный библиотекарь"
        elif page == "⚙️ Настройки":
            self._render_settings()
        elif page == "🤖 Управление моделями":
            self._render_model_management()
    
    def _render_overview(self):
        """Рендер обзора системы"""
        st.header("📊 Обзор системы KB Admin")
        
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            stats = self.kb_manager.get_statistics()
            
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
                    delta=f"{stats['processing_rate']:.1f}%"
                )
            
            with col4:
                # Статус RAG системы
                rag_status = "🟢 Активна" if hasattr(self.rag, 'vectorstores') and len(self.rag.vectorstores) > 0 else "🔴 Неактивна"
                st.metric(
                    label="RAG система",
                    value=rag_status,
                    delta=None
                )
        
        except Exception as e:
            st.error(f"Ошибка загрузки статистики: {e}")
        
        # Графики и диаграммы
        st.markdown("---")
        st.subheader("📈 Аналитика")
        
        try:
            self._render_analytics_charts()
        except Exception as e:
            st.error(f"Ошибка загрузки аналитики: {e}")
        
        # Последние действия
        st.markdown("---")
        st.subheader("🕒 Последние действия")
        self._render_recent_activities()
    
    def _render_analytics_charts(self):
        """Рендер аналитических графиков"""
        try:
            stats = self.kb_manager.get_statistics()
            
            # График по категориям
            if stats['documents_by_category']:
                import plotly.express as px
                
                categories = list(stats['documents_by_category'].keys())
                counts = list(stats['documents_by_category'].values())
                
                fig = px.pie(
                    values=counts,
                    names=categories,
                    title="Распределение документов по категориям"
                )
                st.plotly_chart(fig, width='stretch')
            
        except Exception as e:
            st.warning(f"Не удалось загрузить графики: {e}")
    
    def _render_recent_activities(self):
        """Рендер последних действий"""
        # Заглушка для последних действий
        activities = [
            {"time": "10:30", "action": "Создана KB 'Технические регламенты'", "user": "admin"},
            {"time": "09:45", "action": "Загружен документ 'reg_sbd.pdf'", "user": "admin"},
            {"time": "09:15", "action": "Запущено тестирование релевантности", "user": "admin"},
        ]
        
        for activity in activities:
            st.write(f"🕒 **{activity['time']}** - {activity['action']} ({activity['user']})")
    
    def _render_kb_management(self):
        """Рендер управления KB"""
        st.header("📚 Управление базами знаний")
        
        # Создание новой KB
        with st.expander("➕ Создать новую базу знаний", expanded=False):
            self._render_create_kb_form()
        
        # Список существующих KB
        st.subheader("📋 Существующие базы знаний")
        self._render_kb_list()
    
    def _render_create_kb_form(self):
        """Рендер формы создания KB"""
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
                created_by = st.text_input("Автор*", value="admin")
            
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
    
    def _render_kb_list(self):
        """Рендер списка KB"""
        try:
            kbs = self.kb_manager.get_knowledge_bases()
            
            if not kbs:
                st.info("Базы знаний не найдены. Создайте первую БЗ.")
                return
            
            for kb in kbs:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{kb['name']}**")
                        st.caption(kb['description'] or "Без описания")
                    
                    with col2:
                        st.write(f"📁 {kb['category']}")
                        st.caption(f"Создана: {kb['created_at'][:10]}")
                    
                    with col3:
                        docs = self.kb_manager.get_documents(kb['id'])
                        st.write(f"📄 {len(docs)} документов")
                    
                    with col4:
                        if st.button("⚙️", key=f"manage_{kb['id']}"):
                            st.session_state.selected_kb = kb['id']
                    
                    st.markdown("---")
        
        except Exception as e:
            st.error(f"Ошибка загрузки списка KB: {e}")
    
    def _render_document_upload(self):
        """Рендер загрузки документов"""
        st.header("📄 Загрузка документов")
        st.info("Загрузите PDF документы для создания или расширения базы знаний")
        
        # Используем функционал из админ-панели
        if hasattr(self.admin_panel, 'render_document_upload'):
            self.admin_panel.render_document_upload()
        else:
            st.error("Функционал загрузки документов недоступен")
    
    def _render_text_analysis(self):
        """Рендер анализа текста"""
        st.header("🔍 Анализ структуры текста")
        st.info("Функционал анализа текста будет реализован в следующем модуле")
    
    def _render_chunk_optimization(self):
        """Рендер оптимизации чанков"""
        st.header("⚙️ Оптимизация разбиения на чанки")
        st.info("Функционал оптимизации чанков будет реализован в следующем модуле")
    
    def _render_relevance_testing(self):
        """Рендер тестирования релевантности"""
        from .testing_interface import TestingInterface
        testing_interface = TestingInterface()
        testing_interface.render_testing_interface()
    
    def _render_configuration_comparison(self):
        """Рендер сравнения конфигураций"""
        st.header("📈 Сравнение конфигураций")
        st.info("Функционал сравнения конфигураций будет реализован в следующем модуле")
    
    def _render_integrations(self):
        """Рендер интеграций"""
        st.header("🔗 Интеграции")
        st.info("Функционал интеграций будет реализован в следующем модуле")
    
    def _render_smart_librarian(self):
        """Рендер Умного библиотекаря"""
        # Приветствие
        self.smart_librarian.render_welcome()
        
        # Основной интерфейс
        st.markdown("---")
        # Всегда показываем поток анализа документов;
        # создание/расширение KB выполняется после анализа в соответствующих шагах
        self._render_document_analysis()
    
    def _render_document_analysis(self):
        """Анализ документов"""
        st.subheader("🔍 Анализ документов")
        
        # Инициализируем состояние анализа
        if 'analysis_in_progress' not in st.session_state:
            st.session_state.analysis_in_progress = False
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        if 'selected_files' not in st.session_state:
            st.session_state.selected_files = []
        if 'doc_status' not in st.session_state:
            st.session_state.doc_status = None
        
        # Отладочная информация о состоянии (можно убрать после тестирования)
        # st.write(f"🔍 DEBUG: analysis_in_progress = {st.session_state.analysis_in_progress}")
        # st.write(f"🔍 DEBUG: analysis_results = {st.session_state.analysis_results is not None}")
        # st.write(f"🔍 DEBUG: selected_files = {len(st.session_state.selected_files)}")
        
        # Получаем статус документов, обновляем при смене upload_dir
        current_upload_dir = str(self.smart_librarian.document_manager.upload_dir)
        if st.session_state.doc_status is None or st.session_state.get('last_upload_dir_for_analysis') != current_upload_dir:
            st.session_state.doc_status = self.smart_librarian.document_manager.scan_upload_directory()
            st.session_state.last_upload_dir_for_analysis = current_upload_dir
        
        doc_status = st.session_state.doc_status
        
        # Если анализ уже выполнен, показываем результаты
        if st.session_state.analysis_in_progress and st.session_state.analysis_results:
            st.success("✅ Анализ документов завершен!")
            self._display_analysis_results()
            return
        
        # Если анализ запущен, но не завершен, показываем процесс
        if st.session_state.analysis_in_progress and not st.session_state.analysis_results:
            st.info("🔄 Анализ документов в процессе...")
            
            # Кнопка для сброса "застрявшего" анализа
            if st.button("🔄 Сбросить анализ", key="reset_stuck_analysis_btn"):
                st.session_state.analysis_in_progress = False
                st.session_state.analysis_results = None
                st.session_state.selected_files = []
                st.session_state.doc_status = None
                st.rerun()
            
            self._display_analysis_results()
            return
        
        # Показываем новые документы
        if doc_status['new']:
            st.subheader("🆕 Новые документы")
            st.info(f"Найдено {len(doc_status['new'])} новых документов для анализа")
            
            # Показываем чекбоксы для выбора файлов
            for doc in doc_status['new']:
                file_path = Path(doc['file_path'])
                checkbox_key = f"analyze_new_{doc['file_name']}"
                
                st.checkbox(f"📄 {doc['file_name']} ({doc['file_size']/1024:.1f} KB)", 
                           key=checkbox_key)
            
            # Собираем выбранные файлы
            selected_files = []
            for doc in doc_status['new']:
                file_path = Path(doc['file_path'])
                checkbox_key = f"analyze_new_{doc['file_name']}"
                if st.session_state.get(checkbox_key, False):
                    selected_files.append(file_path)
            
            # Показываем кнопку анализа
            if selected_files:
                
                # Пробуем альтернативный подход с form
                with st.form("analyze_form", clear_on_submit=False):
                    st.write("**Готов к анализу:**")
                    for file_path in selected_files:
                        st.write(f"📄 {file_path.name}")
                    
                    submitted = st.form_submit_button("🧠 Анализировать новые документы", type="primary")
                    
                    if submitted:
                        st.session_state.analysis_in_progress = True
                        st.session_state.selected_files = selected_files
                        st.rerun()
            else:
                st.warning("⚠️ Выберите хотя бы один документ для анализа")
        
        # Показываем обработанные документы
        if doc_status['processed']:
            st.subheader("✅ Обработанные документы")
            st.success(f"Найдено {len(doc_status['processed'])} обработанных документов")
            
    def _display_analysis_results(self):
        """Отображение результатов анализа"""
        if not st.session_state.analysis_results:
            # Выполняем анализ
            selected_files = st.session_state.get('selected_files', [])
            if selected_files:
                try:
                    with st.spinner("Анализируем документы..."):
                        # Используем новый функционал SmartLibrarian с полным отображением
                        results = self.smart_librarian.process_documents_smart(selected_files)
                        st.session_state.analysis_results = results
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Ошибка анализа: {e}")
                    # Сбрасываем состояние при ошибке
                    st.session_state.analysis_in_progress = False
                    st.session_state.analysis_results = None
            else:
                st.error("❌ Нет выбранных файлов для анализа")
            return
        
        # Новый функционал уже отображается в process_documents_smart
        # Здесь показываем только дополнительную информацию
        results = st.session_state.analysis_results
        
        if results:
            st.subheader("📊 Дополнительная информация")
            
            # Показываем общую информацию
            analyses = results.get('analyses', [])
            strategy = results.get('strategy', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Обработано документов:** {len(analyses)}")
            
            with col2:
                if strategy:
                    st.info(f"**Рекомендуемая стратегия:** {strategy.get('type', 'Не определена')}")
            
            # Кнопка для сброса результатов
            if st.button("🔄 Начать новый анализ", key="reset_analysis"):
                st.session_state.analysis_results = None
                st.session_state.analysis_in_progress = False
                st.rerun()
            
            # Показываем кнопки создания БЗ и тестирования релевантности
            st.write(f"🔍 DEBUG: Проверяем стратегию: {strategy is not None}")
            if strategy:
                st.write(f"🔍 DEBUG: Тип стратегии: {strategy.get('type')}")
            
            if strategy and strategy.get('type') != 'no_documents':
                st.markdown("---")
                st.subheader("🎯 Действия с базой знаний")
                st.write(f"🔍 DEBUG: Стратегия найдена, тип: {strategy.get('type')}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("🔍 DEBUG: Отображаем кнопку 'Создать новую БЗ'")
                    if st.button("🚀 Создать новую БЗ", key="create_kb_from_analysis"):
                        # Создаем БЗ на основе стратегии
                        try:
                            st.write(f"🔍 DEBUG: Стратегия для создания БЗ: {strategy}")
                            
                            if strategy['type'] == 'single_kb':
                                self._create_kb_from_strategy(strategy)
                            elif strategy['type'] == 'mixed_kb':
                                self._create_kb_from_strategy(strategy)
                            else:
                                st.warning("Сложная стратегия - используйте Smart Librarian для создания БЗ")
                        except Exception as e:
                            st.error(f"Ошибка создания БЗ: {e}")
                            import traceback
                            st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
                
                with col2:
                    st.write("🔍 DEBUG: Отображаем блок 'Добавить в существующую БЗ'")
                    # Добавить в существующую БЗ
                    try:
                        existing = self.kb_manager.get_knowledge_bases(active_only=True) or []
                        if existing:
                            kb_options = {f"ID {kb['id']}: {kb['name']}": kb['id'] for kb in existing}
                            selected_kb = st.selectbox("Выберите БЗ:", list(kb_options.keys()), key="select_existing_kb")
                            if st.button("➕ Добавить в БЗ", key="add_to_existing_kb"):
                                self._process_documents_to_kb(strategy.get('documents', []), kb_options[selected_kb])
                                st.success("Документы добавлены в БЗ")
                        else:
                            st.info("Нет активных БЗ")
                    except Exception as e:
                        st.error(f"Ошибка добавления в БЗ: {e}")
                
                with col3:
                    st.write("🔍 DEBUG: Отображаем кнопку 'Тестовые вопросы'")
                    if st.button("🧪 Тестовые вопросы", key="generate_test_questions"):
                        # Генерируем тестовые вопросы
                        try:
                            # Получаем анализы из session_state
                            analyses = st.session_state.analysis_results.get('analyses', [])
                            st.write(f"🔍 DEBUG: Найдено анализов: {len(analyses)}")
                            
                            if analyses:
                                # Берем первый анализ
                                first_analysis = analyses[0]
                                st.write(f"🔍 DEBUG: Первый анализ содержит ключи: {list(first_analysis.keys())}")
                                st.write(f"🔍 DEBUG: Содержимое анализа: {first_analysis}")
                                
                                with st.spinner("Генерируем тестовые вопросы..."):
                                    try:
                                        test_questions = self.smart_librarian.generate_relevance_test_questions(first_analysis)
                                        st.write(f"🔍 DEBUG: Получено вопросов: {len(test_questions) if test_questions else 0}")
                                        
                                        if test_questions:
                                            st.session_state.generated_test_questions = test_questions
                                            st.success(f"✅ Сгенерировано {len(test_questions)} вопросов")
                                            st.rerun()
                                        else:
                                            st.warning("⚠️ Не удалось сгенерировать вопросы")
                                    except Exception as e:
                                        st.error(f"❌ Ошибка при генерации вопросов: {e}")
                                        import traceback
                                        st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
                            else:
                                st.error("❌ Нет данных анализа в результатах")
                        except Exception as e:
                            st.error(f"❌ Ошибка генерации вопросов: {e}")
                            import traceback
                            st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
                
                # Показываем тестовые вопросы с ответами
                if st.session_state.get('generated_test_questions'):
                    st.markdown("---")
                    st.subheader("🧪 Тестовые вопросы с ответами на основе анализа документа")
                    questions = st.session_state.generated_test_questions
                    st.write(f"🔍 DEBUG: Сгенерировано {len(questions)} тестовых вопросов с ответами")
                    
                    st.info("💡 Эти вопросы и ответы основаны на анализе документа. После создания БЗ можно будет протестировать, как хорошо RAG система отвечает на эти вопросы.")
                    
                    # Показываем вопросы с ответами
                    for i, question in enumerate(questions, 1):
                        with st.expander(f"❓ Вопрос {i}: {question['question']}"):
                            # Показываем ответ, если он есть
                            if 'answer' in question and question['answer']:
                                st.write("**📝 Ответ на основе анализа документа:**")
                                st.write(question['answer'])
                            else:
                                st.write("**📝 Ответ:** Информация не найдена в документе")
                            
                            # Показываем дополнительную информацию
                            if 'source_info' in question and question['source_info']:
                                st.write(f"**🔍 Источник:** {question['source_info']}")
                            
                            st.write(f"**Категория:** {question.get('category', 'Не указана')}")
                            st.write(f"**Сложность:** {question.get('difficulty', 'Не указана')}")
                            st.write(f"**Ключевые слова:** {', '.join(question.get('expected_keywords', []))}")
                    
                    st.success("✅ Вопросы с ответами готовы. После создания БЗ можно будет протестировать RAG систему.")
            
            # Показываем детали по каждому документу
            for i, analysis in enumerate(analyses):
                # Инициализируем состояние выбора документа
                if f"selected_doc_{i}" not in st.session_state:
                    st.session_state[f"selected_doc_{i}"] = False
                
                with st.expander(f"📄 {analysis.get('file_name', 'Неизвестный файл')} ({analysis.get('category', 'Не определена')})"):
                    # Чекбокс для выбора документа
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        selected = st.checkbox(
                            "✅ Выбрать для KB", 
                            value=st.session_state[f"selected_doc_{i}"],
                            key=f"select_doc_{i}"
                        )
                        st.session_state[f"selected_doc_{i}"] = selected
                    
                    with col2:
                        if selected:
                            st.success("📌 Документ выбран для сохранения в KB")
                        else:
                            st.info("📋 Документ не выбран")
                    
                    # Показываем абстракт
                    if 'smart_summary' in analysis and analysis['smart_summary']:
                        st.write("**🧠 Абстракт документа:**")
                        st.text_area("Абстракт", value=analysis['smart_summary'], height=200, disabled=True, key=f"abstract_{i}")
                    
                    # Показываем полный текст документа
                    full_text = None
                    if 'original_cleaned_text' in analysis and analysis['original_cleaned_text']:
                        full_text = analysis['original_cleaned_text']
                    elif 'full_cleaned_text' in analysis and analysis['full_cleaned_text']:
                        full_text = analysis['full_cleaned_text']
                    elif 'raw_ocr_text' in analysis and analysis['raw_ocr_text']:
                        full_text = analysis['raw_ocr_text']
                    
                    if full_text:
                        st.write("**📄 Полный текст документа:**")
                        # Показываем первые 2000 символов с возможностью развернуть
                        preview_text = full_text[:2000] + "..." if len(full_text) > 2000 else full_text
                        st.text_area("Полный текст", value=preview_text, height=300, disabled=True, key=f"full_text_{i}")
                        
                        if len(full_text) > 2000:
                            st.info(f"📊 Показано 2000 из {len(full_text)} символов. Полный текст будет сохранен в БЗ.")
                    else:
                        st.warning("⚠️ Полный текст документа недоступен")
                    
                    # Показываем рекомендации по чанкингу
                    if 'chunking_recommendations' in analysis and analysis['chunking_recommendations']:
                        st.write("**📏 Рекомендации по разбиению на чанки:**")
                        st.text_area("Рекомендации", value=analysis['chunking_recommendations'], height=100, disabled=True, key=f"chunking_{i}")
                    
                    # Показываем рекомендации по обработке
                    if 'recommendations' in analysis and analysis['recommendations']:
                        st.write("**💡 Рекомендации по обработке:**")
                        for rec in analysis['recommendations']:
                            st.write(f"• {rec}")
                    
                    # Показываем предложение по KB из стратегии
                    strategy = st.session_state.analysis_results.get('strategy', {})
                    if strategy and strategy.get('type') != 'no_documents':
                        st.write("**🎯 Предложение по созданию KB:**")
                        st.write(f"• **Название:** {strategy.get('kb_name', 'Не указано')}")
                        st.write(f"• **Категория:** {strategy.get('category', 'Не указана')}")
                        st.write(f"• **Описание:** {strategy.get('description', 'Не указано')}")
                        st.write(f"• **Тип стратегии:** {strategy.get('type', 'Не определен')}")
                        st.write(f"• **Обоснование:** {strategy.get('reasoning', 'Не указано')}")
                    elif 'suggested_kb' in analysis and analysis['suggested_kb']:
                        st.write("**🎯 Предложение по созданию KB (из анализа):**")
                        kb_suggestion = analysis['suggested_kb']
                        st.write(f"• **Название:** {kb_suggestion.get('name', 'Не указано')}")
                        st.write(f"• **Категория:** {kb_suggestion.get('category', 'Не указана')}")
                        st.write(f"• **Описание:** {kb_suggestion.get('description', 'Не указано')}")
                    
                # Автоматически генерируем тестовые вопросы после анализа
                if not st.session_state.get('generated_test_questions'):
                    st.write("**🧪 Генерируем тестовые вопросы с ответами на основе анализа документа...**")
                    with st.spinner("Создаем тестовые вопросы с ответами..."):
                        try:
                            st.write(f"🔍 DEBUG: Генерируем вопросы для документа: {analysis.get('file_name', 'Неизвестно')}")
                            st.write(f"🔍 DEBUG: Размер документа: {len(analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', '')))} символов")
                            
                            test_questions = self.smart_librarian.generate_relevance_test_questions(analysis)
                            
                            st.write(f"🔍 DEBUG: Получено вопросов: {len(test_questions) if test_questions else 0}")
                            if test_questions:
                                st.write(f"🔍 DEBUG: Первый вопрос: {test_questions[0].get('question', 'Нет вопроса')}")
                                st.write(f"🔍 DEBUG: Первый ответ: {test_questions[0].get('answer', 'Нет ответа')}")
                            
                            if test_questions:
                                st.session_state.generated_test_questions = test_questions
                                st.success(f"✅ Сгенерировано {len(test_questions)} тестовых вопросов с ответами")
                                st.rerun()  # Перезагружаем страницу для отображения вопросов
                            else:
                                st.error("❌ НЕ УДАЛОСЬ сгенерировать тестовые вопросы на основе анализа документа!")
                                st.error("❌ Система НЕ ИСПОЛЬЗУЕТ шаблонные вопросы - требуется реальный анализ текста!")
                                st.info("💡 Проверьте логи для диагностики проблемы")
                        except Exception as e:
                            st.error(f"❌ Ошибка генерации тестовых вопросов: {e}")
                            import traceback
                            st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
                else:
                    st.info("✅ Тестовые вопросы сгенерированы и будут использованы после создания БЗ")
                    if st.button("🔄 Перегенерировать вопросы", key="regenerate_test_questions"):
                        st.session_state.generated_test_questions = None
                        st.rerun()
                    
                    # Показываем изображения и их анализ с чекбоксами
                    if 'images' in analysis and analysis['images']:
                        st.write("**🖼️ Изображения в документе:**")
                        
                        for img_idx, image_info in enumerate(analysis['images']):
                            if not isinstance(image_info, dict):
                                st.warning(f"⚠️ Пропущено некорректное изображение под индексом {img_idx}")
                                continue
                            # Чекбокс для выбора изображения
                            image_name = image_info.get('image_name', f'image_{img_idx}')
                            img_selected = st.checkbox(
                                f"✅ Выбрать изображение: {image_name}", 
                                key=f"select_img_{i}_{img_idx}"
                            )
                            
                            # Всегда показываем expander, но с разным содержимым в зависимости от выбора
                            expander_title = f"📷 {image_name} - {'ВЫБРАНО' if img_selected else 'не выбрано'}"
                            
                            with st.expander(expander_title, expanded=img_selected):
                                if img_selected:
                                    col1, col2 = st.columns([1, 2])
                                    
                                    with col1:
                                        # Показываем изображение
                                        try:
                                            from PIL import Image
                                            image_path = Path(image_info.get('image_path', ''))
                                            if image_path.exists():
                                                image = Image.open(image_path)
                                                st.image(image, caption=image_name, width='stretch')
                                            else:
                                                st.error(f"Изображение не найдено: {image_path}")
                                        except Exception as e:
                                            st.error(f"Ошибка загрузки изображения: {e}")
                                    
                                    with col2:
                                        # Показываем анализ изображения
                                        if image_info.get('error'):
                                            st.error(f"❌ Ошибка анализа: {image_info.get('error')}")
                                        else:
                                            if image_info.get('description'):
                                                st.write("**📝 Описание от Google Gemini:**")
                                                st.text_area("Описание Gemini", value=image_info.get('description', ''), height=150, disabled=True, key=f"gemini_desc_{i}_{img_idx}")
                                            
                                            if image_info.get('text_content'):
                                                st.write("**📄 Извлеченный текст:**")
                                                st.text_area("Извлеченный текст", value=image_info.get('text_content', ''), height=150, disabled=True, key=f"extracted_text_{i}_{img_idx}")
                                else:
                                    st.info("Изображение не выбрано для сохранения в KB")
            
        # Показываем рекомендации по созданию БЗ
        strategy = results.get('strategy', {}) if isinstance(results, dict) else {}
        if strategy:
            st.subheader("🎯 Рекомендации по созданию БЗ")
            
            if 'strategy_type' in strategy:
                st.write(f"**Рекомендуемая стратегия:** {strategy['strategy_type']}")
            
            if 'recommended_kbs' in strategy:
                for kb_rec in strategy['recommended_kbs']:
                    with st.expander(f"📚 {kb_rec.get('name', 'База знаний')}"):
                        st.write(f"**Описание:** {kb_rec.get('description', 'Нет описания')}")
                        st.write(f"**Документов:** {kb_rec.get('document_count', 0)}")
                        st.write(f"**Категория:** {kb_rec.get('category', 'Не определена')}")
                        
                        # Кнопка для создания БЗ
                        if st.button(f"✅ Создать БЗ: {kb_rec.get('name', 'База знаний')}", 
                                   key=f"create_kb_recommended_{kb_rec.get('name', 'unknown')}"):
                            # Создаем стратегию из рекомендации
                            strategy = {
                                'type': 'single_kb',
                                'kb_name': kb_rec.get('name', 'База знаний'),
                                'description': kb_rec.get('description', 'База знаний для документов'),
                                'category': kb_rec.get('category', 'Общие документы')
                            }
                            self._create_kb_from_strategy(strategy)
        
        # Обработка индивидуальных диалогов сохранения
        analyses = results.get('analyses', []) if isinstance(results, dict) else []
        for i, analysis in enumerate(analyses):
            dialog_key = f"show_save_dialog_{analysis['file_name']}"
            if st.session_state.get(dialog_key, False):
                st.subheader(f"💾 Сохранение документа: {analysis['file_name']}")
                
                # Выбор KB для сохранения
                from modules.core.knowledge_manager import KnowledgeBaseManager
                from datetime import datetime
                kb_manager = KnowledgeBaseManager()
                existing_kbs = kb_manager.get_knowledge_bases(active_only=True)
                
                if existing_kbs:
                    kb_options = ["Создать новую KB"] + [f"ID {kb['id']}: {kb['name']}" for kb in existing_kbs]
                    selected_kb = st.selectbox("База знаний:", kb_options, key=f"kb_selection_{i}")
                    
                    if selected_kb == "Создать новую KB":
                        # Создание новой KB
                        kb_name = st.text_input("Название KB:", value=analysis.get('suggested_kb', {}).get('suggested_name', 'Новая база знаний'), key=f"new_kb_name_{i}")
                        kb_category = st.text_input("Категория:", value=analysis.get('suggested_kb', {}).get('suggested_category', 'Общие документы'), key=f"new_kb_category_{i}")
                        kb_description = st.text_area("Описание:", value=analysis.get('suggested_kb', {}).get('description', 'База знаний для документов'), key=f"new_kb_description_{i}")
                        
                        if st.button("✅ Создать KB и сохранить документ", key=f"create_and_save_{i}"):
                            try:
                                # Создаем новую KB
                                kb_id = kb_manager.create_knowledge_base(
                                    name=kb_name,
                                    description=kb_description,
                                    category=kb_category,
                                    created_by="KB Admin"
                                )
                                
                                # Получаем полный текст для сохранения
                                full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                                if not full_text or (full_text.strip() == analysis.get('smart_summary', '').strip()):
                                    full_text = analysis.get('raw_ocr_text', '')
                                
                                # Сохраняем документ
                                doc_id = kb_manager.add_document(
                                    kb_id=kb_id,
                                    title=analysis.get('file_name', 'Документ'),
                                    file_path=str(analysis.get('file_path', '')),
                                    content_type=analysis.get('content_type', 'text/plain'),
                                    file_size=analysis.get('file_size', 0),
                                    metadata={
                                        'ocr_cleaned': True,
                                        'gemini_analyzed': bool(analysis.get('images')),
                                        'text_length': len(full_text),
                                        'summary_length': len(analysis.get('smart_summary', '')),
                                        'content': full_text,
                                        'summary': analysis.get('smart_summary', ''),
                                        'processed': True,
                                        'status': "processed"
                                    }
                                )
                                
                                # Сохраняем изображения и анализ Gemini
                                if analysis.get('images'):
                                    for image_info in analysis['images']:
                                        kb_manager.add_image(
                                            kb_id=kb_id,
                                            image_path=image_info.get('image_path', ''),
                                            image_name=image_info.get('image_name', ''),
                                            image_description=image_info.get('description', ''),
                                            llava_analysis=image_info.get('description', ''),
                                        )
                                
                                # Автоматически экспортируем KB в JSON
                                try:
                                    json_file_path = kb_manager.export_kb_to_json(kb_id, "docs/kb")
                                    st.info(f"📄 KB экспортирована в JSON: {json_file_path}")
                                except Exception as e:
                                    st.warning(f"⚠️ Не удалось экспортировать KB в JSON: {e}")
                                
                                st.success(f"✅ Успешно создана KB '{kb_name}' и сохранен документ!")
                                st.session_state[dialog_key] = False
                                st.session_state["last_saved_selection"] = f"{[i]}_{[]}"
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Ошибка при создании KB: {e}")
                    else:
                        # Сохранение в существующую KB
                        kb_id = int(selected_kb.split(':')[0].split()[1])
                        kb_name = selected_kb.split(':')[1].strip()
                        
                        st.write(f"**Сохранение в KB:** {kb_name}")
                        
                        if st.button("✅ Сохранить документ в выбранную KB", key=f"save_to_existing_{i}"):
                            try:
                                # Получаем полный текст для сохранения
                                full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                                if not full_text or (full_text.strip() == analysis.get('smart_summary', '').strip()):
                                    full_text = analysis.get('raw_ocr_text', '')
                                
                                # Сохраняем документ
                                doc_id = kb_manager.add_document(
                                    kb_id=kb_id,
                                    title=analysis.get('file_name', 'Документ'),
                                    file_path=str(analysis.get('file_path', '')),
                                    content_type=analysis.get('content_type', 'text/plain'),
                                    file_size=analysis.get('file_size', 0),
                                    metadata={
                                        'ocr_cleaned': True,
                                        'gemini_analyzed': bool(analysis.get('images')),
                                        'text_length': len(full_text),
                                        'summary_length': len(analysis.get('smart_summary', '')),
                                        'content': full_text,
                                        'summary': analysis.get('smart_summary', ''),
                                        'processed': True,
                                        'status': "processed"
                                    }
                                )
                                
                                # Сохраняем изображения и анализ Gemini
                                if analysis.get('images'):
                                    for image_info in analysis['images']:
                                        kb_manager.add_image(
                                            kb_id=kb_id,
                                            image_path=image_info.get('image_path', ''),
                                            image_name=image_info.get('image_name', ''),
                                            image_description=image_info.get('description', ''),
                                            llava_analysis=image_info.get('description', ''),
                                        )
                                
                                st.success(f"✅ Успешно сохранен документ в KB '{kb_name}'!")
                                st.session_state[dialog_key] = False
                                st.session_state["last_saved_selection"] = f"{[i]}_{[]}"
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Ошибка при сохранении в KB: {e}")
                else:
                    st.write("**Создание новой базы знаний:**")
                    kb_name = st.text_input("Название KB:", value=analysis.get('suggested_kb', {}).get('suggested_name', 'Новая база знаний'), key=f"new_kb_name_no_existing_{i}")
                    kb_category = st.text_input("Категория:", value=analysis.get('suggested_kb', {}).get('suggested_category', 'Общие документы'), key=f"new_kb_category_no_existing_{i}")
                    kb_description = st.text_area("Описание:", value=analysis.get('suggested_kb', {}).get('description', 'База знаний для документов'), key=f"new_kb_description_no_existing_{i}")
                    
                    if st.button("✅ Создать KB и сохранить документ", key=f"create_and_save_no_existing_{i}"):
                        # Аналогичная логика создания KB
                        pass
                
                if st.button("❌ Отмена", key=f"cancel_save_{i}"):
                    st.session_state[dialog_key] = False
                    st.rerun()
                break  # Показываем только один диалог за раз


        # Диалог сохранения выбранных документов в KB
        if st.session_state.get("show_save_dialog", False):
            st.subheader("💾 Сохранение выбранных документов в KB")
            
            analyses = results.get('analyses', [])
            selected_analyses = [analyses[i] for i in range(len(analyses)) if st.session_state.get(f"selected_doc_{i}", False)]
            
            st.write(f"**Выбрано документов:** {len(selected_analyses)}")
            
            # Показываем список выбранных документов
            for i, analysis in enumerate(selected_analyses):
                st.write(f"• {analysis.get('file_name', 'Неизвестный файл')} ({analysis.get('category', 'Не определена')})")
            
            # Выбор KB для сохранения
            from modules.core.knowledge_manager import KnowledgeBaseManager
            from datetime import datetime
            kb_manager = KnowledgeBaseManager()
            existing_kbs = kb_manager.get_knowledge_bases(active_only=True)
            
            if existing_kbs:
                st.write("**Выберите существующую KB или создайте новую:**")
                
                kb_options = ["Создать новую KB"] + [f"ID {kb['id']}: {kb['name']}" for kb in existing_kbs]
                selected_kb = st.selectbox("База знаний:", kb_options, key="kb_selection")
                
                if selected_kb == "Создать новую KB":
                    # Создание новой KB
                    st.write("**Создание новой базы знаний:**")
                    
                    # Используем предложение от AI если есть
                    if selected_analyses and 'suggested_kb' in selected_analyses[0]:
                        suggestion = selected_analyses[0]['suggested_kb']
                        default_name = suggestion.get('suggested_name', 'Новая база знаний')
                        default_category = suggestion.get('suggested_category', 'Общие документы')
                        default_description = suggestion.get('description', 'База знаний для документов')
                    else:
                        default_name = "Новая база знаний"
                        default_category = "Общие документы"
                        default_description = "База знаний для документов"
                    
                    kb_name = st.text_input("Название KB:", value=default_name, key="new_kb_name")
                    kb_category = st.text_input("Категория:", value=default_category, key="new_kb_category")
                    kb_description = st.text_area("Описание:", value=default_description, key="new_kb_description")
                    
                    # Умная проверка на дубликаты
                    if kb_name and kb_category:
                        kb_check = self._smart_kb_check(kb_name, kb_category, selected_analyses)
                        
                        if kb_check['has_conflicts']:
                            st.warning("⚠️ **Обнаружены потенциальные дубликаты!**")
                            
                            if kb_check['exact_matches']:
                                st.error(f"❌ **Точное совпадение:** KB с названием '{kb_name}' уже существует!")
                                for match in kb_check['exact_matches']:
                                    st.write(f"• **{match['name']}** (ID: {match['id']}, Категория: {match['category']})")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("🔄 Использовать существующую KB", key="use_existing_exact"):
                                        st.session_state["pending_kb_params"] = {
                                            "action": "use_existing",
                                            "kb_id": kb_check['exact_matches'][0]['id'],
                                            "name": kb_check['exact_matches'][0]['name']
                                        }
                                        st.rerun()
                                
                                with col2:
                                    if st.button("➕ Создать новую с другим именем", key="create_different_name"):
                                        # Предлагаем пользователю ввести новое имя
                                        st.session_state["show_rename_dialog"] = True
                                        st.session_state["original_kb_name"] = kb_name
                                        st.session_state["original_kb_category"] = kb_category
                                        st.session_state["original_kb_description"] = kb_description
                                        st.rerun()
                            
                            elif kb_check['similar_matches']:
                                st.warning(f"⚠️ **Похожие названия найдены:**")
                                for match in kb_check['similar_matches']:
                                    st.write(f"• **{match['name']}** (ID: {match['id']}, Категория: {match['category']})")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("🔄 Использовать похожую KB", key="use_similar"):
                                        st.session_state["pending_kb_params"] = {
                                            "action": "use_existing",
                                            "kb_id": kb_check['similar_matches'][0]['id'],
                                            "name": kb_check['similar_matches'][0]['name']
                                        }
                                        st.rerun()
                                
                                with col2:
                                    if st.button("➕ Создать новую", key="create_new_anyway"):
                                        st.session_state["pending_kb_params"] = {
                                            "action": "create_new",
                                            "name": kb_name,
                                            "category": kb_category,
                                            "description": kb_description
                                        }
                                        st.rerun()
                            
                            if kb_check['category_matches']:
                                st.info(f"💡 **KB в той же категории:** {len(kb_check['category_matches'])} найдено")
                                for match in kb_check['category_matches'][:3]:  # Показываем только первые 3
                                    st.write(f"• **{match['name']}** (ID: {match['id']})")
                                
                                if st.button("🔄 Показать все KB в категории", key="show_category_kbs"):
                                    st.session_state["show_category_kbs"] = True
                                    st.rerun()
                        else:
                            st.success("✅ **Название уникально!** Можно создавать новую KB.")
                    
                    # Показываем все KB в категории если запрошено
                    if st.session_state.get("show_category_kbs", False):
                        st.subheader(f"📚 Все KB в категории '{kb_category}':")
                        for match in kb_check['category_matches']:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            with col1:
                                st.write(f"**{match['name']}** (ID: {match['id']})")
                                st.caption(match.get('description', 'Без описания'))
                            with col2:
                                docs = kb_manager.get_documents(match['id'])
                                st.write(f"📄 {len(docs)} документов")
                            with col3:
                                if st.button("🔄 Использовать", key=f"use_category_kb_{match['id']}"):
                                    st.session_state["pending_kb_params"] = {
                                        "action": "use_existing",
                                        "kb_id": match['id'],
                                        "name": match['name']
                                    }
                                    st.session_state["show_category_kbs"] = False
                                    st.rerun()
                        
                        if st.button("❌ Скрыть", key="hide_category_kbs"):
                            st.session_state["show_category_kbs"] = False
                            st.rerun()
                    
                    # Диалог для ввода нового имени KB
                    if st.session_state.get("show_rename_dialog", False):
                        st.subheader("✏️ Введите новое название KB:")
                        new_kb_name = st.text_input(
                            "Новое название KB:", 
                            value=st.session_state.get("original_kb_name", ""),
                            key="new_kb_name_input"
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Создать с новым именем", key="confirm_new_name"):
                                st.session_state["pending_kb_params"] = {
                                    "action": "create_new",
                                    "name": new_kb_name,
                                    "category": st.session_state.get("original_kb_category", ""),
                                    "description": st.session_state.get("original_kb_description", "")
                                }
                                st.session_state["show_rename_dialog"] = False
                                st.rerun()
                        
                        with col2:
                            if st.button("❌ Отмена", key="cancel_rename"):
                                st.session_state["show_rename_dialog"] = False
                                st.rerun()
                    
                    # Сохраняем параметры KB в session_state для использования в кнопке внизу
                    st.session_state["pending_kb_params"] = {
                        "action": "create_new",
                        "name": kb_name,
                        "category": kb_category,
                        "description": kb_description
                    }
                    
                    if st.button("💾 Создать KB и сохранить документы", key="create_and_save_final", type="primary"):
                        # Получаем индексы выбранных документов
                        selected_doc_indices = [i for i in range(len(analyses)) if st.session_state.get(f"selected_doc_{i}", False)]
                        selected_image_indices = []
                        for i in range(len(analyses)):
                            if 'images' in analyses[i]:
                                for img_idx in range(len(analyses[i]['images'])):
                                    if st.session_state.get(f"select_img_{i}_{img_idx}", False):
                                        selected_image_indices.append((i, img_idx))
                        
                        # Используем транзакционный метод сохранения
                        self._execute_save_to_kb_transactional(analyses, selected_doc_indices, selected_image_indices)
                    
                    if False:  # Отключаем кнопку в диалоге
                        try:
                            # Создаем новую KB
                            kb_id = kb_manager.create_knowledge_base(
                                name=kb_name,
                                description=kb_description,
                                category=kb_category,
                                created_by="KB Admin"
                            )
                            
                            # Сохраняем документы
                            saved_count = 0
                            for analysis in selected_analyses:
                                # Получаем полный текст для сохранения
                                full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                                if not full_text or (full_text.strip() == analysis.get('smart_summary', '').strip()):
                                    full_text = analysis.get('raw_ocr_text', '')
                                
                                # Добавляем документ в KB с полным содержимым
                                doc_id = kb_manager.add_document(
                                    kb_id=kb_id,
                                    title=analysis.get('file_name', 'Документ'),
                                    file_path=str(analysis.get('file_path', '')),
                                    content_type=analysis.get('content_type', 'text/plain'),
                                    file_size=analysis.get('file_size', 0),
                                    upload_date=datetime.now().isoformat(),
                                    processed=True,
                                    status="processed",
                                    content=full_text,  # Сохраняем полный текст
                                    summary=analysis.get('smart_summary', ''),  # Сохраняем абстракт
                                    metadata={
                                        'ocr_cleaned': True,
                                        'gemini_analyzed': bool(analysis.get('images')),
                                        'text_length': len(full_text),
                                        'summary_length': len(analysis.get('smart_summary', '')),
                                        'content': full_text,
                                        'summary': analysis.get('smart_summary', ''),
                                        'processed': True,
                                        'status': "processed"
                                    }
                                )
                                
                                # Сохраняем изображения и анализ Gemini
                                if analysis.get('images'):
                                    for image_info in analysis['images']:
                                        kb_manager.add_image(
                                            kb_id=kb_id,
                                            image_path=image_info.get('image_path', ''),
                                            image_name=image_info.get('image_name', ''),
                                            image_description=image_info.get('description', ''),
                                            llava_analysis=image_info.get('description', ''),
                                        )
                                
                                saved_count += 1
                            
                            # Автоматически экспортируем KB в JSON
                            try:
                                json_file_path = kb_manager.export_kb_to_json(kb_id, "docs/kb")
                                st.info(f"📄 KB экспортирована в JSON: {json_file_path}")
                            except Exception as e:
                                st.warning(f"⚠️ Не удалось экспортировать KB в JSON: {e}")
                            
                            st.success(f"✅ Успешно создана KB '{kb_name}' и сохранено {saved_count} документов!")
                            
                            # Предлагаем архивировать сохраненные документы
                            st.info("💡 Документы успешно сохранены в KB. Хотите архивировать их, чтобы убрать из списка новых документов?")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📦 Архивировать сохраненные документы", key="archive_saved_docs_new_kb", type="primary"):
                                    archived_count = 0
                                    for doc_idx in selected_docs:
                                        analysis = analyses[doc_idx]
                                        file_path = Path(analysis.get('file_path', ''))
                                        if file_path.exists():
                                            success, result = self.smart_librarian.document_manager.archive_document(file_path, "saved_to_kb")
                                            if success:
                                                archived_count += 1
                                            else:
                                                st.error(f"❌ Ошибка архивирования {file_path.name}: {result}")
                                    
                                    if archived_count > 0:
                                        st.success(f"📦 Архивировано {archived_count} документов")
                                        # Обновляем результаты анализа, убирая заархивированные документы
                                        new_analyses = [analyses[i] for i in range(len(analyses)) if i not in selected_docs]
                                        st.session_state.analysis_results['analyses'] = new_analyses
                            
                            with col2:
                                if st.button("❌ Не архивировать", key="dont_archive_new_kb"):
                                    pass
                            
                            # Сбрасываем состояние и обновляем последнее сохраненное состояние
                            st.session_state["show_save_dialog"] = False
                            st.session_state["last_saved_selection"] = f"{selected_docs}_{selected_images}"
                            for i in range(len(analyses)):
                                st.session_state[f"selected_doc_{i}"] = False
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Ошибка при создании KB: {e}")
                else:
                    # Сохранение в существующую KB
                    kb_id = int(selected_kb.split(':')[0].split()[1])
                    kb_name = selected_kb.split(':')[1].strip()
                    
                    st.write(f"**Сохранение в KB:** {kb_name}")
                    
                    # Сохраняем параметры KB в session_state для использования в кнопке внизу
                    st.session_state["pending_kb_params"] = {
                        "action": "use_existing",
                        "kb_id": kb_id,
                        "name": kb_name
                    }
                    
                    if st.button("💾 Сохранить документы в выбранную KB", key="save_to_existing_final", type="primary"):
                        # Получаем индексы выбранных документов
                        selected_doc_indices = [i for i in range(len(analyses)) if st.session_state.get(f"selected_doc_{i}", False)]
                        selected_image_indices = []
                        for i in range(len(analyses)):
                            if 'images' in analyses[i]:
                                for img_idx in range(len(analyses[i]['images'])):
                                    if st.session_state.get(f"select_img_{i}_{img_idx}", False):
                                        selected_image_indices.append((i, img_idx))
                        
                        # Используем транзакционный метод сохранения
                        self._execute_save_to_kb_transactional(analyses, selected_doc_indices, selected_image_indices)
                    
                    if False:  # Отключаем кнопку в диалоге
                        try:
                            saved_count = 0
                            for analysis in selected_analyses:
                                # Получаем полный текст для сохранения
                                full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                                if not full_text or (full_text.strip() == analysis.get('smart_summary', '').strip()):
                                    full_text = analysis.get('raw_ocr_text', '')
                                
                                # Добавляем документ в существующую KB с полным содержимым
                                doc_id = kb_manager.add_document(
                                    kb_id=kb_id,
                                    title=analysis.get('file_name', 'Документ'),
                                    file_path=str(analysis.get('file_path', '')),
                                    content_type=analysis.get('content_type', 'text/plain'),
                                    file_size=analysis.get('file_size', 0),
                                    upload_date=datetime.now().isoformat(),
                                    processed=True,
                                    status="processed",
                                    content=full_text,  # Сохраняем полный текст
                                    summary=analysis.get('smart_summary', ''),  # Сохраняем абстракт
                                    metadata={
                                        'ocr_cleaned': True,
                                        'gemini_analyzed': bool(analysis.get('images')),
                                        'text_length': len(full_text),
                                        'summary_length': len(analysis.get('smart_summary', '')),
                                        'content': full_text,
                                        'summary': analysis.get('smart_summary', ''),
                                        'processed': True,
                                        'status': "processed"
                                    }
                                )
                                
                                # Сохраняем изображения и анализ Gemini
                                if analysis.get('images'):
                                    for image_info in analysis['images']:
                                        kb_manager.add_image(
                                            kb_id=kb_id,
                                            image_path=image_info.get('image_path', ''),
                                            image_name=image_info.get('image_name', ''),
                                            image_description=image_info.get('description', ''),
                                            llava_analysis=image_info.get('description', ''),
                                        )
                                
                                saved_count += 1
                            
                            st.success(f"✅ Успешно сохранено {saved_count} документов в KB '{kb_name}'!")
                            
                            # Предлагаем архивировать сохраненные документы
                            st.info("💡 Документы успешно сохранены в KB. Хотите архивировать их, чтобы убрать из списка новых документов?")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("📦 Архивировать сохраненные документы", key="archive_saved_docs_existing_kb", type="primary"):
                                    archived_count = 0
                                    for doc_idx in selected_docs:
                                        analysis = analyses[doc_idx]
                                        file_path = Path(analysis.get('file_path', ''))
                                        if file_path.exists():
                                            success, result = self.smart_librarian.document_manager.archive_document(file_path, "saved_to_kb")
                                            if success:
                                                archived_count += 1
                                            else:
                                                st.error(f"❌ Ошибка архивирования {file_path.name}: {result}")
                                    
                                    if archived_count > 0:
                                        st.success(f"📦 Архивировано {archived_count} документов")
                                        # Обновляем результаты анализа, убирая заархивированные документы
                                        new_analyses = [analyses[i] for i in range(len(analyses)) if i not in selected_docs]
                                        st.session_state.analysis_results['analyses'] = new_analyses
                            
                            with col2:
                                if st.button("❌ Не архивировать", key="dont_archive_existing_kb"):
                                    pass
                            
                            # Сбрасываем состояние и обновляем последнее сохраненное состояние
                            st.session_state["show_save_dialog"] = False
                            st.session_state["last_saved_selection"] = f"{selected_docs}_{selected_images}"
                            for i in range(len(analyses)):
                                st.session_state[f"selected_doc_{i}"] = False
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Ошибка при сохранении в KB: {e}")
            else:
                st.write("**Создание новой базы знаний:**")
                kb_name = st.text_input("Название KB:", key="new_kb_name_no_existing")
                kb_category = st.text_input("Категория:", key="new_kb_category_no_existing")
                kb_description = st.text_area("Описание:", key="new_kb_description_no_existing")
                
                if st.button("✅ Создать KB и сохранить документы", key="create_and_save_no_existing"):
                    # Аналогичная логика создания KB
                    pass
            
            if st.button("❌ Отмена", key="cancel_save"):
                st.session_state["show_save_dialog"] = False
                st.rerun()
        
        # Стабильная секция сохранения в KB (скрыта когда диалог открыт)
        if not st.session_state.get("show_save_dialog", False):
            st.subheader("💾 Сохранение в базу знаний")
        
        if results and 'analyses' in results and not st.session_state.get("show_save_dialog", False):
            analyses = results.get('analyses', [])
            selected_docs = [i for i in range(len(analyses)) if st.session_state.get(f"selected_doc_{i}", False)]
            selected_images = []
            for i in range(len(analyses)):
                if 'images' in analyses[i]:
                    for img_idx in range(len(analyses[i]['images'])):
                        if st.session_state.get(f"select_img_{i}_{img_idx}", False):
                            selected_images.append((i, img_idx))
            
            total_selected = len(selected_docs) + len(selected_images)
            
            # Всегда показываем статистику
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Выбрано документов", len(selected_docs))
            with col2:
                st.metric("🖼️ Выбрано изображений", len(selected_images))
            with col3:
                st.metric("📦 Всего выбрано", total_selected)
            
            # Умная кнопка сохранения - активна только при выборе и изменениях
            if total_selected > 0:
                # Проверяем, были ли изменения в выборе
                current_selection = f"{selected_docs}_{selected_images}"
                last_saved_selection = st.session_state.get("last_saved_selection", "")
                
                if current_selection != last_saved_selection:
                    # Есть изменения - показываем активную кнопку
                    if st.button("💾 Сохранить выбранное в KB", key="save_selected_to_kb_main", type="primary"):
                        # Открываем диалог
                        st.session_state["show_save_dialog"] = True
                        st.rerun()
                    st.info("ℹ️ Есть несохраненные изменения в выборе документов")
                else:
                    # Нет изменений - показываем неактивную кнопку
                    st.button("💾 Сохранить выбранное в KB", key="save_selected_to_kb_main", disabled=True)
                    st.success("✅ Все выбранные документы уже сохранены")
            else:
                st.button("💾 Сохранить выбранное в KB", key="save_selected_to_kb_main", disabled=True)
                st.info("ℹ️ Выберите документы или изображения для сохранения в KB")
        else:
            # Показываем пустую статистику когда нет результатов
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Выбрано документов", 0)
            with col2:
                st.metric("🖼️ Выбрано изображений", 0)
            with col3:
                st.metric("📦 Всего выбрано", 0)
            
            st.button("💾 Сохранить выбранное в KB", key="save_selected_to_kb_empty", disabled=True)
            st.info("ℹ️ Загрузите и проанализируйте документы для сохранения в KB")

        # Показываем сообщение о успешном создании БЗ если есть
        if st.session_state.get('kb_created_successfully', False):
            st.success(f"🎉 База знаний '{st.session_state.get('created_kb_name', '')}' успешно создана!")
            st.session_state['kb_created_successfully'] = False
        
        # Кнопка для сброса анализа
        if st.button("🔄 Анализировать новые документы", key="reset_analysis_btn"):
            # Очищаем все состояния анализа
            st.session_state.analysis_in_progress = False
            st.session_state.analysis_results = None
            st.session_state.selected_files = []
            st.session_state.doc_status = None
            # Очищаем все состояния анализа документов
            keys_to_clear = [key for key in st.session_state.keys() if key.startswith(('show_full_text_', 'saved_text_', 'edit_text_', 'analyze_new_'))]
            for key in keys_to_clear:
                del st.session_state[key]
            st.rerun()
    
    def _render_smart_kb_creation(self):
        """Умное создание БЗ"""
        st.subheader("📚 Умное создание базы знаний")
        
        # Используем функционал из PDFUploadInterface
        self.pdf_upload_interface.render_simple_kb_creation()
    
    def _render_smart_kb_expansion(self):
        """Умное расширение БЗ"""
        st.subheader("📈 Умное расширение базы знаний")
        
        # Получаем список существующих БЗ
        kbs = self.kb_manager.get_knowledge_bases()
        
        if not kbs:
            st.warning("Нет созданных баз знаний. Сначала создайте БЗ")
            return
        
        # Выбор БЗ для расширения
        kb_options = {f"{kb['name']} ({kb['category']})": kb['id'] for kb in kbs}
        selected_kb_name = st.selectbox("Выберите базу знаний для расширения:", list(kb_options.keys()))
        selected_kb_id = kb_options[selected_kb_name]
        
        # Показываем информацию о БЗ
        selected_kb = next(kb for kb in kbs if kb['id'] == selected_kb_id)
        st.info(f"**База знаний:** {selected_kb['name']} | **Категория:** {selected_kb['category']}")
        
        # Получаем список файлов
        upload_dir = self.smart_librarian.document_manager.upload_dir
        pdf_files = list(upload_dir.glob("*.pdf"))
        
        if not pdf_files:
            st.warning("Нет PDF файлов для добавления")
            return
        
        # Выбор файлов
        st.write("**Выберите файлы для добавления в БЗ:**")
        selected_files = []
        already_processed_files = []
        
        for pdf_file in pdf_files:
            # Проверяем, не обработан ли уже файл
            docs = self.kb_manager.get_documents(selected_kb_id)
            already_processed = any(doc['title'] == pdf_file.name for doc in docs)
            
            if already_processed:
                st.write(f"✅ {pdf_file.name} (уже обработан)")
                already_processed_files.append(pdf_file)
            else:
                if st.checkbox(f"📄 {pdf_file.name}", key=f"expand_{pdf_file.name}"):
                    selected_files.append(pdf_file)
        
        # Показываем кнопки для разных типов файлов
        col1, col2 = st.columns(2)
        
        with col1:
            if selected_files:
                if st.button("🚀 Добавить выбранные файлы в БЗ", type="primary"):
                    self._process_uploaded_files(selected_files, selected_kb_id)
            else:
                st.button("🚀 Добавить выбранные файлы в БЗ", disabled=True)
        
        with col2:
            if already_processed_files:
                if st.button("🔄 Добавить уже обработанные файлы", type="secondary"):
                    self._add_processed_files_to_kb(already_processed_files, selected_kb_id)
            else:
                st.button("🔄 Добавить уже обработанные файлы", disabled=True)
        
        # Показываем информацию о файлах
        if selected_files:
            st.info(f"📄 Выбрано новых файлов: {len(selected_files)}")
        if already_processed_files:
            st.info(f"✅ Уже обработанных файлов: {len(already_processed_files)}")
    
    def _add_processed_files_to_kb(self, processed_files, kb_id):
        """Добавляет уже обработанные файлы в KB"""
        try:
            added_count = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, pdf_file in enumerate(processed_files):
                status_text.text(f"Добавление: {pdf_file.name}")
                
                try:
                    # Проверяем, есть ли уже этот файл в KB
                    docs = self.kb_manager.get_documents(kb_id)
                    already_exists = any(doc['title'] == pdf_file.name for doc in docs)
                    
                    if already_exists:
                        st.warning(f"⚠️ {pdf_file.name} уже есть в этой KB")
                        continue
                    
                    # Ищем анализ этого файла в session_state
                    analysis_data = None
                    if 'analysis_results' in st.session_state and st.session_state.analysis_results:
                        analyses = st.session_state.analysis_results.get('analyses', [])
                        for analysis in analyses:
                            if analysis.get('file_name') == pdf_file.name:
                                analysis_data = analysis
                                break
                    
                    if analysis_data:
                        # Используем данные из анализа
                        full_text = analysis_data.get('original_cleaned_text', analysis_data.get('full_cleaned_text', ''))
                        if not full_text or (full_text.strip() == analysis_data.get('smart_summary', '').strip()):
                            full_text = analysis_data.get('raw_ocr_text', '')
                        
                        # Добавляем документ в KB
                        doc_id = self.kb_manager.add_document(
                            kb_id=kb_id,
                            title=analysis_data.get('file_name', pdf_file.name),
                            file_path=str(pdf_file),
                            content_type='application/pdf',
                            file_size=pdf_file.stat().st_size,
                            metadata={
                                'ocr_cleaned': True,
                                'gemini_analyzed': bool(analysis_data.get('images')),
                                'text_length': len(full_text),
                                'summary_length': len(analysis_data.get('smart_summary', '')),
                                'content': full_text,
                                'summary': analysis_data.get('smart_summary', ''),
                                'processed': True,
                                'status': "processed"
                            }
                        )
                        
                        # Добавляем изображения если есть
                        if analysis_data.get('images'):
                            for image_info in analysis_data['images']:
                                self.kb_manager.add_image(
                                    kb_id=kb_id,
                                    image_path=image_info.get('image_path', ''),
                                    image_name=image_info.get('image_name', ''),
                                    image_description=image_info.get('description', ''),
                                    llava_analysis=image_info.get('description', ''),
                                )
                        
                        added_count += 1
                        st.success(f"✅ Добавлен: {pdf_file.name}")
                        
                    else:
                        # Если нет данных анализа, добавляем как простой документ
                        doc_id = self.kb_manager.add_document(
                            kb_id=kb_id,
                            title=pdf_file.name,
                            file_path=str(pdf_file),
                            content_type='application/pdf',
                            file_size=pdf_file.stat().st_size,
                            metadata={
                                'processed': False,
                                'status': "pending"
                            }
                        )
                        added_count += 1
                        st.info(f"📄 Добавлен как простой документ: {pdf_file.name}")
                
                except Exception as e:
                    st.error(f"❌ Ошибка добавления {pdf_file.name}: {e}")
                
                progress_bar.progress((i + 1) / len(processed_files))
            
            status_text.text("")
            
            if added_count > 0:
                st.success(f"🎉 Успешно добавлено {added_count} из {len(processed_files)} файлов в KB!")
                st.rerun()
            else:
                st.warning("⚠️ Не удалось добавить ни одного файла")
                
        except Exception as e:
            st.error(f"❌ Ошибка при добавлении файлов: {e}")
    
    def _render_archive_management(self):
        """Управление архивом документов"""
        st.subheader("📦 Управление архивом документов")
        
        # Получаем информацию об архиве
        archive_info = self.smart_librarian.document_manager.get_archive_info()
        
        if archive_info['total_files'] == 0:
            st.info("Архив пуст")
            return
        
        # Показываем общую статистику
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📦 Всего файлов в архиве", archive_info['total_files'])
        with col2:
            st.metric("💾 Общий размер архива", f"{archive_info['total_size']/1024/1024:.1f} MB")
        
        # Показываем архивы по датам
        st.subheader("📅 Архивы по датам")
        
        for date_info in archive_info['dates']:
            with st.expander(f"📅 {date_info['date']} ({date_info['files_count']} файлов, {date_info['size']/1024:.1f} KB)"):
                # Получаем список файлов в этой дате
                date_dir = self.smart_librarian.document_manager.archive_dir / date_info['date']
                if date_dir.exists():
                    files = list(date_dir.glob("*"))
                    
                    for file_path in files:
                        if file_path.is_file():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.write(f"📄 {file_path.name}")
                            
                            with col2:
                                st.write(f"{file_path.stat().st_size/1024:.1f} KB")
                            
                            with col3:
                                if st.button("🔄 Восстановить", key=f"restore_{file_path.name}"):
                                    success = self.smart_librarian.document_manager.restore_from_archive(str(file_path))
                                    if success:
                                        st.success(f"✅ Документ {file_path.name} восстановлен")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Ошибка восстановления")
        
        # Массовые операции
        st.subheader("⚙️ Массовые операции")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Очистить весь архив", type="secondary"):
                if st.session_state.get('confirm_clear_archive', False):
                    # Удаляем все файлы из архива
                    archive_dir = self.smart_librarian.document_manager.archive_dir
                    if archive_dir.exists():
                        import shutil
                        shutil.rmtree(archive_dir)
                        archive_dir.mkdir(parents=True, exist_ok=True)
                    st.success("✅ Архив очищен")
                    st.rerun()
                else:
                    st.session_state['confirm_clear_archive'] = True
                    st.warning("⚠️ Нажмите еще раз для подтверждения очистки архива")
        
        with col2:
            if st.button("📊 Обновить статистику"):
                st.rerun()
    
    def _render_admin_panel(self):
        """Рендер админ-панели AI Billing"""
        st.header("🔧 Админ-панель AI Billing")
        st.info("Интегрированная админ-панель из AI Billing системы")
        
        # Рендерим админ-панель
        self.admin_panel.render_main_panel()
    
    def _render_create_new_kb(self):
        """Рендер создания новой БЗ"""
        st.header("🤖 Создание новой базы знаний")
        st.info("Создайте новую базу знаний из PDF документов")
        
        # Используем SimpleKBAssistant из админ-панели
        if hasattr(self.admin_panel, 'kb_assistant') and self.admin_panel.kb_assistant:
            self.admin_panel.kb_assistant.render_assistant()
        else:
            st.error("Ассистент создания БЗ недоступен")
    
    def _render_expand_existing_kb(self):
        """Рендер расширения существующей БЗ"""
        st.header("📈 Расширение существующей базы знаний")
        st.info("Добавьте новые документы в существующую базу знаний")
        
        # Получаем список существующих БЗ
        kbs = self.kb_manager.get_knowledge_bases()
        
        if not kbs:
            st.warning("Нет созданных баз знаний. Сначала создайте БЗ в разделе 'Создание новой БЗ'")
            return
        
        # Выбор БЗ для расширения
        kb_options = {f"{kb['name']} ({kb['category']})": kb['id'] for kb in kbs}
        selected_kb_name = st.selectbox("Выберите базу знаний для расширения:", list(kb_options.keys()))
        selected_kb_id = kb_options[selected_kb_name]
        
        # Показываем информацию о выбранной БЗ
        selected_kb = next(kb for kb in kbs if kb['id'] == selected_kb_id)
        st.subheader(f"📚 База знаний: {selected_kb['name']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Категория:** {selected_kb['category']}")
            st.write(f"**Описание:** {selected_kb['description']}")
        with col2:
            st.write(f"**Создана:** {selected_kb['created_at']}")
            st.write(f"**Автор:** {selected_kb['created_by']}")
        
        # Показываем текущие документы
        docs = self.kb_manager.get_documents(selected_kb_id)
        st.subheader(f"📄 Текущие документы ({len(docs)})")
        
        if docs:
            for doc in docs:
                status_icon = "✅" if doc['processed'] else "⏳"
                st.write(f"{status_icon} **{doc['title']}** - {doc['processing_status']}")
        else:
            st.info("В базе знаний пока нет документов")
        
        # Загрузка новых документов
        st.subheader("📤 Добавить новые документы")
        
        uploaded_files = st.file_uploader(
            "Выберите PDF файлы для добавления в БЗ",
            type=['pdf'],
            accept_multiple_files=True,
            help="Можно выбрать несколько PDF файлов одновременно"
        )
        
        if uploaded_files:
            st.success(f"Выбрано {len(uploaded_files)} файлов")
            
            # Показываем выбранные файлы
            with st.expander("📋 Выбранные файлы"):
                for file in uploaded_files:
                    file_size = len(file.getvalue()) / 1024
                    st.write(f"• **{file.name}** ({file_size:.1f} KB)")
            
            if st.button("🚀 Добавить документы в БЗ", type="primary"):
                self._process_uploaded_files(uploaded_files, selected_kb_id)
    
    def _process_uploaded_files(self, uploaded_files, kb_id):
        """Обработка загруженных файлов"""
        processed_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Обработка: {uploaded_file.name}")
                
                # Обрабатываем PDF
                result = self.admin_panel.pdf_processor.process_pdf(
                    uploaded_file, 
                    kb_id, 
                    uploaded_file.name
                )
                
                if result['success']:
                    # Добавляем документ в БЗ
                    doc_id = self.kb_manager.add_document(
                        kb_id,
                        result['title'],
                        result['file_path'],
                        result['content_type'],
                        result['file_size'],
                        result['metadata']
                    )
                    
                    # Обновляем статус обработки
                    self.kb_manager.update_document_status(doc_id, True, 'completed')
                    processed_count += 1
                    
                    st.success(f"✅ Обработан: {uploaded_file.name}")
                else:
                    st.error(f"❌ Ошибка: {uploaded_file.name} - {result.get('error', 'Неизвестная ошибка')}")
                
            except Exception as e:
                st.error(f"❌ Ошибка: {uploaded_file.name} - {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("")
        st.success(f"🎉 Обработка завершена! Успешно обработано {processed_count} из {len(uploaded_files)} файлов")
        
        # Обновляем страницу
        st.rerun()
    
    def _render_settings(self):
        """Рендер настроек"""
        render_settings_page()
    
    def _render_model_management(self):
        """Рендер страницы управления моделями"""
        st.header("🤖 Управление моделями агентов")
        st.markdown("---")
        
        # Глобальные настройки
        self.model_manager.render_global_model_settings()
        
        st.markdown("---")
        
        # Конфигурация агентов
        st.subheader("🔧 Конфигурация агентов")
        
        # Собираем всех агентов
        agents = {
            "Smart Librarian": self.smart_librarian,
            "RAG System": self.rag,
            "Text Analyzer": self.text_analyzer,
            "Chunk Optimizer": self.chunk_optimizer,
        }
        
        # Создаем вкладки для каждого агента
        agent_tabs = st.tabs([f"🤖 {name}" for name in agents.keys()])
        
        for i, (agent_name, agent_instance) in enumerate(agents.items()):
            with agent_tabs[i]:
                try:
                    self.model_manager.render_agent_model_config(
                        agent_name, 
                        agent_instance, 
                        key_prefix=f"agent_{i}"
                    )
                except Exception as e:
                    st.error(f"Ошибка конфигурации {agent_name}: {e}")
    
    def _create_kb_from_strategy(self, strategy: Dict):
        """Создание БЗ на основе стратегии"""
        try:
            st.write(f"🔍 DEBUG: Создаем БЗ с параметрами:")
            st.write(f"🔍 DEBUG: - Название: {strategy.get('kb_name', 'НЕ УКАЗАНО')}")
            st.write(f"🔍 DEBUG: - Описание: {strategy.get('description', 'НЕ УКАЗАНО')}")
            st.write(f"🔍 DEBUG: - Категория: {strategy.get('category', 'НЕ УКАЗАНО')}")
            
            # Создаем БЗ
            kb_id = self.kb_manager.create_knowledge_base(
                name=strategy.get('kb_name', 'База знаний'),
                description=strategy.get('description', 'База знаний для документов'),
                category=strategy.get('category', 'Общие документы'),
                created_by='admin'
            )
            
            st.success(f"✅ База знаний '{strategy['kb_name']}' создана с ID: {kb_id}")
            
            # Добавляем документы из анализа
            analyses = st.session_state.analysis_results.get('analyses', [])
            added_count = 0
            
            for analysis in analyses:
                if isinstance(analysis, dict):
                    # Проверяем, что сохраняется в БЗ
                    full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                    st.write(f"🔍 DEBUG: Полный текст для RAG: {len(full_text)} символов")
                    st.write(f"🔍 DEBUG: Первые 100 символов: {full_text[:100]}...")
                    st.write(f"🔍 DEBUG: Создаем очищенные метаданные без больших текстовых полей")
                    
                    # Создаем очищенные метаданные без больших текстовых полей
                    clean_metadata = {
                        'file_name': analysis.get('file_name', 'Неизвестный файл'),
                        'file_path': analysis.get('file_path', ''),
                        'content_type': analysis.get('content_type', 'application/octet-stream'),
                        'file_size': analysis.get('file_size', 0),
                        'category': analysis.get('category', 'Неизвестно'),
                        'format_description': analysis.get('format_description', ''),
                        'content_type_detected': analysis.get('content_type_detected', ''),
                        'confidence': analysis.get('confidence', 0),
                        'recommendations': analysis.get('recommendations', []),
                        'chunking_recommendations': analysis.get('chunking_recommendations', []),
                        'suggested_kb': analysis.get('suggested_kb', {}),
                        'images_count': len(analysis.get('images', [])),
                        'processing_timestamp': analysis.get('processing_timestamp', ''),
                        # Исключаем: original_cleaned_text, full_cleaned_text, smart_summary, raw_ocr_text
                        # Эти данные хранятся в RAG системе
                    }
                    
                    doc_id = self.kb_manager.add_document(
                        kb_id=kb_id,
                        title=analysis.get('file_name', 'Неизвестный файл'),
                        file_path=analysis.get('file_path', ''),
                        content_type=analysis.get('content_type', 'application/octet-stream'),
                        file_size=analysis.get('file_size', 0),
                        metadata=clean_metadata
                    )
                    if doc_id:
                        # Индексируем документ в RAG системе
                        try:
                            full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                            if full_text:
                                st.write(f"🔍 DEBUG: Индексируем документ в RAG системе...")
                                self.rag.add_document_to_kb(
                                    kb_id=kb_id,
                                    content=full_text,
                                    metadata={
                                        'title': analysis.get('file_name', 'Неизвестный файл'),
                                        'file_path': analysis.get('file_path', ''),
                                        'content_type': analysis.get('content_type', 'application/octet-stream'),
                                        'file_size': analysis.get('file_size', 0),
                                        'category': analysis.get('category', 'Неизвестно'),
                                        'doc_id': doc_id
                                    }
                                )
                                st.write(f"🔍 DEBUG: Документ проиндексирован в RAG системе")
                            else:
                                st.warning("⚠️ Нет текста для индексации в RAG")
                        except Exception as e:
                            st.error(f"❌ Ошибка индексации в RAG: {e}")
                            import traceback
                            st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
                        
                        added_count += 1
            
            st.success(f"✅ Добавлено {added_count} документов в БЗ")
            
            # Сохраняем тестовые вопросы в БЗ как метаданные
            test_questions = st.session_state.get('generated_test_questions')
            st.write(f"🔍 DEBUG: Проверяем наличие тестовых вопросов: {len(test_questions) if test_questions else 0}")
            
            if test_questions:
                st.write(f"🔍 DEBUG: Сохраняем тестовые вопросы в БЗ {kb_id}")
                try:
                    # Сохраняем тестовые вопросы в БЗ
                    self.smart_librarian._save_test_questions_to_kb(kb_id, test_questions)
                    st.success(f"✅ Тестовые вопросы сохранены в БЗ {kb_id}")
                    
                    # Показываем тестирование релевантности
                    st.write(f"🔍 DEBUG: Показываем тестирование релевантности для БЗ {kb_id}")
                    self._show_relevance_testing_after_creation(kb_id, test_questions)
                except Exception as e:
                    st.error(f"❌ Ошибка сохранения тестовых вопросов: {e}")
                    import traceback
                    st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
            else:
                st.info("ℹ️ Тестовые вопросы не сгенерированы. Нажмите '🧪 Тестовые вопросы' для их создания.")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Ошибка создания БЗ: {e}")
    
    def _process_documents_to_kb(self, documents: List[Dict], kb_id: int):
        """Обработка документов в БЗ"""
        try:
            # Получаем анализы из session_state, а не из параметра documents
            analyses = st.session_state.analysis_results.get('analyses', [])
            st.write(f"🔍 DEBUG: Найдено анализов для добавления: {len(analyses)}")
            added_count = 0
            
            for i, analysis in enumerate(analyses):
                if isinstance(analysis, dict):
                    st.write(f"🔍 DEBUG: Добавляем документ {i+1}: {analysis.get('file_name', 'Неизвестный файл')}")
                    
                    # Добавляем документ в БЗ
                    try:
                        # Проверяем, что сохраняется в БЗ
                        full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                        st.write(f"🔍 DEBUG: Полный текст для RAG: {len(full_text)} символов")
                        st.write(f"🔍 DEBUG: Первые 100 символов: {full_text[:100]}...")
                        st.write(f"🔍 DEBUG: Создаем очищенные метаданные без больших текстовых полей")
                        
                        # Создаем очищенные метаданные без больших текстовых полей
                        clean_metadata = {
                            'file_name': analysis.get('file_name', 'Неизвестный файл'),
                            'file_path': analysis.get('file_path', ''),
                            'content_type': analysis.get('content_type', 'application/octet-stream'),
                            'file_size': analysis.get('file_size', 0),
                            'category': analysis.get('category', 'Неизвестно'),
                            'format_description': analysis.get('format_description', ''),
                            'content_type_detected': analysis.get('content_type_detected', ''),
                            'confidence': analysis.get('confidence', 0),
                            'recommendations': analysis.get('recommendations', []),
                            'chunking_recommendations': analysis.get('chunking_recommendations', []),
                            'suggested_kb': analysis.get('suggested_kb', {}),
                            'images_count': len(analysis.get('images', [])),
                            'processing_timestamp': analysis.get('processing_timestamp', ''),
                            # Исключаем: original_cleaned_text, full_cleaned_text, smart_summary, raw_ocr_text
                            # Эти данные хранятся в RAG системе
                        }
                        
                        doc_id = self.kb_manager.add_document(
                            kb_id=kb_id,
                            title=analysis.get('file_name', 'Неизвестный файл'),
                            file_path=analysis.get('file_path', ''),
                            content_type=analysis.get('content_type', 'application/octet-stream'),
                            file_size=analysis.get('file_size', 0),
                            metadata=clean_metadata
                        )
                        st.write(f"🔍 DEBUG: Документ добавлен с ID: {doc_id}")
                        if doc_id:
                            # Индексируем документ в RAG системе
                            try:
                                full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                                if full_text:
                                    st.write(f"🔍 DEBUG: Индексируем документ в RAG системе...")
                                    self.rag.add_document_to_kb(
                                        kb_id=kb_id,
                                        content=full_text,
                                        metadata={
                                            'title': analysis.get('file_name', 'Неизвестный файл'),
                                            'file_path': analysis.get('file_path', ''),
                                            'content_type': analysis.get('content_type', 'application/octet-stream'),
                                            'file_size': analysis.get('file_size', 0),
                                            'category': analysis.get('category', 'Неизвестно'),
                                            'doc_id': doc_id
                                        }
                                    )
                                    st.write(f"🔍 DEBUG: Документ проиндексирован в RAG системе")
                                else:
                                    st.warning("⚠️ Нет текста для индексации в RAG")
                            except Exception as e:
                                st.error(f"❌ Ошибка индексации в RAG: {e}")
                                import traceback
                                st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
                            
                            added_count += 1
                    except Exception as e:
                        st.write(f"🔍 DEBUG: Ошибка добавления документа: {e}")
                        import traceback
                        st.write(f"🔍 DEBUG: Трассировка: {traceback.format_exc()}")
            
            st.success(f"✅ Добавлено {added_count} документов в БЗ")
            
            # Сохраняем тестовые вопросы в БЗ как метаданные
            test_questions = st.session_state.get('generated_test_questions')
            st.write(f"🔍 DEBUG: Проверяем наличие тестовых вопросов: {len(test_questions) if test_questions else 0}")
            
            if test_questions:
                st.write(f"🔍 DEBUG: Сохраняем тестовые вопросы в БЗ {kb_id}")
                try:
                    # Сохраняем тестовые вопросы в БЗ
                    self.smart_librarian._save_test_questions_to_kb(kb_id, test_questions)
                    st.success(f"✅ Тестовые вопросы сохранены в БЗ {kb_id}")
                    
                    # Показываем тестирование релевантности
                    st.write(f"🔍 DEBUG: Показываем тестирование релевантности для БЗ {kb_id}")
                    self._show_relevance_testing_after_creation(kb_id, test_questions)
                except Exception as e:
                    st.error(f"❌ Ошибка сохранения тестовых вопросов: {e}")
                    import traceback
                    st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
            else:
                st.info("ℹ️ Тестовые вопросы не сгенерированы. Нажмите '🧪 Тестовые вопросы' для их создания.")
            
        except Exception as e:
            st.error(f"❌ Ошибка добавления документов: {e}")
            import traceback
            st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
    
    def _show_relevance_testing_after_creation(self, kb_id: int, test_questions: List[Dict]):
        """Показать тестирование релевантности после создания БЗ"""
        st.markdown("---")
        st.subheader("🧪 Тестирование релевантности созданной БЗ")
        
        st.write(f"🔍 DEBUG: Показываем {len(test_questions)} тестовых вопросов для БЗ {kb_id}")
        st.info(f"Тестируем БЗ ID: {kb_id}")
        st.success("✅ Тестовые вопросы сохранены в БЗ и доступны через API")
        st.info(f"🌐 API endpoint: `/kb-test-questions/{kb_id}` для получения тестовых вопросов")
        
        # Кнопки для проверки сохраненных данных
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Загрузить тестовые вопросы из БЗ", key=f"load_test_questions_from_kb_{kb_id}"):
                try:
                    saved_questions = self.smart_librarian.get_test_questions_from_kb(kb_id)
                    if saved_questions:
                        st.success(f"✅ Загружено {len(saved_questions)} тестовых вопросов из БЗ")
                        st.write("**Сохраненные тестовые вопросы:**")
                        for i, q in enumerate(saved_questions, 1):
                            st.write(f"{i}. {q.get('question', 'Вопрос не найден')}")
                    else:
                        st.warning("⚠️ Тестовые вопросы не найдены в БЗ")
                except Exception as e:
                    st.error(f"❌ Ошибка загрузки тестовых вопросов: {e}")
        
        with col2:
            if st.button("📄 Проверить метаданные БЗ", key=f"check_saved_metadata_{kb_id}"):
                try:
                    documents = self.kb_manager.get_documents(kb_id)
                    if documents:
                        doc = documents[0]  # Берем первый документ
                        metadata = json.loads(doc.get('metadata', '{}')) if doc.get('metadata') else {}
                        
                        st.success(f"✅ Метаданные загружены из БЗ")
                        st.write("**Сохраненные метаданные (без текстовых полей):**")
                        
                        # Показываем только ключи метаданных
                        metadata_keys = list(metadata.keys())
                        st.write(f"**Ключи метаданных:** {', '.join(metadata_keys)}")
                        
                        # Показываем основные поля
                        st.write(f"**Название файла:** {metadata.get('file_name', 'Не указано')}")
                        st.write(f"**Категория:** {metadata.get('category', 'Не указана')}")
                        st.write(f"**Размер файла:** {metadata.get('file_size', 0)} байт")
                        st.write(f"**Количество изображений:** {metadata.get('images_count', 0)}")
                        st.write(f"**Уверенность:** {metadata.get('confidence', 0)}")
                        
                        st.info("ℹ️ Полный текст документа хранится в RAG системе, а не в метаданных SQLite")
                    else:
                        st.warning("⚠️ Документы не найдены в БЗ")
                except Exception as e:
                    st.error(f"❌ Ошибка проверки метаданных: {e}")
        
        # Кнопка для тестирования RAG поиска
        st.markdown("---")
        st.subheader("🔍 Тестирование RAG поиска")
        
        test_query = st.text_input("Введите тестовый запрос для поиска в RAG:", key=f"test_rag_query_{kb_id}")
        if st.button("🔍 Поиск в RAG", key=f"test_rag_search_{kb_id}"):
            if test_query:
                try:
                    with st.spinner("Ищем в RAG системе..."):
                        # Тестируем поиск в RAG
                        results = self.rag.get_response_with_context(
                            test_query, 
                            kb_ids=[kb_id], 
                            context_limit=3
                        )
                        
                        st.success("✅ Поиск в RAG выполнен")
                        st.write("**Результат поиска:**")
                        st.write(results)
                        
                        # Также показываем найденные документы
                        try:
                            docs = self.rag.search_documents(test_query, kb_ids=[kb_id], limit=3)
                            if docs:
                                st.write("**Найденные документы:**")
                                for i, doc in enumerate(docs, 1):
                                    st.write(f"{i}. {doc.get('title', 'Без названия')}")
                                    st.write(f"   Релевантность: {doc.get('score', 'N/A')}")
                                    st.write(f"   Содержимое: {doc.get('content', '')[:200]}...")
                            else:
                                st.warning("⚠️ Документы не найдены в RAG")
                        except Exception as e:
                            st.warning(f"⚠️ Ошибка поиска документов: {e}")
                            
                except Exception as e:
                    st.error(f"❌ Ошибка поиска в RAG: {e}")
                    import traceback
                    st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
            else:
                st.warning("⚠️ Введите тестовый запрос")
        
        for i, question in enumerate(test_questions, 1):
            with st.expander(f"❓ Вопрос {i}: {question['question']}"):
                st.write(f"**Категория:** {question.get('category', 'Не указана')}")
                st.write(f"**Сложность:** {question.get('difficulty', 'Не указана')}")
                st.write(f"**Ключевые слова:** {', '.join(question.get('expected_keywords', []))}")
                
                if st.button(f"🧪 Тестировать на БЗ {kb_id}", key=f"test_question_kb_{kb_id}_{i}"):
                    try:
                        with st.spinner("Тестируем вопрос через RAG систему..."):
                            # Тестируем вопрос через RAG
                            answer = self.rag.get_response_with_context(
                                question['question'], 
                                kb_ids=[kb_id], 
                                context_limit=3
                            )
                        
                        st.success("✅ Ответ получен:")
                        st.write(answer)
                        
                        # Оценка релевантности
                        relevance_score = self._calculate_relevance_score(question, answer)
                        st.metric("Оценка релевантности", f"{relevance_score:.1f}/10")
                        
                        # Показываем найденные источники
                        try:
                            sources = self.rag.search_documents(question['question'], kb_ids=[kb_id], limit=3)
                            if sources:
                                st.write("**Найденные источники:**")
                                for j, source in enumerate(sources, 1):
                                    st.write(f"{j}. {source.get('title', 'Без названия')} (релевантность: {source.get('score', 0):.3f})")
                            else:
                                st.warning("⚠️ Источники не найдены в БЗ")
                        except Exception as e:
                            st.warning(f"⚠️ Ошибка поиска источников: {e}")
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка тестирования: {e}")
                        import traceback
                        st.write(f"🔍 DEBUG: Трассировка ошибки: {traceback.format_exc()}")
    
    def _calculate_relevance_score(self, question: Dict, answer: str) -> float:
        """Простая оценка релевантности ответа"""
        if not answer or "не найдено" in answer.lower() or "недостаточно данных" in answer.lower():
            return 2.0
        
        # Проверяем наличие ключевых слов
        expected_keywords = question.get('expected_keywords', [])
        found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in answer.lower())
        
        if expected_keywords:
            keyword_score = (found_keywords / len(expected_keywords)) * 5.0
        else:
            keyword_score = 3.0
        
        # Длина ответа (не слишком короткий, не слишком длинный)
        length_score = min(5.0, max(1.0, len(answer) / 100))
        
        return min(10.0, keyword_score + length_score)
        
        st.markdown("---")
        
        # Статус всех агентов
        self.model_manager.render_agent_status(agents)
    
    def _smart_kb_check(self, suggested_name, suggested_category, analyses):
        """Умная проверка KB на дубликаты и предложение объединения"""
        from modules.core.knowledge_manager import KnowledgeBaseManager
        
        kb_manager = KnowledgeBaseManager()
        existing_kbs = kb_manager.get_knowledge_bases(active_only=True)
        
        # Проверяем точные совпадения
        exact_matches = [kb for kb in existing_kbs if kb['name'].lower() == suggested_name.lower()]
        
        # Проверяем похожие названия
        similar_matches = []
        for kb in existing_kbs:
            if (suggested_name.lower() in kb['name'].lower() or 
                kb['name'].lower() in suggested_name.lower()):
                similar_matches.append(kb)
        
        # Проверяем совпадения по категории
        category_matches = [kb for kb in existing_kbs if kb['category'] == suggested_category]
        
        return {
            'exact_matches': exact_matches,
            'similar_matches': similar_matches,
            'category_matches': category_matches,
            'has_conflicts': len(exact_matches) > 0 or len(similar_matches) > 0
        }
    
    def _execute_save_to_kb_transactional(self, analyses, selected_docs, selected_images):
        """Выполняет сохранение документов в KB с транзакционной поддержкой"""
        from modules.core.knowledge_manager import KnowledgeBaseManager
        from datetime import datetime
        
        kb_manager = KnowledgeBaseManager()
        pending_params = st.session_state.get("pending_kb_params", {})
        
        # Показываем индикатор прогресса
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Начинаем транзакцию
            status_text.text("🔄 Начинаем транзакцию...")
            progress_bar.progress(10)
            
            transaction_id = self.smart_librarian.transaction_manager.begin_transaction(
                operation_type="kb_save_operation",
                metadata={
                    'documents_count': len(selected_docs),
                    'images_count': len(selected_images),
                    'action': pending_params.get("action", "unknown"),
                    'kb_name': pending_params.get("name", "unknown")
                }
            )
            
            progress_bar.progress(20)
            status_text.text("✅ Транзакция начата")
            if pending_params["action"] == "create_new":
                # Используем оригинальное имя без автоматического переименования
                kb_name = pending_params["name"]
                
                # Создаем новую KB
                status_text.text("📚 Создаем новую базу знаний...")
                progress_bar.progress(30)
                
                kb_id = kb_manager.create_knowledge_base(
                    name=kb_name,
                    description=pending_params["description"],
                    category=pending_params["category"],
                    created_by="KB Admin"
                )
                
                progress_bar.progress(40)
                status_text.text("✅ База знаний создана")
            else:
                # Используем существующую KB
                kb_id = pending_params["kb_id"]
                kb_name = pending_params["name"]
                progress_bar.progress(40)
                status_text.text("📚 Используем существующую базу знаний")
            
            # Сохраняем документы
            status_text.text("💾 Сохраняем документы...")
            progress_bar.progress(50)
            
            saved_count = 0
            total_docs = len(selected_docs)
            
            for i, doc_idx in enumerate(selected_docs):
                analysis = analyses[doc_idx]
                
                # Обновляем прогресс для каждого документа
                doc_progress = 50 + (i / total_docs) * 30  # 50-80% для документов
                progress_bar.progress(int(doc_progress))
                status_text.text(f"💾 Сохраняем документ {i+1}/{total_docs}: {analysis.get('file_name', 'Документ')}")
                
                # Получаем полный текст для сохранения
                full_text = analysis.get('original_cleaned_text', analysis.get('full_cleaned_text', ''))
                if not full_text or (full_text.strip() == analysis.get('smart_summary', '').strip()):
                    full_text = analysis.get('raw_ocr_text', '')
                
                # Сохраняем документ
                doc_id = kb_manager.add_document(
                    kb_id=kb_id,
                    title=analysis.get('file_name', 'Документ'),
                    file_path=str(analysis.get('file_path', '')),
                    content_type=analysis.get('content_type', 'text/plain'),
                    file_size=analysis.get('file_size', 0),
                    metadata={
                        'ocr_cleaned': True,
                        'gemini_analyzed': bool(analysis.get('images')),
                        'text_length': len(full_text),
                        'summary_length': len(analysis.get('smart_summary', '')),
                        'content': full_text,
                        'summary': analysis.get('smart_summary', ''),
                        'processed': True,
                        'status': "processed"
                    }
                )
                
                # Сохраняем изображения и анализ Gemini
                if analysis.get('images'):
                    for image_info in analysis['images']:
                        kb_manager.add_image(
                            kb_id=kb_id,
                            image_path=image_info.get('image_path', ''),
                            image_name=image_info.get('image_name', ''),
                            image_description=image_info.get('description', ''),
                            llava_analysis=image_info.get('description', ''),
                        )
                
                saved_count += 1
            
            # Автоматически экспортируем KB в JSON
            status_text.text("📄 Экспортируем KB в JSON...")
            progress_bar.progress(85)
            
            try:
                json_file_path = kb_manager.export_kb_to_json(kb_id, "docs/kb")
                st.info(f"📄 KB экспортирована в JSON: {json_file_path}")
            except Exception as e:
                st.warning(f"⚠️ Не удалось экспортировать KB в JSON: {e}")
            
            # Подтверждаем транзакцию
            status_text.text("✅ Подтверждаем транзакцию...")
            progress_bar.progress(90)
            
            commit_success = self.smart_librarian.transaction_manager.commit_transaction(transaction_id)
            if not commit_success:
                raise Exception("Ошибка подтверждения транзакции")
            
            progress_bar.progress(100)
            status_text.text("🎉 Операция завершена успешно!")
            
            # Показываем результат
            if pending_params["action"] == "create_new":
                st.success(f"✅ Успешно создана KB '{kb_name}' и сохранено {saved_count} документов!")
            else:
                st.success(f"✅ Успешно сохранено {saved_count} документов в KB '{kb_name}'!")
            
            # Предлагаем архивировать сохраненные документы
            st.info("💡 Документы успешно сохранены в KB. Хотите архивировать их, чтобы убрать из списка новых документов?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📦 Архивировать сохраненные документы", key="archive_saved_docs_final", type="primary"):
                    archived_count = 0
                    for doc_idx in selected_docs:
                        analysis = analyses[doc_idx]
                        file_path = Path(analysis.get('file_path', ''))
                        if file_path.exists():
                            success, result = self.smart_librarian.document_manager.archive_document(file_path, "saved_to_kb")
                            if success:
                                archived_count += 1
                            else:
                                st.error(f"❌ Ошибка архивирования {file_path.name}: {result}")
                    
                    if archived_count > 0:
                        st.success(f"📦 Архивировано {archived_count} документов")
                        # Обновляем результаты анализа, убирая заархивированные документы
                        new_analyses = [analyses[i] for i in range(len(analyses)) if i not in selected_docs]
                        st.session_state.analysis_results['analyses'] = new_analyses
            
            with col2:
                if st.button("❌ Не архивировать", key="dont_archive_final"):
                    pass
            
            # Автоматически архивируем сохраненные документы
            archived_count = 0
            for doc_idx in selected_docs:
                analysis = analyses[doc_idx]
                file_path = Path(analysis.get('file_path', ''))
                if file_path.exists():
                    try:
                        success, result = self.smart_librarian.document_manager.archive_document(file_path, "saved_to_kb")
                        if success:
                            archived_count += 1
                        else:
                            st.warning(f"⚠️ Не удалось заархивировать {file_path.name}: {result}")
                    except Exception as e:
                        st.warning(f"⚠️ Ошибка архивирования {file_path.name}: {e}")
            
            if archived_count > 0:
                st.info(f"📦 Автоматически заархивировано {archived_count} документов")
                # Обновляем результаты анализа, убирая заархивированные документы
                new_analyses = [analyses[i] for i in range(len(analyses)) if i not in selected_docs]
                st.session_state.analysis_results['analyses'] = new_analyses
            
            # Сбрасываем состояние
            st.session_state["show_save_dialog"] = False
            st.session_state["pending_kb_params"] = None
            st.session_state["last_saved_selection"] = f"{selected_docs}_{selected_images}"
            for i in range(len(analyses)):
                st.session_state[f"selected_doc_{i}"] = False
            st.rerun()
            
        except Exception as e:
            # Откатываем транзакцию при ошибке
            try:
                status_text.text("🔄 Откатываем транзакцию...")
                progress_bar.progress(0)
                
                rollback_success = self.smart_librarian.transaction_manager.rollback_transaction(transaction_id)
                if rollback_success:
                    status_text.text("❌ Ошибка - транзакция откачена")
                    st.error(f"❌ Ошибка при сохранении в KB: {e}")
                    st.warning("🔄 Транзакция откачена. Все изменения отменены.")
                else:
                    status_text.text("❌ Критическая ошибка")
                    st.error(f"❌ Критическая ошибка при сохранении в KB: {e}")
                    st.error("⚠️ Не удалось откатить транзакцию. Проверьте состояние системы.")
            except Exception as rollback_error:
                status_text.text("🚨 Критическая ошибка системы")
                st.error(f"❌ Критическая ошибка при сохранении в KB: {e}")
                st.error(f"⚠️ Ошибка отката транзакции: {rollback_error}")
                st.error("🚨 Требуется ручная проверка состояния системы!")
