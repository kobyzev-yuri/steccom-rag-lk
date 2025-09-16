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
    st.write(f"🔍 DEBUG: display_query_results вызвана")
    
    results = execute_query(query, params)
    
    if isinstance(results, tuple) and len(results) == 2:
        df, error = results
        if error:
            st.error(f"Error executing query: {error}")
        else:
            st.dataframe(df)
            
            # Chart section - автоматическое построение графика
            if not df.empty:
                st.markdown("### 📊 График")
                
                chart_type = st.selectbox(
                    "Тип графика:",
                    ["line", "bar", "pie", "scatter"],
                    format_func=lambda x: {
                        "line": "📈 Линейный график",
                        "bar": "📊 Столбчатая диаграмма", 
                        "pie": "🥧 Круговая диаграмма",
                        "scatter": "🔍 Точечная диаграмма"
                    }[x],
                    key=f"chart_type_{hash(query)}_{len(query)}"
                )
                
                # Автоматически строим график
                logger.info(f"Автоматически строим график типа: {chart_type}")
                logger.info(f"Данные: {df.shape}, колонки: {list(df.columns)}")
                create_chart(df, chart_type)
            
            # Download option
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Скачать CSV",
                    data=csv,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    else:
        st.error("Unexpected query result format")


def _generate_quick_question() -> str:
    """Generate a random quick question for the user"""
    import random
    from .queries import QUICK_QUESTIONS
    return random.choice(QUICK_QUESTIONS)
