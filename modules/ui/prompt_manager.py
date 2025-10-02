"""
Prompt Manager for AI Billing System
Управление промптами для различных ассистентов
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, Optional


class PromptManager:
    """Менеджер промптов для различных ассистентов"""
    
    def __init__(self):
        self.prompts_dir = Path("resources/prompts")
        self.prompts_file = self.prompts_dir / "prompts.json"
        self.default_prompts = self._get_default_prompts()
        self._ensure_prompts_file()
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """Получить промпты по умолчанию"""
        return {
            "sql_assistant": """Ты — SQL ассистент для системы биллинга спутниковой связи СТЭККОМ.

ЗАДАЧА: Создай SQL запрос на основе вопроса пользователя.

ПРАВИЛА:
1) Отвечай ТОЛЬКО SQL запросом без объяснений
2) Используй таблицы: users, contracts, devices, usage, sessions
3) Для фильтрации по компании используй параметр ?
4) Сортируй результаты по дате (DESC)
5) Ограничивай результаты LIMIT 100

ВОПРОС: {question}

SQL:""",
            
            "rag_assistant": """Ты — ассистент биллинга. Отвечай строго ПО КОНТЕКСТУ из базы знаний.

КОНТЕКСТ:
{context}

ВОПРОС: {question}

ПРАВИЛА ОТВЕТА (ОБЯЗАТЕЛЬНЫ):
1) ТОЛЬКО на русском языке.
2) Используй ТОЛЬКО сведения из контекста: формулировки, пункты, правила.
3) Если в контексте есть релевантная информация, используй её для ответа, даже если она не полная.
4) Если в контексте НЕТ достаточной информации для полного ответа, но есть частичная информация, ответь на основе имеющихся данных и укажи, что для полного ответа нужна дополнительная информация.
5) Только если в контексте вообще НЕТ релевантной информации, ответь: "Недостаточно данных в БЗ для точного ответа".
6) Для расчётных вопросов дай краткую формулу/шаги строго по тексту БЗ.
7) Не придумывай факты вне контекста.

ОТВЕТ (кратко, по делу):""",
            
            "general_assistant": """Ты — помощник по системе спутниковой связи СТЭККОМ.

Помогай пользователям с вопросами по:
- Биллингу и тарифам
- Техническим вопросам
- Документации
- Процедурам

Отвечай кратко и по делу на русском языке."""
        }
    
    def _ensure_prompts_file(self):
        """Создать файл с промптами если его нет"""
        if not self.prompts_file.exists():
            self.prompts_dir.mkdir(parents=True, exist_ok=True)
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.default_prompts, f, ensure_ascii=False, indent=2)
    
    def load_prompts(self) -> Dict[str, str]:
        """Загрузить промпты из файла"""
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Ошибка загрузки промптов: {e}")
            return self.default_prompts
    
    def save_prompts(self, prompts: Dict[str, str]):
        """Сохранить промпты в файл"""
        try:
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2)
            st.success("Промпты сохранены!")
        except Exception as e:
            st.error(f"Ошибка сохранения промптов: {e}")
    
    def get_prompt(self, assistant_type: str) -> str:
        """Получить промпт для конкретного ассистента"""
        prompts = self.load_prompts()
        return prompts.get(assistant_type, self.default_prompts.get(assistant_type, ""))
    
    def render_prompt_editor(self):
        """Отобразить интерфейс редактирования промптов"""
        st.subheader("📝 Управление промптами")
        
        # Загрузить текущие промпты
        prompts = self.load_prompts()
        
        # Выбор ассистента
        assistant_type = st.selectbox(
            "Выберите ассистента:",
            options=list(prompts.keys()),
            format_func=lambda x: {
                "sql_assistant": "🧮 SQL Assistant",
                "rag_assistant": "🤖 RAG Assistant", 
                "general_assistant": "💬 General Assistant"
            }.get(x, x)
        )
        
        # Редактор промпта
        current_prompt = prompts.get(assistant_type, "")
        
        st.markdown("**Текущий промпт:**")
        edited_prompt = st.text_area(
            "Промпт:",
            value=current_prompt,
            height=300,
            key=f"prompt_editor_{assistant_type}"
        )
        
        # Кнопки управления
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Сохранить", key=f"save_{assistant_type}"):
                prompts[assistant_type] = edited_prompt
                self.save_prompts(prompts)
                st.rerun()
        
        with col2:
            if st.button("🔄 Сбросить", key=f"reset_{assistant_type}"):
                prompts[assistant_type] = self.default_prompts[assistant_type]
                self.save_prompts(prompts)
                st.rerun()
        
        with col3:
            if st.button("📋 Копировать", key=f"copy_{assistant_type}"):
                st.code(edited_prompt, language="text")
        
        with col4:
            if st.button("📖 Предпросмотр", key=f"preview_{assistant_type}"):
                st.markdown("**Предпросмотр промпта:**")
                st.markdown(f"```\n{edited_prompt}\n```")
        
        # Информация о переменных
        st.markdown("---")
        st.markdown("**📚 Доступные переменные:**")
        
        if assistant_type == "sql_assistant":
            st.markdown("""
            - `{question}` - вопрос пользователя
            - `{company}` - компания пользователя (опционально)
            """)
        elif assistant_type == "rag_assistant":
            st.markdown("""
            - `{context}` - контекст из базы знаний
            - `{question}` - вопрос пользователя
            """)
        else:
            st.markdown("""
            - `{question}` - вопрос пользователя
            - `{context}` - дополнительный контекст (опционально)
            """)
        
        # Статистика
        st.markdown("---")
        st.markdown("**📊 Статистика:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Длина промпта", len(edited_prompt))
        
        with col2:
            st.metric("Количество строк", edited_prompt.count('\n') + 1)
        
        with col3:
            st.metric("Количество слов", len(edited_prompt.split()))
