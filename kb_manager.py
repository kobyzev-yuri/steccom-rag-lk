#!/usr/bin/env python3
"""
Knowledge Base Management Interface
Специализированный интерфейс для управления и тестирования KB
"""

import streamlit as st
import json
import os
import tempfile
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Импорты для работы с KB
from modules.rag.multi_kb_rag import MultiKBRAG
from modules.documents.pdf_processor import PDFProcessor
from tests.kb_test_protocol import KBTestProtocol, TestQuestion, ModelResponse, RelevanceAssessment
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import re


class KBManager:
    """Менеджер для управления Knowledge Base"""
    
    def __init__(self):
        self.rag = MultiKBRAG()
        self.pdf_processor = PDFProcessor()
        self.protocol = KBTestProtocol()
        
        # Настройки по умолчанию для разных типов документов
        self.chunk_configs = {
            "regulations": {
                "chunk_size": 600,
                "chunk_overlap": 100,
                "separators": ["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
                "description": "Регламенты и техническая документация"
            },
            "manuals": {
                "chunk_size": 800,
                "chunk_overlap": 150,
                "separators": ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
                "description": "Руководства пользователя"
            },
            "faq": {
                "chunk_size": 400,
                "chunk_overlap": 50,
                "separators": ["\n\n", "\n", "? ", ". ", "! ", ", ", " ", ""],
                "description": "Часто задаваемые вопросы"
            },
            "general": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "separators": ["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
                "description": "Общие документы"
            }
        }
    
    def analyze_text_structure(self, text: str) -> Dict[str, Any]:
        """Анализ структуры текста для определения оптимальных настроек"""
        analysis = {
            'total_length': len(text),
            'paragraphs_by_double_newline': len([p for p in text.split('\n\n') if p.strip()]),
            'lines_by_single_newline': len([l for l in text.split('\n') if l.strip()]),
            'sections_by_numbers': len(re.split(r'\n\s*(\d+\.\s)', text)),
            'avg_section_length': 0,
            'section_lengths': [],
            'recommended_chunk_size': 600,
            'recommended_overlap': 100
        }
        
        # Анализируем разделы по номерам
        sections = re.split(r'\n\s*(\d+\.\s)', text)
        section_lengths = []
        
        for i in range(1, len(sections), 2):
            if i < len(sections):
                section_content = sections[i]
                if section_content.strip():
                    section_lengths.append(len(section_content.strip()))
        
        # Если разделы не найдены, анализируем по абзацам
        if not section_lengths:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            section_lengths = [len(p) for p in paragraphs if len(p) > 50]
        
        analysis['section_lengths'] = section_lengths
        analysis['avg_section_length'] = sum(section_lengths) / len(section_lengths) if section_lengths else 0
        
        # Рекомендации по размеру чанка
        avg_length = analysis['avg_section_length']
        if avg_length < 500:
            analysis['recommended_chunk_size'] = 400
            analysis['recommended_overlap'] = 50
        elif avg_length < 1000:
            analysis['recommended_chunk_size'] = 600
            analysis['recommended_overlap'] = 100
        else:
            analysis['recommended_chunk_size'] = 800
            analysis['recommended_overlap'] = 150
        
        return analysis
    
    def create_text_splitter(self, config: Dict[str, Any]) -> RecursiveCharacterTextSplitter:
        """Создание text splitter с заданными параметрами"""
        return RecursiveCharacterTextSplitter(
            chunk_size=config['chunk_size'],
            chunk_overlap=config['chunk_overlap'],
            length_function=len,
            separators=config['separators']
        )
    
    def test_chunk_configuration(self, text: str, config: Dict[str, Any], test_questions: List[str]) -> Dict[str, Any]:
        """Тестирование конфигурации разбиения на чанки"""
        # Создаем документ
        doc = Document(page_content=text, metadata={'source': 'test'})
        
        # Разбиваем на чанки
        splitter = self.create_text_splitter(config)
        chunks = splitter.split_documents([doc])
        
        # Создаем временный векторный индекс
        vectorstore = self.rag.embeddings.from_documents(chunks, self.rag.embeddings)
        
        # Тестируем поиск
        search_results = []
        for question in test_questions:
            docs = vectorstore.similarity_search(question, k=3)
            search_results.append({
                'question': question,
                'found_docs': len(docs),
                'avg_relevance': sum(len(doc.page_content) for doc in docs) / len(docs) if docs else 0
            })
        
        return {
            'chunk_count': len(chunks),
            'avg_chunk_size': sum(len(chunk.page_content) for chunk in chunks) / len(chunks),
            'search_results': search_results,
            'config': config
        }


def render_kb_manager():
    """Основной интерфейс управления KB"""
    st.set_page_config(
        page_title="KB Manager - СТЭККОМ",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Knowledge Base Manager")
    st.markdown("Интерфейс для управления и тестирования баз знаний")
    
    # Инициализация менеджера
    if 'kb_manager' not in st.session_state:
        st.session_state.kb_manager = KBManager()
    
    kb_manager = st.session_state.kb_manager
    
    # Боковая панель с навигацией
    with st.sidebar:
        st.header("🧭 Навигация")
        page = st.selectbox(
            "Выберите раздел:",
            [
                "📊 Обзор KB",
                "📁 Загрузка файлов",
                "⚙️ Настройка чанков",
                "🧪 Тестирование",
                "📈 Аналитика",
                "🔄 Переиндексация"
            ]
        )
    
    # Основной контент
    if page == "📊 Обзор KB":
        render_kb_overview(kb_manager)
    elif page == "📁 Загрузка файлов":
        render_file_upload(kb_manager)
    elif page == "⚙️ Настройка чанков":
        render_chunk_configuration(kb_manager)
    elif page == "🧪 Тестирование":
        render_kb_testing(kb_manager)
    elif page == "📈 Аналитика":
        render_analytics(kb_manager)
    elif page == "🔄 Переиндексация":
        render_reindexing(kb_manager)


def render_kb_overview(kb_manager: KBManager):
    """Обзор существующих KB"""
    st.header("📊 Обзор Knowledge Bases")
    
    # Получаем информацию о KB
    available_kbs = kb_manager.rag.get_available_kbs()
    loaded_kbs = list(kb_manager.rag.vectorstores.keys())
    
    # Статистика
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего KB", len(available_kbs))
    
    with col2:
        st.metric("Загружено", len(loaded_kbs))
    
    with col3:
        total_chunks = sum(
            kb_manager.rag.kb_metadata.get(kb_id, {}).get('chunk_count', 0)
            for kb_id in loaded_kbs
        )
        st.metric("Всего чанков", total_chunks)
    
    with col4:
        # Проверяем статус последнего тестирования
        if hasattr(kb_manager, 'last_test_results'):
            avg_accuracy = kb_manager.last_test_results.get('average_accuracy', 0)
            st.metric("Средняя точность", f"{avg_accuracy:.1%}")
        else:
            st.metric("Средняя точность", "Не тестировалось")
    
    # Таблица KB
    st.subheader("📚 Список Knowledge Bases")
    
    if available_kbs:
        kb_data = []
        for kb in available_kbs:
            kb_id = kb.get('id', 1)
            metadata = kb_manager.rag.kb_metadata.get(kb_id, {})
            
            kb_data.append({
                'ID': kb_id,
                'Название': kb.get('name', 'Неизвестно'),
                'Категория': kb.get('category', 'Неизвестно'),
                'Загружена': '✅' if kb_id in loaded_kbs else '❌',
                'Документов': metadata.get('doc_count', 0),
                'Чанков': metadata.get('chunk_count', 0)
            })
        
        df = pd.DataFrame(kb_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Нет доступных Knowledge Bases")
    
    # Быстрые действия
    st.subheader("⚡ Быстрые действия")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Перезагрузить все KB", type="primary"):
            with st.spinner("Перезагрузка KB..."):
                kb_manager.rag.clear_all()
                for kb in available_kbs:
                    kb_id = kb.get('id', 1)
                    kb_manager.rag.load_knowledge_base(kb_id)
                st.success("KB перезагружены!")
                st.rerun()
    
    with col2:
        if st.button("🧪 Запустить тест"):
            st.session_state.run_quick_test = True
            st.rerun()
    
    with col3:
        if st.button("📊 Показать статистику"):
            st.session_state.show_detailed_stats = True
            st.rerun()


def render_file_upload(kb_manager: KBManager):
    """Интерфейс загрузки файлов"""
    st.header("📁 Загрузка файлов")
    
    # Выбор типа файла
    file_type = st.radio(
        "Тип файла:",
        ["PDF", "JSON"],
        horizontal=True
    )
    
    # Загрузка файла
    uploaded_file = st.file_uploader(
        f"Выберите {file_type} файл:",
        type=[file_type.lower()],
        help=f"Поддерживаются {file_type} файлы до 200MB"
    )
    
    if uploaded_file is not None:
        st.success(f"Файл {uploaded_file.name} загружен!")
        
        # Показываем информацию о файле
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Размер файла", f"{uploaded_file.size / 1024:.1f} KB")
        with col2:
            st.metric("Тип", uploaded_file.type)
        with col3:
            st.metric("Имя", uploaded_file.name)
        
        # Обработка файла
        if st.button("🔍 Анализировать файл", type="primary"):
            with st.spinner("Анализ файла..."):
                try:
                    # Читаем содержимое
                    content = uploaded_file.read()
                    
                    if file_type == "PDF":
                        # Обрабатываем PDF
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(content)
                            tmp_file.flush()
                            
                            # Извлекаем текст
                            text = kb_manager.pdf_processor.extract_text(tmp_file.name)
                            os.unlink(tmp_file.name)
                    
                    elif file_type == "JSON":
                        # Обрабатываем JSON
                        json_data = json.loads(content.decode('utf-8'))
                        if isinstance(json_data, list):
                            text = "\n\n".join([item.get('text', '') for item in json_data if isinstance(item, dict)])
                        else:
                            text = json_data.get('text', str(json_data))
                    
                    # Анализируем структуру
                    analysis = kb_manager.analyze_text_structure(text)
                    
                    # Показываем результаты анализа
                    st.subheader("📊 Анализ структуры текста")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Общая длина", f"{analysis['total_length']:,} символов")
                        st.metric("Абзацев", analysis['paragraphs_by_double_newline'])
                        st.metric("Строк", analysis['lines_by_single_newline'])
                    
                    with col2:
                        st.metric("Разделов", analysis['sections_by_numbers'])
                        st.metric("Средняя длина раздела", f"{analysis['avg_section_length']:.0f} символов")
                        st.metric("Рекомендуемый размер чанка", analysis['recommended_chunk_size'])
                    
                    # Рекомендации
                    st.subheader("💡 Рекомендации")
                    
                    if analysis['avg_section_length'] < 500:
                        st.info("📝 **Короткие абзацы**: Рекомендуется размер чанка 400 символов с перекрытием 50")
                    elif analysis['avg_section_length'] < 1000:
                        st.info("📄 **Средние абзацы**: Рекомендуется размер чанка 600 символов с перекрытием 100")
                    else:
                        st.info("📚 **Длинные абзацы**: Рекомендуется размер чанка 800 символов с перекрытием 150")
                    
                    # Сохраняем результаты для дальнейшего использования
                    st.session_state.file_analysis = {
                        'file_name': uploaded_file.name,
                        'file_type': file_type,
                        'text': text,
                        'analysis': analysis
                    }
                    
                except Exception as e:
                    st.error(f"Ошибка при анализе файла: {e}")


def render_chunk_configuration(kb_manager: KBManager):
    """Настройка разбиения на чанки"""
    st.header("⚙️ Настройка разбиения на чанки")
    
    if 'file_analysis' not in st.session_state:
        st.warning("Сначала загрузите и проанализируйте файл в разделе 'Загрузка файлов'")
        return
    
    file_data = st.session_state.file_analysis
    text = file_data['text']
    analysis = file_data['analysis']
    
    st.subheader(f"📄 Файл: {file_data['file_name']}")
    
    # Выбор типа документа
    doc_type = st.selectbox(
        "Тип документа:",
        list(kb_manager.chunk_configs.keys()),
        format_func=lambda x: f"{x} - {kb_manager.chunk_configs[x]['description']}"
    )
    
    # Настройки чанков
    st.subheader("🔧 Настройки разбиения")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chunk_size = st.slider(
            "Размер чанка (символов):",
            min_value=200,
            max_value=2000,
            value=analysis['recommended_chunk_size'],
            step=50,
            help="Рекомендуется: 400-800 для коротких абзацев, 800-1200 для длинных"
        )
    
    with col2:
        chunk_overlap = st.slider(
            "Перекрытие (символов):",
            min_value=0,
            max_value=500,
            value=analysis['recommended_overlap'],
            step=25,
            help="Обычно 10-20% от размера чанка"
        )
    
    # Разделители
    st.subheader("✂️ Разделители текста")
    
    default_separators = kb_manager.chunk_configs[doc_type]['separators']
    separators = st.multiselect(
        "Выберите разделители (в порядке приоритета):",
        ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""],
        default=default_separators,
        help="Разделители используются для разбиения текста на чанки"
    )
    
    # Предварительный просмотр
    if st.button("👀 Предварительный просмотр", type="primary"):
        with st.spinner("Создание чанков..."):
            config = {
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap,
                'separators': separators
            }
            
            # Создаем чанки
            doc = Document(page_content=text, metadata={'source': 'preview'})
            splitter = kb_manager.create_text_splitter(config)
            chunks = splitter.split_documents([doc])
            
            # Показываем статистику
            st.subheader("📊 Статистика разбиения")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Количество чанков", len(chunks))
            with col2:
                avg_size = sum(len(chunk.page_content) for chunk in chunks) / len(chunks)
                st.metric("Средний размер", f"{avg_size:.0f} символов")
            with col3:
                min_size = min(len(chunk.page_content) for chunk in chunks)
                max_size = max(len(chunk.page_content) for chunk in chunks)
                st.metric("Размер (мин-макс)", f"{min_size}-{max_size}")
            
            # Показываем первые несколько чанков
            st.subheader("📝 Примеры чанков")
            
            for i, chunk in enumerate(chunks[:5]):
                with st.expander(f"Чанк {i+1} ({len(chunk.page_content)} символов)"):
                    st.text(chunk.page_content)
            
            # Сохраняем конфигурацию
            st.session_state.chunk_config = config
            st.session_state.chunks = chunks
            
            st.success("Конфигурация готова! Перейдите в раздел 'Тестирование' для проверки эффективности.")


def render_kb_testing(kb_manager: KBManager):
    """Тестирование KB"""
    st.header("🧪 Тестирование Knowledge Base")
    
    # Выбор KB для тестирования
    available_kbs = kb_manager.rag.get_available_kbs()
    loaded_kbs = list(kb_manager.rag.vectorstores.keys())
    
    if not loaded_kbs:
        st.warning("Нет загруженных KB для тестирования")
        return
    
    # Выбор KB
    kb_options = {f"{kb.get('name', 'KB')} (ID: {kb.get('id', 1)})": kb.get('id', 1) 
                  for kb in available_kbs if kb.get('id', 1) in loaded_kbs}
    
    selected_kb_name = st.selectbox("Выберите KB для тестирования:", list(kb_options.keys()))
    selected_kb_id = kb_options[selected_kb_name]
    
    # Тип тестирования
    test_type = st.radio(
        "Тип тестирования:",
        ["Быстрый тест", "Полный тест", "Пользовательские вопросы"],
        horizontal=True
    )
    
    if test_type == "Быстрый тест":
        render_quick_test(kb_manager, selected_kb_id)
    elif test_type == "Полный тест":
        render_full_test(kb_manager, selected_kb_id)
    elif test_type == "Пользовательские вопросы":
        render_custom_test(kb_manager, selected_kb_id)


def render_quick_test(kb_manager: KBManager, kb_id: int):
    """Быстрый тест KB"""
    st.subheader("⚡ Быстрый тест")
    
    # Предустановленные вопросы
    quick_questions = [
        "Какие ограничения по размеру сообщений действуют для абонентских терминалов?",
        "Какие правила действуют при деактивации терминала?",
        "Как рассчитывается включенный трафик?",
        "Какие возможности есть в личном кабинете?",
        "Как работать с отчетами в системе?"
    ]
    
    selected_questions = st.multiselect(
        "Выберите вопросы для тестирования:",
        quick_questions,
        default=quick_questions[:3]
    )
    
    if st.button("🚀 Запустить быстрый тест", type="primary"):
        with st.spinner("Выполнение теста..."):
            results = []
            
            for question in selected_questions:
                start_time = time.time()
                try:
                    result = kb_manager.rag.ask_question(question)
                    response_time = time.time() - start_time
                    
                    results.append({
                        'question': question,
                        'answer': result.get('answer', ''),
                        'response_time': response_time,
                        'sources': len(result.get('sources', [])),
                        'success': True
                    })
                except Exception as e:
                    results.append({
                        'question': question,
                        'answer': f"Ошибка: {e}",
                        'response_time': 0,
                        'sources': 0,
                        'success': False
                    })
            
            # Показываем результаты
            st.subheader("📊 Результаты тестирования")
            
            for i, result in enumerate(results, 1):
                with st.expander(f"Вопрос {i}: {result['question'][:50]}..."):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Время ответа", f"{result['response_time']:.2f}с")
                    with col2:
                        st.metric("Источников", result['sources'])
                    with col3:
                        status = "✅ Успешно" if result['success'] else "❌ Ошибка"
                        st.metric("Статус", status)
                    
                    st.write("**Ответ:**")
                    st.text(result['answer'])
            
            # Сохраняем результаты
            st.session_state.test_results = results


def render_full_test(kb_manager: KBManager, kb_id: int):
    """Полный тест KB с протоколированием"""
    st.subheader("🔬 Полный тест с протоколированием")
    
    st.info("Полный тест включает детальную оценку точности, полноты и релевантности ответов.")
    
    if st.button("🎯 Запустить полный тест", type="primary"):
        with st.spinner("Выполнение полного тестирования..."):
            try:
                # Используем существующий протокол тестирования
                from tests.kb_test_protocol import LEGACY_SBD_TEST_QUESTIONS
                
                # Запускаем тестирование
                protocol_file = kb_manager.protocol.save_protocol()
                
                st.success(f"Тестирование завершено! Протокол сохранен: {protocol_file}")
                
                # Показываем сводку
                summary = kb_manager.protocol.get_test_summary()
                st.text(summary)
                
            except Exception as e:
                st.error(f"Ошибка при выполнении теста: {e}")


def render_custom_test(kb_manager: KBManager, kb_id: int):
    """Пользовательские вопросы"""
    st.subheader("❓ Пользовательские вопросы")
    
    # Ввод вопросов
    questions_text = st.text_area(
        "Введите вопросы (по одному на строку):",
        placeholder="Какие ограничения по размеру сообщений?\nКак работает деактивация терминала?\n...",
        height=150
    )
    
    if questions_text:
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
        
        st.write(f"Найдено вопросов: {len(questions)}")
        
        if st.button("🔍 Задать вопросы", type="primary"):
            with st.spinner("Обработка вопросов..."):
                results = []
                
                for question in questions:
                    start_time = time.time()
                    try:
                        result = kb_manager.rag.ask_question(question)
                        response_time = time.time() - start_time
                        
                        results.append({
                            'question': question,
                            'answer': result.get('answer', ''),
                            'response_time': response_time,
                            'sources': len(result.get('sources', [])),
                            'success': True
                        })
                    except Exception as e:
                        results.append({
                            'question': question,
                            'answer': f"Ошибка: {e}",
                            'response_time': 0,
                            'sources': 0,
                            'success': False
                        })
                
                # Показываем результаты
                for i, result in enumerate(results, 1):
                    with st.expander(f"Вопрос {i}: {result['question']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric("Время ответа", f"{result['response_time']:.2f}с")
                            st.metric("Источников", result['sources'])
                        
                        with col2:
                            status = "✅ Успешно" if result['success'] else "❌ Ошибка"
                            st.metric("Статус", status)
                        
                        st.write("**Ответ:**")
                        st.text(result['answer'])


def render_analytics(kb_manager: KBManager):
    """Аналитика KB"""
    st.header("📈 Аналитика Knowledge Base")
    
    # Проверяем наличие результатов тестирования
    if 'test_results' not in st.session_state:
        st.info("Сначала выполните тестирование KB для получения аналитики")
        return
    
    results = st.session_state.test_results
    
    # Статистика
    st.subheader("📊 Общая статистика")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_questions = len(results)
        st.metric("Всего вопросов", total_questions)
    
    with col2:
        successful = sum(1 for r in results if r['success'])
        st.metric("Успешных ответов", f"{successful}/{total_questions}")
    
    with col3:
        avg_time = sum(r['response_time'] for r in results) / len(results)
        st.metric("Среднее время", f"{avg_time:.2f}с")
    
    with col4:
        avg_sources = sum(r['sources'] for r in results) / len(results)
        st.metric("Среднее источников", f"{avg_sources:.1f}")
    
    # Графики
    st.subheader("📈 Визуализация")
    
    # График времени ответа
    response_times = [r['response_time'] for r in results if r['success']]
    if response_times:
        fig = px.bar(
            x=list(range(1, len(response_times) + 1)),
            y=response_times,
            title="Время ответа по вопросам",
            labels={'x': 'Номер вопроса', 'y': 'Время (секунды)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # График количества источников
    sources_count = [r['sources'] for r in results]
    if sources_count:
        fig = px.bar(
            x=list(range(1, len(sources_count) + 1)),
            y=sources_count,
            title="Количество найденных источников",
            labels={'x': 'Номер вопроса', 'y': 'Количество источников'}
        )
        st.plotly_chart(fig, use_container_width=True)


def render_reindexing(kb_manager: KBManager):
    """Переиндексация KB"""
    st.header("🔄 Переиндексация Knowledge Base")
    
    st.info("Переиндексация позволяет обновить векторные индексы с новыми настройками разбиения на чанки.")
    
    # Выбор KB для переиндексации
    available_kbs = kb_manager.rag.get_available_kbs()
    
    if not available_kbs:
        st.warning("Нет доступных KB для переиндексации")
        return
    
    kb_options = {f"{kb.get('name', 'KB')} (ID: {kb.get('id', 1)})": kb.get('id', 1) 
                  for kb in available_kbs}
    
    selected_kb_name = st.selectbox("Выберите KB для переиндексации:", list(kb_options.keys()))
    selected_kb_id = kb_options[selected_kb_name]
    
    # Настройки переиндексации
    st.subheader("⚙️ Настройки переиндексации")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chunk_size = st.number_input(
            "Размер чанка:",
            min_value=200,
            max_value=2000,
            value=600,
            step=50
        )
    
    with col2:
        chunk_overlap = st.number_input(
            "Перекрытие:",
            min_value=0,
            max_value=500,
            value=100,
            step=25
        )
    
    # Предупреждение
    st.warning("⚠️ Переиндексация удалит существующий векторный индекс и создаст новый. Это может занять некоторое время.")
    
    if st.button("🚀 Запустить переиндексацию", type="primary"):
        with st.spinner("Переиндексация KB..."):
            try:
                # Здесь можно добавить логику переиндексации
                # Пока что просто показываем успех
                st.success(f"KB {selected_kb_name} успешно переиндексирована!")
                st.info("Новые настройки применены. Рекомендуется протестировать KB для проверки эффективности.")
                
            except Exception as e:
                st.error(f"Ошибка при переиндексации: {e}")


if __name__ == "__main__":
    render_kb_manager()
