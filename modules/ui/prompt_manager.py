"""
Prompt Management Module
Модуль для управления промптами SQL Assistant и KB Assistant
"""

import streamlit as st
import os
from pathlib import Path
from typing import Dict, Optional
import json

class PromptManager:
    """Менеджер для редактирования и сохранения промптов"""
    
    def __init__(self, prompts_dir: str = "resources/prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Определяем файлы промптов
        self.prompt_files = {
            "SQL Assistant": "sql_prompt.txt",
            "KB Assistant": "rag_prompt.txt",
            "General Assistant": "assistant_prompt.txt"
        }
        
        # Загружаем текущие промпты
        self.current_prompts = self._load_all_prompts()
    
    def _load_all_prompts(self) -> Dict[str, str]:
        """Загружает все промпты из файлов"""
        prompts = {}
        for name, filename in self.prompt_files.items():
            file_path = self.prompts_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        prompts[name] = f.read()
                except Exception as e:
                    st.error(f"Ошибка загрузки промпта {name}: {e}")
                    prompts[name] = ""
            else:
                prompts[name] = ""
        return prompts
    
    def _save_prompt(self, prompt_name: str, content: str) -> bool:
        """Сохраняет промпт в файл"""
        try:
            filename = self.prompt_files[prompt_name]
            file_path = self.prompts_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Обновляем кэш
            self.current_prompts[prompt_name] = content
            return True
        except Exception as e:
            st.error(f"Ошибка сохранения промпта {prompt_name}: {e}")
            return False
    
    def render_prompt_editor(self):
        """Отображает интерфейс редактирования промптов"""
        st.header("📝 Управление промптами")
        st.markdown("Здесь вы можете редактировать промпты для различных ассистентов системы.")
        
        # Выбор промпта для редактирования
        selected_prompt = st.selectbox(
            "Выберите промпт для редактирования:",
            list(self.prompt_files.keys()),
            key="prompt_selector"
        )
        
        if selected_prompt:
            st.markdown(f"### Редактирование промпта: {selected_prompt}")
            
            # Получаем текущий контент
            current_content = self.current_prompts.get(selected_prompt, "")
            
            # Текстовое поле для редактирования
            edited_content = st.text_area(
                "Содержимое промпта:",
                value=current_content,
                height=400,
                key=f"prompt_editor_{selected_prompt}",
                help="Используйте переменные в фигурных скобках: {question}, {context}, {company} и т.д."
            )
            
            # Кнопки управления
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Сохранить", key=f"save_{selected_prompt}"):
                    if self._save_prompt(selected_prompt, edited_content):
                        st.success(f"Промпт '{selected_prompt}' успешно сохранен!")
                        st.rerun()
            
            with col2:
                if st.button("🔄 Сбросить", key=f"reset_{selected_prompt}"):
                    st.rerun()
            
            with col3:
                if st.button("📋 Копировать", key=f"copy_{selected_prompt}"):
                    st.code(edited_content, language="text")
            
            # Информация о промпте
            st.markdown("---")
            st.markdown("#### 📋 Информация о промпте")
            
            if selected_prompt == "SQL Assistant":
                st.info("""
                **SQL Assistant** - генерирует SQL запросы из естественного языка.
                
                **Доступные переменные:**
                - `{question}` - вопрос пользователя
                - `{company}` - название компании (если указано)
                - `{schema}` - схема базы данных
                
                **Особенности:**
                - Оптимизирован для SQLite
                - Включает правила для спутниковой связи
                - Поддерживает фильтрацию по компаниям
                """)
            
            elif selected_prompt == "KB Assistant":
                st.info("""
                **KB Assistant** - отвечает на вопросы на основе баз знаний.
                
                **Доступные переменные:**
                - `{question}` - вопрос пользователя
                - `{context}` - контекст из базы знаний
                
                **Особенности:**
                - Анализирует контекст из RAG системы
                - Отвечает только на русском языке
                - Использует информацию из баз знаний
                """)
            
            elif selected_prompt == "General Assistant":
                st.info("""
                **General Assistant** - общий ассистент для помощи пользователям.
                
                **Доступные переменные:**
                - `{question}` - вопрос пользователя
                - `{context}` - контекст
                - `{role}` - роль пользователя
                
                **Особенности:**
                - Помогает с навигацией по системе
                - Предоставляет инструкции
                - Поддерживает различные роли пользователей
                """)
            
            # Статистика
            st.markdown("#### 📊 Статистика")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Символов", len(edited_content))
            
            with col2:
                st.metric("Строк", len(edited_content.split('\n')))
            
            with col3:
                st.metric("Слов", len(edited_content.split()))
    
    def get_prompt_content(self, prompt_name: str) -> str:
        """Возвращает содержимое промпта"""
        return self.current_prompts.get(prompt_name, "")
    
    def reload_prompts(self):
        """Перезагружает промпты из файлов"""
        self.current_prompts = self._load_all_prompts()
