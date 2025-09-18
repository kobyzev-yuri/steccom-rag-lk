"""
Utility functions for satellite billing system
Contains helper functions for data display and other utilities
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional
import logging
from .database import execute_query
from .charts import create_chart

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def display_query_results(query: str, params: Tuple = ()) -> None:
    """Helper function to display query results with charts."""
    logger.info(f"display_query_results вызвана с запросом: {query[:50]}...")
    
    results = execute_query(query, params)
    
    if isinstance(results, tuple) and len(results) == 2:
        df, error = results
        if error:
            st.error(f"Error executing query: {error}")
        else:
            st.dataframe(df)
            
            # Download option - moved right after table
            if not df.empty:
                csv = df.to_csv(index=False)
                # Unique key for download button
                dl_counter_key = 'download_widget_counter'
                if dl_counter_key not in st.session_state:
                    st.session_state[dl_counter_key] = 0
                dl_key = f"download_btn_{st.session_state[dl_counter_key]}"
                st.session_state[dl_counter_key] += 1
                st.download_button(
                    label="📥 Скачать CSV",
                    data=csv,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key=dl_key
                )
            
            # Chart section - автоматическое построение графика
            if not df.empty:
                st.markdown("### 📊 График")
                
                # Ensure unique key per widget instance to avoid duplicate key errors
                counter_key = 'chart_widget_counter'
                if counter_key not in st.session_state:
                    st.session_state[counter_key] = 0
                unique_key = f"chart_type_{st.session_state[counter_key]}"
                st.session_state[counter_key] += 1

                chart_type = st.selectbox(
                    "Тип графика:",
                    ["line", "bar", "pie", "scatter"],
                    format_func=lambda x: {
                        "line": "📈 Линейный график",
                        "bar": "📊 Столбчатая диаграмма", 
                        "pie": "🥧 Круговая диаграмма",
                        "scatter": "🔍 Точечная диаграмма"
                    }[x],
                    key=unique_key
                )
                
                # Автоматически строим график
                logger.info(f"Автоматически строим график типа: {chart_type}")
                logger.info(f"Данные: {df.shape}, колонки: {list(df.columns)}")
                create_chart(df, chart_type)
    else:
        st.error("Unexpected query result format")


def _generate_quick_question() -> str:
    """Generate a random quick question for the user"""
    import random
    from .queries import QUICK_QUESTIONS
    return random.choice(QUICK_QUESTIONS)
