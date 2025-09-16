"""
Chart creation functions for satellite billing system
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_chart(df: pd.DataFrame, chart_type: str = "line") -> None:
    """Создает график на основе данных DataFrame"""
    logger.info(f"create_chart вызвана с типом: {chart_type}")
    logger.info(f"DataFrame пустой: {df.empty}")
    logger.info(f"Колонки: {list(df.columns)}")
    logger.info(f"Размер: {df.shape}")
    
    st.write(f"🔍 DEBUG: create_chart вызвана с типом: {chart_type}")
    st.write(f"🔍 DEBUG: DataFrame пустой: {df.empty}")
    st.write(f"🔍 DEBUG: Колонки: {list(df.columns)}")
    st.write(f"🔍 DEBUG: Размер: {df.shape}")
    
    if df.empty:
        st.warning("Нет данных для построения графика")
        return
    
    try:
        if chart_type == "line" and 'total_usage' in df.columns:
            # Линейный график
            if 'month' in df.columns:
                # График по месяцам
                if 'service_type' in df.columns:
                    fig = px.line(df, x='month', y='total_usage', color='service_type',
                                 title='Динамика трафика по типам услуг',
                                 labels={'month': 'Месяц', 'total_usage': 'Объем трафика'})
                else:
                    fig = px.line(df, x='month', y='total_usage', 
                                 title='Динамика трафика по месяцам',
                                 labels={'month': 'Месяц', 'total_usage': 'Объем трафика'})
            elif 'device_id' in df.columns:
                # График по устройствам (горизонтальный)
                fig = px.line(df, x='device_id', y='total_usage',
                             title='Трафик по устройствам',
                             labels={'device_id': 'Устройство', 'total_usage': 'Объем трафика'})
            else:
                # Общий линейный график
                fig = px.line(df, y='total_usage',
                             title='Объем трафика',
                             labels={'total_usage': 'Объем трафика'})
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "bar" and 'total_usage' in df.columns:
            # Столбчатая диаграмма для сравнения
            if 'device_id' in df.columns:
                # График по устройствам
                fig = px.bar(df, x='device_id', y='total_usage',
                            title='Трафик по устройствам',
                            labels={'device_id': 'Устройство', 'total_usage': 'Объем трафика'})
            elif 'service_type' in df.columns:
                # График по типам услуг
                fig = px.bar(df, x='service_type', y='total_usage',
                            title='Сравнение трафика по типам услуг',
                            labels={'service_type': 'Тип услуги', 'total_usage': 'Объем трафика'})
            else:
                # Общий график
                fig = px.bar(df, y='total_usage',
                            title='Объем трафика',
                            labels={'total_usage': 'Объем трафика'})
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "pie" and 'total_usage' in df.columns:
            # Круговая диаграмма для распределения трафика
            if 'device_id' in df.columns:
                # Круговая диаграмма по устройствам
                fig = px.pie(df, values='total_usage', names='device_id',
                            title='Распределение трафика по устройствам')
            elif 'service_type' in df.columns:
                # Круговая диаграмма по типам услуг
                fig = px.pie(df, values='total_usage', names='service_type',
                            title='Распределение трафика по типам услуг')
            else:
                # Общая круговая диаграмма
                fig = px.pie(df, values='total_usage',
                            title='Распределение трафика')
            st.plotly_chart(fig, use_container_width=True)
            
        elif chart_type == "scatter" and 'usage_amount' in df.columns and 'duration_minutes' in df.columns:
            # Точечная диаграмма для анализа сессий
            if 'service_type' in df.columns:
                fig = px.scatter(df, x='duration_minutes', y='usage_amount', color='service_type',
                               title='Анализ сессий по типам услуг',
                               labels={'duration_minutes': 'Длительность (мин)', 'usage_amount': 'Объем трафика'})
            else:
                fig = px.scatter(df, x='duration_minutes', y='usage_amount',
                               title='Анализ сессий: длительность vs объем',
                               labels={'duration_minutes': 'Длительность (мин)', 'usage_amount': 'Объем трафика'})
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            # Универсальный график для любых данных
            st.info("Создаю универсальный график...")
            
            # Найдем числовые колонки
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                # Используем первую числовую колонку
                y_col = numeric_cols[0]
                x_col = df.columns[0] if len(df.columns) > 1 else None
                
                if chart_type == "line":
                    if x_col:
                        fig = px.line(df, x=x_col, y=y_col, title=f'График: {y_col}')
                    else:
                        fig = px.line(df, y=y_col, title=f'График: {y_col}')
                elif chart_type == "bar":
                    if x_col:
                        fig = px.bar(df, x=x_col, y=y_col, title=f'Диаграмма: {y_col}')
                    else:
                        fig = px.bar(df, y=y_col, title=f'Диаграмма: {y_col}')
                elif chart_type == "pie":
                    if x_col and y_col:
                        fig = px.pie(df, names=x_col, values=y_col, title=f'Круговая диаграмма: {y_col}')
                    else:
                        st.warning("Для круговой диаграммы нужны две колонки")
                        return
                else:
                    st.warning(f"Тип графика '{chart_type}' не поддерживается для данных")
                    return
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Нет числовых данных для построения графика")
            
    except Exception as e:
        st.error(f"Ошибка построения графика: {str(e)}")
