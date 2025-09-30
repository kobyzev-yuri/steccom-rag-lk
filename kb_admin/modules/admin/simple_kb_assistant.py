"""
Simple Knowledge Base Assistant
Простой ассистент для создания баз знаний
"""

import streamlit as st
import os
from pathlib import Path
from typing import List

class SimpleKBAssistant:
    def __init__(self, kb_manager, pdf_processor):
        self.kb_manager = kb_manager
        self.pdf_processor = pdf_processor
    
    def render_assistant(self):
        """Render simple KB creation assistant"""
        st.header("🤖 Ассистент создания базы знаний")
        
        # Показываем информацию о недавно созданной БЗ
        if st.session_state.get('kb_created', False):
            st.success(f"✅ База знаний '{st.session_state.get('created_kb_name', '')}' успешно создана!")
            st.info(f"ID базы знаний: {st.session_state.get('created_kb_id', '')}")
            
            # Кнопки для навигации
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Перейти к загрузке документов", type="primary"):
                    st.session_state.current_page = "📄 Загрузка документов"
                    st.rerun()
            with col2:
                if st.button("🔄 Создать новую БЗ"):
                    # Сбрасываем состояние
                    st.session_state.kb_created = False
                    st.session_state.created_kb_name = None
                    st.session_state.created_kb_id = None
                    st.rerun()
            
            st.markdown("---")
        
        # Показываем информацию о добавлении документов в существующую БЗ
        if st.session_state.get('kb_updated', False):
            st.success(f"✅ Добавлено {st.session_state.get('added_documents_count', 0)} документов в БЗ!")
            st.info(f"ID обновленной БЗ: {st.session_state.get('updated_kb_id', '')}")
            
            # Кнопки для навигации
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Перейти к загрузке документов", type="primary"):
                    st.session_state.current_page = "📄 Загрузка документов"
                    st.rerun()
            with col2:
                if st.button("🔄 Добавить еще документы"):
                    # Сбрасываем состояние
                    st.session_state.kb_updated = False
                    st.session_state.updated_kb_id = None
                    st.session_state.added_documents_count = None
                    st.rerun()
            
            st.markdown("---")
        
        # Check for existing files
        upload_dir = Path("data/uploads")
        if not upload_dir.exists():
            st.error("Директория uploads не найдена")
            return
        
        pdf_files = list(upload_dir.glob("*.pdf"))
        
        if not pdf_files:
            st.warning("В директории uploads не найдено PDF файлов")
            st.info("Загрузите PDF файлы через интерфейс 'Загрузка документов'")
            return
        
        st.success(f"Найдено {len(pdf_files)} PDF файлов")
        
        # Show files
        with st.expander("📋 Найденные файлы"):
            for pdf_file in pdf_files:
                file_size = pdf_file.stat().st_size / 1024
                st.write(f"• **{pdf_file.name}** ({file_size:.1f} KB)")
        
        # Check existing KBs
        existing_kbs = self.kb_manager.get_knowledge_bases()
        
        if existing_kbs:
            st.subheader("📚 Существующие базы знаний")
            for kb in existing_kbs:
                docs = self.kb_manager.get_documents(kb['id'])
                st.write(f"• **{kb['name']}** ({kb['category']}) - {len(docs)} документов")
            
            # Test existing KB
            st.subheader("🔍 Тестирование существующей БЗ")
            if st.button("🧪 Протестировать поиск в существующей БЗ", type="secondary"):
                st.info("Перейдите в раздел '🔍 Поиск и тестирование' для тестирования поиска")
                st.markdown("**Следующие шаги:**")
                st.markdown("1. Перейдите в '🔍 Поиск и тестирование'")
                st.markdown("2. Нажмите '🔄 Загрузить все базы знаний'")
                st.markdown("3. Введите тестовый запрос, например: 'технические требования к спутниковой связи'")
                st.markdown("4. Нажмите '🔍 Найти'")
        
        # Quick creation options
        st.subheader("⚡ Быстрое создание БЗ")
        
        # Показываем опции только если есть файлы
        if pdf_files:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                kb_name = "Технические регламенты v2" if any(kb['name'] == "Технические регламенты" for kb in existing_kbs) else "Технические регламенты"
                if st.button(f"🚀 Создать БЗ '{kb_name}'", type="primary"):
                    self._create_kb_with_files(kb_name, pdf_files, "Технические регламенты")
            
            with col2:
                kb_name = "Документация СТЭККОМ v2" if any(kb['name'] == "Документация СТЭККОМ" for kb in existing_kbs) else "Документация СТЭККОМ"
                if st.button(f"📚 Создать БЗ '{kb_name}'"):
                    self._create_kb_with_files(kb_name, pdf_files, "Пользовательские инструкции")
            
            with col3:
                kb_name = "Лицензии и разрешения v2" if any(kb['name'] == "Лицензии и разрешения" for kb in existing_kbs) else "Лицензии и разрешения"
                if st.button(f"📜 Создать БЗ '{kb_name}'"):
                    self._create_kb_with_files(kb_name, pdf_files, "Лицензии и разрешения", "База знаний с лицензиями и разрешениями СТЭККОМ")
        
        # Опция добавления в существующую БЗ
        if existing_kbs and pdf_files:
            st.subheader("📚 Добавить в существующую БЗ")
            
            kb_options = {f"{kb['name']} ({kb['category']})": kb['id'] for kb in existing_kbs}
            selected_kb_name = st.selectbox("Выберите базу знаний:", list(kb_options.keys()))
            
            if st.button("📄 Добавить документы в выбранную БЗ", type="secondary"):
                selected_kb_id = kb_options[selected_kb_name]
                self._add_files_to_existing_kb(selected_kb_id, pdf_files)
        
        # Manual creation
        st.subheader("🔧 Ручное создание")
        
        with st.form("manual_kb"):
            kb_name = st.text_input("Название БЗ", value="Технические регламенты")
            kb_category = st.selectbox(
                "Категория",
                ["Технические регламенты", "Пользовательские инструкции", 
                 "Лицензии и разрешения", "Политики безопасности", "Процедуры биллинга", "Другое"]
            )
            kb_description = st.text_area(
                "Описание", 
                value="База знаний с техническими регламентами СТЭККОМ"
            )
            
            submitted = st.form_submit_button("Создать БЗ")
            
            if submitted:
                self._create_kb_with_files(kb_name, pdf_files, kb_category, kb_description)
    
    def _add_files_to_existing_kb(self, kb_id: int, pdf_files: List[Path]):
        """Добавить файлы в существующую БЗ"""
        try:
            st.info(f"Добавляем {len(pdf_files)} документов в БЗ...")
            
            processed_count = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, pdf_file in enumerate(pdf_files):
                try:
                    status_text.text(f"Обработка: {pdf_file.name}")
                    
                    # Read file
                    with open(pdf_file, 'rb') as f:
                        file_content = f.read()
                    
                    # Create mock uploaded file
                    class MockFile:
                        def __init__(self, name, content):
                            self.name = name
                            self._content = content
                        
                        def getvalue(self):
                            return self._content
                    
                    mock_file = MockFile(pdf_file.name, file_content)
                    
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
                            pdf_file.stem,
                            result['text_content'],
                            str(pdf_file),
                            result.get('extraction_method', 'unknown')
                        )
                        processed_count += 1
                        st.success(f"✅ {pdf_file.name} добавлен в БЗ")
                    else:
                        st.error(f"❌ Ошибка обработки {pdf_file.name}: {result.get('error', 'Неизвестная ошибка')}")
                    
                    progress_bar.progress((i + 1) / len(pdf_files))
                    
                except Exception as e:
                    st.error(f"❌ Ошибка обработки {pdf_file.name}: {e}")
                    progress_bar.progress((i + 1) / len(pdf_files))
            
            # Сохраняем состояние
            st.session_state.kb_updated = True
            st.session_state.updated_kb_id = kb_id
            st.session_state.added_documents_count = processed_count
            
            st.success(f"🎉 Добавлено {processed_count} из {len(pdf_files)} документов в БЗ!")
            
            # Кнопки для навигации
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Перейти к загрузке документов", type="primary"):
                    st.session_state.current_page = "📄 Загрузка документов"
                    st.rerun()
            with col2:
                if st.button("🔄 Добавить еще документы"):
                    # Сбрасываем состояние
                    st.session_state.kb_updated = False
                    st.session_state.updated_kb_id = None
                    st.session_state.added_documents_count = None
                    st.rerun()
            
        except Exception as e:
            st.error(f"Критическая ошибка: {e}")
    
    def _create_kb_with_files(self, name: str, pdf_files: List[Path], 
                             category: str = "Технические регламенты", 
                             description: str = None):
        """Create KB with all PDF files"""
        try:
            # Create KB
            kb_id = self.kb_manager.create_knowledge_base(
                name=name,
                description=description or f"База знаний: {name}",
                category=category,
                created_by=st.session_state.get('username', 'admin')
            )
            
            st.success(f"База знаний '{name}' создана с ID: {kb_id}")
            
            # Сохраняем состояние для предотвращения сброса навигации
            st.session_state.kb_created = True
            st.session_state.created_kb_name = name
            st.session_state.created_kb_id = kb_id
            
            # Process files
            processed_count = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, pdf_file in enumerate(pdf_files):
                try:
                    status_text.text(f"Обработка: {pdf_file.name}")
                    
                    # Read file
                    with open(pdf_file, 'rb') as f:
                        file_content = f.read()
                    
                    # Create mock uploaded file
                    class MockFile:
                        def __init__(self, name, content):
                            self.name = name
                            self._content = content
                        
                        def getvalue(self):
                            return self._content
                    
                    mock_file = MockFile(pdf_file.name, file_content)
                    
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
                        
                        st.write(f"✅ {pdf_file.name}")
                    else:
                        st.error(f"❌ {pdf_file.name}: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"❌ {pdf_file.name}: {e}")
                
                # Update progress
                progress_bar.progress((i + 1) / len(pdf_files))
            
            status_text.text("Готово!")
            st.success(f"База знаний готова! Обработано {processed_count} из {len(pdf_files)} файлов")
            
            # Show next steps
            st.info("""
            **Следующие шаги:**
            1. Перейдите в "🔍 Поиск и тестирование"
            2. Нажмите "🔄 Загрузить все базы знаний"
            3. Протестируйте поиск по документам
            """)
            
        except Exception as e:
            st.error(f"Ошибка создания БЗ: {e}")
