#!/usr/bin/env python3
"""
Упрощенная версия KB Admin приложения
"""

import streamlit as st
import os
import sys
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kb_admin.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Настройка путей
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "modules"))

def main():
    """Главная функция приложения"""
    try:
        logger.info("Запуск KB Admin...")
        
        # Простой интерфейс без сложных импортов
        st.set_page_config(
            page_title="KB Admin - Управление базами знаний",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Заголовок
        st.title("🧠 KB Admin - Управление базами знаний")
        st.markdown("---")
        
        # Простой интерфейс
        st.header("📊 Статус системы")
        
        # Проверяем RAG систему
        try:
            from modules.rag.multi_kb_rag import MultiKBRAG
            rag = MultiKBRAG()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Базы знаний",
                    value=len(rag.kb_metadata),
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="Векторные хранилища",
                    value=len(rag.vectorstores),
                    delta=None
                )
            
            with col3:
                rag_status = "🟢 Активна" if len(rag.vectorstores) > 0 else "🔴 Неактивна"
                st.metric(
                    label="RAG система",
                    value=rag_status,
                    delta=None
                )
            
            # Тестируем поиск
            st.markdown("---")
            st.header("🔍 Тест поиска")
            
            query = st.text_input("Введите запрос для поиска:", value="спутниковая связь")
            
            if st.button("Поиск"):
                try:
                    results = rag.search_across_kbs(query, k=3)
                    st.success(f"Найдено результатов: {len(results)}")
                    
                    for i, doc in enumerate(results[:3]):
                        with st.expander(f"Результат {i+1}: {doc.metadata.get('title', 'Без названия')}"):
                            st.write(f"**Источник:** {doc.metadata.get('source', 'Неизвестно')}")
                            st.write(f"**Категория:** {doc.metadata.get('category', 'Неизвестно')}")
                            st.write("**Содержимое:**")
                            st.write(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                
                except Exception as e:
                    st.error(f"Ошибка поиска: {e}")
            
            # Информация о базах знаний
            st.markdown("---")
            st.header("📚 Информация о базах знаний")
            
            for kb_id, metadata in rag.kb_metadata.items():
                with st.expander(f"KB {kb_id}: {metadata['name']}"):
                    st.write(f"**Описание:** {metadata['description']}")
                    st.write(f"**Категория:** {metadata['category']}")
                    st.write(f"**Документов:** {metadata['doc_count']}")
                    st.write(f"**Чанков:** {metadata['chunk_count']}")
        
        except Exception as e:
            st.error(f"Ошибка инициализации RAG системы: {e}")
            logger.error(f"RAG initialization error: {e}")
        
        logger.info("KB Admin успешно запущен")
        
    except Exception as e:
        st.error(f"Критическая ошибка: {e}")
        logger.error(f"Critical error: {e}")

if __name__ == "__main__":
    main()










