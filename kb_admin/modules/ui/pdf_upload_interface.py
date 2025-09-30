"""
PDF Upload Interface for KB Admin
Интерфейс загрузки и обработки PDF документов
"""

import streamlit as st
import os
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

class PDFUploadInterface:
    """Интерфейс загрузки и обработки PDF документов"""
    
    def __init__(self, kb_manager, pdf_processor):
        self.kb_manager = kb_manager
        self.pdf_processor = pdf_processor
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def render_upload_interface(self):
        """Рендер основного интерфейса загрузки"""
        st.header("📄 Загрузка и обработка PDF документов")
        
        # Показываем существующие файлы
        self._render_existing_files()
        
        # Загрузка новых файлов
        self._render_file_upload()
        
        # Обработка файлов
        self._render_file_processing()
    
    def _render_existing_files(self):
        """Показ существующих файлов"""
        st.subheader("📋 Существующие PDF файлы")
        
        pdf_files = list(self.upload_dir.glob("*.pdf"))
        
        if pdf_files:
            st.success(f"Найдено {len(pdf_files)} PDF файлов")
            
            # Создаем таблицу с файлами
            file_data = []
            for pdf_file in pdf_files:
                file_size = pdf_file.stat().st_size / 1024  # KB
                file_data.append({
                    "Файл": pdf_file.name,
                    "Размер (KB)": f"{file_size:.1f}",
                    "Путь": str(pdf_file)
                })
            
            df = pd.DataFrame(file_data)
            st.dataframe(df, use_container_width=True)
            
            # Показываем детали файлов
            with st.expander("📄 Детали файлов"):
                for pdf_file in pdf_files:
                    st.write(f"**{pdf_file.name}**")
                    
                    # Показываем превью текста
                    try:
                        text = self.pdf_processor.extract_text(str(pdf_file))
                        if text:
                            preview = text[:300] + "..." if len(text) > 300 else text
                            st.text_area(f"Превью {pdf_file.name}:", preview, height=100, key=f"preview_{pdf_file.name}")
                        else:
                            st.warning("Не удалось извлечь текст")
                    except Exception as e:
                        st.error(f"Ошибка извлечения текста: {e}")
                    
                    st.markdown("---")
        else:
            st.info("В директории uploads нет PDF файлов")
    
    def _render_file_upload(self):
        """Интерфейс загрузки файлов"""
        st.subheader("📤 Загрузка новых PDF файлов")
        
        uploaded_files = st.file_uploader(
            "Выберите PDF файлы для загрузки",
            type=['pdf'],
            accept_multiple_files=True,
            help="Можно выбрать несколько PDF файлов одновременно"
        )
        
        if uploaded_files:
            st.success(f"Выбрано {len(uploaded_files)} файлов")
            
            # Показываем информацию о файлах
            with st.expander("📋 Информация о выбранных файлах"):
                for file in uploaded_files:
                    file_size = len(file.getvalue()) / 1024
                    st.write(f"• **{file.name}** ({file_size:.1f} KB)")
            
            # Кнопка загрузки
            if st.button("💾 Загрузить файлы", type="primary"):
                self._upload_files(uploaded_files)
    
    def _upload_files(self, uploaded_files):
        """Загрузка файлов на сервер"""
        uploaded_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Загрузка: {uploaded_file.name}")
                
                # Сохраняем файл
                file_path = self.upload_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                uploaded_count += 1
                st.success(f"✅ Загружен: {uploaded_file.name}")
                
            except Exception as e:
                st.error(f"❌ Ошибка загрузки {uploaded_file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("")
        st.success(f"🎉 Загрузка завершена! Успешно загружено {uploaded_count} из {len(uploaded_files)} файлов")
        
        # Обновляем страницу
        st.rerun()
    
    def _render_file_processing(self):
        """Интерфейс обработки файлов"""
        st.subheader("⚙️ Обработка файлов в базу знаний")
        
        # Получаем список существующих БЗ
        kbs = self.kb_manager.get_knowledge_bases()
        
        if not kbs:
            st.warning("Нет созданных баз знаний. Сначала создайте БЗ в разделе 'Создание новой БЗ'")
            return
        
        # Выбор БЗ
        kb_options = {f"{kb['name']} ({kb['category']})": kb['id'] for kb in kbs}
        selected_kb_name = st.selectbox("Выберите базу знаний:", list(kb_options.keys()))
        selected_kb_id = kb_options[selected_kb_name]
        
        # Показываем информацию о выбранной БЗ
        selected_kb = next(kb for kb in kbs if kb['id'] == selected_kb_id)
        st.info(f"**База знаний:** {selected_kb['name']} | **Категория:** {selected_kb['category']}")
        
        # Получаем список файлов для обработки
        pdf_files = list(self.upload_dir.glob("*.pdf"))
        
        if not pdf_files:
            st.warning("Нет PDF файлов для обработки")
            return
        
        # Выбор файлов для обработки
        st.write("**Выберите файлы для обработки:**")
        
        selected_files = []
        for pdf_file in pdf_files:
            # Проверяем, не обработан ли уже файл
            docs = self.kb_manager.get_documents(selected_kb_id)
            already_processed = any(doc['title'] == pdf_file.name for doc in docs)
            
            if already_processed:
                st.write(f"✅ {pdf_file.name} (уже обработан)")
            else:
                if st.checkbox(f"📄 {pdf_file.name}", key=f"process_{pdf_file.name}"):
                    selected_files.append(pdf_file)
        
        if selected_files:
            st.success(f"Выбрано {len(selected_files)} файлов для обработки")
            
            # Кнопка обработки
            if st.button("🚀 Обработать выбранные файлы", type="primary"):
                self._process_files(selected_files, selected_kb_id)
    
    def _process_files(self, pdf_files: List[Path], kb_id: int):
        """Обработка выбранных файлов"""
        processed_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                status_text.text(f"Обработка: {pdf_file.name}")
                
                # Читаем файл
                with open(pdf_file, 'rb') as f:
                    file_content = f.read()
                
                # Создаем mock объект для PDFProcessor
                class MockUploadedFile:
                    def __init__(self, name, content):
                        self.name = name
                        self._content = content
                    
                    def getvalue(self):
                        return self._content
                
                mock_file = MockUploadedFile(pdf_file.name, file_content)
                
                # Обрабатываем PDF
                result = self.pdf_processor.process_pdf(
                    mock_file, 
                    kb_id, 
                    pdf_file.stem
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
                    
                    st.success(f"✅ Обработан: {pdf_file.name}")
                else:
                    st.error(f"❌ Ошибка: {pdf_file.name} - {result.get('error', 'Неизвестная ошибка')}")
                
            except Exception as e:
                st.error(f"❌ Ошибка: {pdf_file.name} - {e}")
            
            progress_bar.progress((i + 1) / len(pdf_files))
        
        status_text.text("")
        st.success(f"🎉 Обработка завершена! Успешно обработано {processed_count} из {len(pdf_files)} файлов")
        
        # Обновляем страницу
        st.rerun()
    
    def render_simple_kb_creation(self):
        """Простое создание БЗ из всех файлов"""
        st.header("🤖 Быстрое создание базы знаний")
        st.info("Создайте новую базу знаний из всех доступных PDF файлов")
        
        # Получаем список файлов
        pdf_files = list(self.upload_dir.glob("*.pdf"))
        
        if not pdf_files:
            st.warning("В директории uploads нет PDF файлов")
            st.info("Загрузите PDF файлы через интерфейс 'Загрузка документов'")
            return
        
        st.success(f"Найдено {len(pdf_files)} PDF файлов")
        
        # Показываем файлы
        with st.expander("📋 Файлы для обработки"):
            for pdf_file in pdf_files:
                file_size = pdf_file.stat().st_size / 1024
                st.write(f"• **{pdf_file.name}** ({file_size:.1f} KB)")
        
        # Форма создания БЗ
        with st.form("create_kb_form"):
            st.subheader("📚 Создание новой базы знаний")
            
            kb_name = st.text_input(
                "Название базы знаний:",
                value="Новая база знаний",
                help="Уникальное название для базы знаний"
            )
            
            kb_category = st.selectbox(
                "Категория:",
                [
                    "Технические регламенты",
                    "Лицензии и разрешения",
                    "Документация",
                    "Руководства",
                    "Другое"
                ]
            )
            
            kb_description = st.text_area(
                "Описание:",
                value=f"База знаний, созданная из {len(pdf_files)} PDF файлов",
                help="Описание содержимого базы знаний"
            )
            
            submitted = st.form_submit_button("🚀 Создать базу знаний", type="primary")
            
            if submitted:
                if not kb_name.strip():
                    st.error("Введите название базы знаний")
                else:
                    self._create_kb_with_files(kb_name, pdf_files, kb_category, kb_description)
    
    def _create_kb_with_files(self, name: str, pdf_files: List[Path], 
                             category: str = "Технические регламенты", 
                             description: str = None):
        """Создание БЗ с файлами"""
        try:
            # Создаем БЗ
            kb_id = self.kb_manager.create_knowledge_base(
                name=name,
                description=description or f"База знаний: {name}",
                category=category,
                created_by=st.session_state.get('username', 'admin')
            )
            
            st.success(f"База знаний '{name}' создана с ID: {kb_id}")
            
            # Обрабатываем файлы
            processed_count = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, pdf_file in enumerate(pdf_files):
                try:
                    status_text.text(f"Обработка: {pdf_file.name}")
                    
                    # Читаем файл
                    with open(pdf_file, 'rb') as f:
                        file_content = f.read()
                    
                    # Создаем mock объект
                    class MockUploadedFile:
                        def __init__(self, name, content):
                            self.name = name
                            self._content = content
                        
                        def getvalue(self):
                            return self._content
                    
                    mock_file = MockUploadedFile(pdf_file.name, file_content)
                    
                    # Обрабатываем PDF
                    result = self.pdf_processor.process_pdf(
                        mock_file, 
                        kb_id, 
                        pdf_file.stem
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
                        
                        # Обновляем статус
                        self.kb_manager.update_document_status(doc_id, True, 'completed')
                        processed_count += 1
                        
                        st.write(f"✅ Обработан: {pdf_file.name}")
                    else:
                        st.error(f"❌ Ошибка: {pdf_file.name}")
                
                except Exception as e:
                    st.error(f"❌ Ошибка: {pdf_file.name} - {e}")
                
                progress_bar.progress((i + 1) / len(pdf_files))
            
            status_text.text("")
            st.success(f"🎉 База знаний готова! Обработано {processed_count} из {len(pdf_files)} файлов")
            
            # Обновляем страницу
            st.rerun()
            
        except Exception as e:
            st.error(f"Ошибка создания базы знаний: {e}")






