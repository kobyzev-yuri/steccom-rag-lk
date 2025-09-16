"""
Knowledge Base Creation Assistant
Ассистент для создания и настройки баз знаний
"""

import streamlit as st
import os
import sqlite3
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime

class KBAssistant:
    def __init__(self, kb_manager, pdf_processor):
        self.kb_manager = kb_manager
        self.pdf_processor = pdf_processor
    
    def render_assistant(self):
        """Render KB creation assistant interface"""
        st.header("🤖 Ассистент создания базы знаний")
        
        # Step 1: Analyze existing files
        st.subheader("📁 Шаг 1: Анализ существующих файлов")
        
        upload_dir = Path("data/uploads")
        if upload_dir.exists():
            pdf_files = list(upload_dir.glob("*.pdf"))
            
            if pdf_files:
                st.success(f"Найдено {len(pdf_files)} PDF файлов в директории uploads")
                
                # Show file analysis
                with st.expander("📋 Анализ файлов"):
                    for pdf_file in pdf_files:
                        file_size = pdf_file.stat().st_size / 1024  # KB
                        st.write(f"• **{pdf_file.name}** ({file_size:.1f} KB)")
                        
                        # Try to extract basic info
                        try:
                            metadata = self.pdf_processor.get_pdf_metadata(str(pdf_file))
                            if metadata.get('title'):
                                st.write(f"  - Название: {metadata['title']}")
                            if metadata.get('pages'):
                                st.write(f"  - Страниц: {metadata['pages']}")
                        except:
                            st.write("  - Метаданные недоступны")
                
                # Suggest KB structure
                st.subheader("💡 Шаг 2: Предложения по структуре БЗ")
                
                # Analyze filenames to suggest categories
                suggested_categories = self._analyze_filenames(pdf_files)
                
                if suggested_categories:
                    st.write("**Рекомендуемые категории на основе имен файлов:**")
                    for category, files in suggested_categories.items():
                        st.write(f"• **{category}**: {', '.join(files)}")
                
                # Quick setup options
                st.subheader("⚡ Шаг 3: Быстрая настройка")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚀 Создать БЗ 'Технические регламенты'"):
                        self._create_tech_regulations_kb(pdf_files)
                
                with col2:
                    if st.button("📚 Создать БЗ 'Документация СТЭККОМ'"):
                        self._create_steccom_docs_kb(pdf_files)
                
                # Manual setup
                st.subheader("🔧 Шаг 4: Ручная настройка")
                
                with st.form("manual_kb_setup"):
                    kb_name = st.text_input("Название БЗ", value="Технические регламенты")
                    kb_category = st.selectbox(
                        "Категория",
                        ["Технические регламенты", "Пользовательские инструкции", 
                         "Политики безопасности", "Процедуры биллинга", "Другое"]
                    )
                    kb_description = st.text_area(
                        "Описание", 
                        value="База знаний с техническими регламентами и документацией СТЭККОМ"
                    )
                    
                    # File selection
                    st.write("**Выберите файлы для включения:**")
                    selected_files = []
                    for pdf_file in pdf_files:
                        if st.checkbox(f"Включить: {pdf_file.name}", value=True):
                            selected_files.append(pdf_file)
                    
                    submitted = st.form_submit_button("Создать БЗ с выбранными файлами")
                    
                    if submitted and selected_files:
                        self._create_manual_kb(kb_name, kb_category, kb_description, selected_files)
            else:
                st.warning("В директории uploads не найдено PDF файлов")
                st.info("Загрузите PDF файлы через интерфейс 'Загрузка документов'")
        else:
            st.error("Директория uploads не найдена")
    
    def _analyze_filenames(self, pdf_files: List[Path]) -> Dict[str, List[str]]:
        """Analyze filenames to suggest categories"""
        categories = {}
        
        for pdf_file in pdf_files:
            filename = pdf_file.name.lower()
            
            if 'reg' in filename or 'регламент' in filename:
                category = "Технические регламенты"
            elif 'sbd' in filename:
                category = "Протоколы связи"
            elif 'gps' in filename or 'track' in filename:
                category = "Системы мониторинга"
            elif 'monitor' in filename:
                category = "Системы мониторинга"
            else:
                category = "Общая документация"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(pdf_file.name)
        
        return categories
    
    def _create_tech_regulations_kb(self, pdf_files: List[Path]):
        """Create technical regulations KB with all files"""
        try:
            # Create KB
            kb_id = self.kb_manager.create_knowledge_base(
                name="Технические регламенты",
                description="База знаний с техническими регламентами и стандартами СТЭККОМ",
                category="Технические регламенты",
                created_by=st.session_state.get('username', 'admin')
            )
            
            st.success(f"База знаний создана с ID: {kb_id}")
            
            # Process all files
            processed_count = 0
            progress_bar = st.progress(0)
            
            for i, pdf_file in enumerate(pdf_files):
                try:
                    # Read file content
                    with open(pdf_file, 'rb') as f:
                        file_content = f.read()
                    
                    # Create a mock uploaded file object
                    class MockUploadedFile:
                        def __init__(self, name, content):
                            self.name = name
                            self._content = content
                        
                        def getvalue(self):
                            return self._content
                    
                    mock_file = MockUploadedFile(pdf_file.name, file_content)
                    
                    # Process PDF
                    result = self.pdf_processor.process_pdf(
                        mock_file, 
                        kb_id, 
                        pdf_file.stem
                    )
                    
                    if result['success']:
                        # Add to database
                        doc_id = self.kb_manager.add_document(
                            kb_id,
                            result['title'],
                            result['file_path'],
                            result['content_type'],
                            result['file_size'],
                            result['metadata']
                        )
                        
                        # Mark as processed
                        self.kb_manager.update_document_status(doc_id, True, 'completed')
                        processed_count += 1
                        
                        st.write(f"✅ Обработан: {pdf_file.name}")
                    else:
                        st.error(f"❌ Ошибка обработки {pdf_file.name}: {result['error']}")
                
                except Exception as e:
                    st.error(f"❌ Ошибка обработки {pdf_file.name}: {e}")
                
                # Update progress
                progress_bar.progress((i + 1) / len(pdf_files))
            
            st.success(f"База знаний создана! Обработано {processed_count} из {len(pdf_files)} файлов")
            st.rerun()
            
        except Exception as e:
            st.error(f"Ошибка создания БЗ: {e}")
    
    def _create_steccom_docs_kb(self, pdf_files: List[Path]):
        """Create STECCOM documentation KB"""
        try:
            kb_id = self.kb_manager.create_knowledge_base(
                name="Документация СТЭККОМ",
                description="Полная документация оператора спутниковой связи СТЭККОМ",
                category="Технические регламенты",
                created_by=st.session_state.get('username', 'admin')
            )
            
            st.success(f"База знаний 'Документация СТЭККОМ' создана с ID: {kb_id}")
            
            # Process files with better titles
            title_mapping = {
                'reg_07032015.pdf': 'Регламент технических требований (2015)',
                'reg_gpstrack_14042014.pdf': 'Регламент GPS-трекинга (2014)',
                'reg_monitor_16112013.pdf': 'Регламент мониторинга (2013)',
                'reg_sbd_en.pdf': 'SBD Protocol Specification (EN)',
                'reg_sbd.pdf': 'Спецификация протокола SBD'
            }
            
            processed_count = 0
            progress_bar = st.progress(0)
            
            for i, pdf_file in enumerate(pdf_files):
                try:
                    with open(pdf_file, 'rb') as f:
                        file_content = f.read()
                    
                    class MockUploadedFile:
                        def __init__(self, name, content):
                            self.name = name
                            self._content = content
                        
                        def getvalue(self):
                            return self._content
                    
                    mock_file = MockUploadedFile(pdf_file.name, file_content)
                    
                    # Use better title if available
                    title = title_mapping.get(pdf_file.name, pdf_file.stem)
                    
                    result = self.pdf_processor.process_pdf(
                        mock_file, 
                        kb_id, 
                        title
                    )
                    
                    if result['success']:
                        doc_id = self.kb_manager.add_document(
                            kb_id,
                            result['title'],
                            result['file_path'],
                            result['content_type'],
                            result['file_size'],
                            result['metadata']
                        )
                        
                        self.kb_manager.update_document_status(doc_id, True, 'completed')
                        processed_count += 1
                        
                        st.write(f"✅ Обработан: {title}")
                    else:
                        st.error(f"❌ Ошибка: {pdf_file.name}")
                
                except Exception as e:
                    st.error(f"❌ Ошибка: {pdf_file.name} - {e}")
                
                progress_bar.progress((i + 1) / len(pdf_files))
            
            st.success(f"Документация СТЭККОМ готова! Обработано {processed_count} файлов")
            st.rerun()
            
        except Exception as e:
            st.error(f"Ошибка создания БЗ: {e}")
    
    def _create_manual_kb(self, name: str, category: str, description: str, selected_files: List[Path]):
        """Create KB with manually selected files"""
        try:
            kb_id = self.kb_manager.create_knowledge_base(
                name=name,
                description=description,
                category=category,
                created_by=st.session_state.get('username', 'admin')
            )
            
            st.success(f"База знаний '{name}' создана с ID: {kb_id}")
            
            processed_count = 0
            progress_bar = st.progress(0)
            
            for i, pdf_file in enumerate(selected_files):
                try:
                    with open(pdf_file, 'rb') as f:
                        file_content = f.read()
                    
                    class MockUploadedFile:
                        def __init__(self, name, content):
                            self.name = name
                            self._content = content
                        
                        def getvalue(self):
                            return self._content
                    
                    mock_file = MockUploadedFile(pdf_file.name, file_content)
                    
                    result = self.pdf_processor.process_pdf(
                        mock_file, 
                        kb_id, 
                        pdf_file.stem
                    )
                    
                    if result['success']:
                        doc_id = self.kb_manager.add_document(
                            kb_id,
                            result['title'],
                            result['file_path'],
                            result['content_type'],
                            result['file_size'],
                            result['metadata']
                        )
                        
                        self.kb_manager.update_document_status(doc_id, True, 'completed')
                        processed_count += 1
                        
                        st.write(f"✅ Обработан: {pdf_file.name}")
                    else:
                        st.error(f"❌ Ошибка: {pdf_file.name}")
                
                except Exception as e:
                    st.error(f"❌ Ошибка: {pdf_file.name} - {e}")
                
                progress_bar.progress((i + 1) / len(selected_files))
            
            st.success(f"База знаний готова! Обработано {processed_count} файлов")
            st.rerun()
            
        except Exception as e:
            st.error(f"Ошибка создания БЗ: {e}")
