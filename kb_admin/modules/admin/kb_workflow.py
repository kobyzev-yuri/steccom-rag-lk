"""
Knowledge Base Workflow Guide
Алгоритм работы с базами знаний
"""

import streamlit as st
from typing import List, Dict

class KBWorkflow:
    def __init__(self):
        self.workflow_steps = {
            "create": {
                "title": "📚 Создание базы знаний",
                "steps": [
                    "1. Выберите раздел '🤖 Ассистент создания БЗ'",
                    "2. Проверьте найденные PDF файлы в директории uploads/",
                    "3. Выберите способ создания:",
                    "   • Быстрое создание (все файлы)",
                    "   • Ручное создание (выбор файлов)",
                    "4. Укажите название, категорию и описание БЗ",
                    "5. Нажмите кнопку создания",
                    "6. Дождитесь обработки всех файлов"
                ],
                "result": "База знаний создана и документы проиндексированы"
            },
            "load": {
                "title": "🔄 Загрузка базы знаний в RAG",
                "steps": [
                    "1. Перейдите в '🔍 Поиск и тестирование'",
                    "2. Нажмите '🔄 Загрузить все базы знаний'",
                    "3. Дождитесь сообщения об успешной загрузке",
                    "4. Проверьте статистику загруженных БЗ"
                ],
                "result": "База знаний доступна для поиска"
            },
            "test": {
                "title": "🧪 Тестирование поиска",
                "steps": [
                    "1. В разделе '🔍 Поиск и тестирование'",
                    "2. Выберите базы знаний для поиска",
                    "3. Введите тестовый запрос на русском языке",
                    "4. Нажмите '🔍 Найти'",
                    "5. Проверьте найденные документы",
                    "6. Протестируйте ответ ИИ"
                ],
                "result": "Поиск работает корректно"
            },
            "stop": {
                "title": "⏹️ Остановка RAG системы",
                "steps": [
                    "1. В разделе '⚙️ Настройки'",
                    "2. Нажмите '🔄 Перезагрузить RAG систему'",
                    "3. Или перезапустите приложение Streamlit"
                ],
                "result": "RAG система очищена из памяти"
            },
            "recreate": {
                "title": "🔄 Пересоздание базы знаний",
                "steps": [
                    "1. В разделе '📚 Управление БЗ'",
                    "2. Найдите нужную базу знаний",
                    "3. Нажмите '🗑️ Удалить' (мягкое удаление)",
                    "4. Создайте новую БЗ через ассистента",
                    "5. Загрузите в RAG систему",
                    "6. Протестируйте работу"
                ],
                "result": "База знаний пересоздана"
            },
            "troubleshoot": {
                "title": "🔧 Устранение проблем",
                "steps": [
                    "1. Проверьте статус в '📊 Обзор'",
                    "2. Убедитесь, что документы обработаны (processed = 1)",
                    "3. Проверьте наличие файлов в data/uploads/",
                    "4. Перезагрузите RAG систему",
                    "5. Проверьте логи Ollama моделей",
                    "6. При необходимости пересоздайте БЗ"
                ],
                "result": "Проблемы устранены"
            }
        }
    
    def render_workflow_guide(self):
        """Render complete workflow guide"""
        st.header("📋 Алгоритм работы с базами знаний")
        
        # Workflow selection
        workflow_type = st.selectbox(
            "Выберите операцию:",
            [
                "📚 Создание базы знаний",
                "🔄 Загрузка базы знаний в RAG", 
                "🧪 Тестирование поиска",
                "⏹️ Остановка RAG системы",
                "🔄 Пересоздание базы знаний",
                "🔧 Устранение проблем"
            ]
        )
        
        # Get workflow key
        workflow_key = None
        for key, value in self.workflow_steps.items():
            if value["title"] == workflow_type:
                workflow_key = key
                break
        
        if workflow_key:
            self._render_workflow_steps(workflow_key)
        
        # Quick actions
        st.subheader("⚡ Быстрые действия")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Полный цикл создания БЗ", type="primary"):
                self._render_full_cycle()
        
        with col2:
            if st.button("🔍 Диагностика системы"):
                self._render_diagnostics()
        
        with col3:
            if st.button("📊 Статус всех БЗ"):
                self._render_status_check()
    
    def _render_workflow_steps(self, workflow_key: str):
        """Render specific workflow steps"""
        workflow = self.workflow_steps[workflow_key]
        
        st.subheader(workflow["title"])
        
        # Steps
        st.markdown("**Пошаговый алгоритм:**")
        for step in workflow["steps"]:
            st.markdown(f"• {step}")
        
        # Result
        st.success(f"**Результат:** {workflow['result']}")
        
        # Additional tips
        if workflow_key == "create":
            st.info("""
            **💡 Советы:**
            - Используйте понятные названия БЗ
            - Выбирайте правильную категорию
            - Проверяйте размер файлов (рекомендуется до 50MB)
            - Дождитесь полной обработки всех файлов
            """)
        
        elif workflow_key == "load":
            st.info("""
            **💡 Советы:**
            - Загрузка может занять время при большом количестве документов
            - Проверьте, что Ollama модели запущены
            - При ошибках перезапустите RAG систему
            """)
        
        elif workflow_key == "test":
            st.info("""
            **💡 Советы:**
            - Используйте конкретные запросы на русском языке
            - Тестируйте разные типы вопросов
            - Проверяйте релевантность найденных документов
            """)
    
    def _render_full_cycle(self):
        """Render full KB creation cycle"""
        st.subheader("🚀 Полный цикл создания и тестирования БЗ")
        
        st.markdown("""
        **1. Подготовка файлов**
        - Поместите PDF файлы в директорию `data/uploads/`
        - Убедитесь, что файлы не повреждены
        
        **2. Создание БЗ**
        - Перейдите в "🤖 Ассистент создания БЗ"
        - Выберите "🚀 Создать БЗ 'Технические регламенты'"
        - Дождитесь обработки всех файлов
        
        **3. Загрузка в RAG**
        - Перейдите в "🔍 Поиск и тестирование"
        - Нажмите "🔄 Загрузить все базы знаний"
        - Проверьте статистику загрузки
        
        **4. Тестирование**
        - Введите тестовый запрос
        - Проверьте найденные документы
        - Протестируйте ответ ИИ
        
        **5. Проверка работы**
        - Убедитесь, что поиск работает корректно
        - Протестируйте разные типы запросов
        """)
    
    def _render_diagnostics(self):
        """Render system diagnostics"""
        st.subheader("🔍 Диагностика системы")
        
        # Check database
        try:
            import sqlite3
            conn = sqlite3.connect('kbs.db')
            c = conn.cursor()
            
            # KB count
            c.execute("SELECT COUNT(*) FROM knowledge_bases WHERE is_active = 1")
            kb_count = c.fetchone()[0]
            
            # Document count
            c.execute("SELECT COUNT(*) FROM knowledge_documents WHERE processed = 1")
            doc_count = c.fetchone()[0]
            
            # File count
            import os
            upload_dir = "data/uploads"
            file_count = len([f for f in os.listdir(upload_dir) if f.endswith('.pdf')]) if os.path.exists(upload_dir) else 0
            
            conn.close()
            
            st.markdown("**Статус системы:**")
            st.write(f"• Базы знаний в БД: {kb_count}")
            st.write(f"• Обработанных документов: {doc_count}")
            st.write(f"• PDF файлов в uploads/: {file_count}")
            
            if kb_count > 0 and doc_count > 0:
                st.success("✅ Система готова к работе")
            else:
                st.warning("⚠️ Требуется создание БЗ")
                
        except Exception as e:
            st.error(f"❌ Ошибка диагностики: {e}")
    
    def _render_status_check(self):
        """Render status of all KBs"""
        st.subheader("📊 Статус всех баз знаний")
        
        try:
            import sqlite3
            conn = sqlite3.connect('kbs.db')
            c = conn.cursor()
            
            c.execute("""
                SELECT kb.id, kb.name, kb.category, kb.created_at,
                       COUNT(kd.id) as doc_count,
                       SUM(CASE WHEN kd.processed = 1 THEN 1 ELSE 0 END) as processed_count
                FROM knowledge_bases kb
                LEFT JOIN knowledge_documents kd ON kb.id = kd.kb_id
                WHERE kb.is_active = 1
                GROUP BY kb.id
                ORDER BY kb.created_at DESC
            """)
            
            results = c.fetchall()
            conn.close()
            
            if results:
                for row in results:
                    kb_id, name, category, created_at, doc_count, processed_count = row
                    
                    with st.expander(f"📚 {name} (ID: {kb_id})"):
                        st.write(f"**Категория:** {category}")
                        st.write(f"**Создано:** {created_at}")
                        st.write(f"**Документов:** {doc_count}")
                        st.write(f"**Обработано:** {processed_count}")
                        
                        if processed_count == doc_count and doc_count > 0:
                            st.success("✅ Готова к использованию")
                        elif processed_count > 0:
                            st.warning("⚠️ Частично обработана")
                        else:
                            st.error("❌ Не обработана")
            else:
                st.info("Нет созданных баз знаний")
                
        except Exception as e:
            st.error(f"❌ Ошибка проверки статуса: {e}")
