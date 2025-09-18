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
    
    if df.empty:
        st.warning("Нет данных для построения графика")
        return
    
    try:
        # Unique key generator for plotly charts
        if 'plotly_chart_counter' not in st.session_state:
            st.session_state['plotly_chart_counter'] = 0
        def next_chart_key() -> str:
            k = f"plt_{st.session_state['plotly_chart_counter']}"
            st.session_state['plotly_chart_counter'] += 1
            return k

        # Try to coerce common numeric columns
        for col in ["total_usage", "total_amount", "usage_amount", "active_devices"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # Normalize possible time columns for ordering
        if "month" in df.columns:
            try:
                df["month"] = pd.to_datetime(df["month"], errors="coerce")
            except Exception:
                pass

        if chart_type == "line" and 'total_usage' in df.columns:
            # Возможные варианты оси X
            x_candidates = [
                'month', 'quarter', 'billing_date', 'session_start', 'start_time', 'activation_date'
            ]
            x_col = next((c for c in x_candidates if c in df.columns), None)
            if x_col:
                try:
                    if x_col == 'month':
                        df_sorted = df.sort_values(by='month')
                    elif x_col == 'quarter':
                        # Sort lexicographically works if formatted like YYYY-Q
                        df_sorted = df.sort_values(by='quarter')
                    else:
                        df_sorted = df.sort_values(by=x_col)
                except Exception:
                    df_sorted = df
                fig = px.line(df_sorted, x=x_col, y='total_usage', color='service_type' if 'service_type' in df.columns else None)
                st.plotly_chart(fig, use_container_width=True, key=next_chart_key())
            else:
                fig = px.line(df, y='total_usage', color='service_type' if 'service_type' in df.columns else None)
                st.plotly_chart(fig, use_container_width=True, key=next_chart_key())
         
        elif chart_type == "bar":
            # Prefer total_usage; fallback to total_amount or usage_amount
            y_col = 'total_usage' if 'total_usage' in df.columns else ('total_amount' if 'total_amount' in df.columns else ('usage_amount' if 'usage_amount' in df.columns else None))
            if not y_col:
                # Fallback to first numeric column
                non_x_exclude = {"month", "service_type", "unit", "company", "device_id", "imei"}
                numeric_cols = [c for c in df.columns if c not in non_x_exclude and pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors='coerce'))]
                if numeric_cols:
                    y_col = numeric_cols[0]
                else:
                    st.warning("Нет подходящих числовых колонок для столбчатой диаграммы")
                    return
            # Ensure y is numeric
            df_plot = df.copy()
            df_plot[y_col] = pd.to_numeric(df_plot[y_col], errors='coerce')
            x_col = None
            for candidate in ['month', 'quarter', 'service_type', 'company', 'device_id', 'imei', 'device_imei']:
                if candidate in df.columns:
                    x_col = candidate
                    break
            if x_col is None and len(df.columns) > 1:
                # choose first non-numeric column
                non_num = [c for c in df.columns if not pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors='coerce'))]
                x_col = non_num[0] if non_num else df.columns[0]
            if x_col:
                # Format month if used as x
                if x_col == 'month':
                    try:
                        df_plot['month_str'] = pd.to_datetime(df_plot['month'], errors='coerce').dt.strftime('%Y-%m').fillna(df_plot['month'].astype(str))
                        x_use = 'month_str'
                    except Exception:
                        x_use = x_col
                elif x_col == 'quarter':
                    x_use = x_col
                else:
                    x_use = x_col
                fig = px.bar(df_plot, x=x_use, y=y_col, color='service_type' if ('service_type' in df_plot.columns and x_col != 'service_type') else None)
                st.plotly_chart(fig, use_container_width=True, key=next_chart_key())
            else:
                st.warning("Не удалось определить ось X для столбчатой диаграммы")
         
        elif chart_type == "pie":
            # Require a categorical names and a numeric values
            values_col = 'total_usage' if 'total_usage' in df.columns else ('total_amount' if 'total_amount' in df.columns else ('usage_amount' if 'usage_amount' in df.columns else None))
            if not values_col:
                # Fallback: find first numeric column
                candidate_exclude = {"month", "service_type", "unit", "company", "device_id", "imei"}
                numeric_cols = [c for c in df.columns if c not in candidate_exclude and pd.api.types.is_numeric_dtype(pd.to_numeric(df[c], errors='coerce'))]
                if numeric_cols:
                    values_col = numeric_cols[0]
                else:
                    st.warning("Нет подходящей числовой колонки для круговой диаграммы")
                    return
            names_col = None
            # Prefer month for time-series pies, then service type
            for candidate in ['month', 'quarter', 'service_type', 'device_id', 'imei', 'device_imei']:
                if candidate in df.columns:
                    names_col = candidate
                    break
            if names_col:
                # If month is datetime, format to YYYY-MM for labels
                if names_col == 'month':
                    month_col = 'month_str'
                    try:
                        if pd.api.types.is_datetime64_any_dtype(df['month']):
                            df_plot = df.copy()
                            df_plot[month_col] = df_plot['month'].dt.strftime('%Y-%m')
                        else:
                            # Ensure it's treated as string
                            df_plot = df.copy()
                            df_plot[month_col] = pd.to_datetime(df_plot['month'], errors='coerce').dt.strftime('%Y-%m').fillna(df_plot['month'].astype(str))
                        # Ensure values are numeric
                        df_plot[values_col] = pd.to_numeric(df_plot[values_col], errors='coerce')
                        fig = px.pie(df_plot, names=month_col, values=values_col)
                    except Exception:
                        df_plot = df.copy()
                        df_plot[values_col] = pd.to_numeric(df_plot[values_col], errors='coerce')
                        fig = px.pie(df_plot, names=names_col, values=values_col)
                elif names_col == 'quarter':
                    # Use quarter string as is
                    df_plot = df.copy()
                    df_plot[values_col] = pd.to_numeric(df_plot[values_col], errors='coerce')
                    fig = px.pie(df_plot, names=names_col, values=values_col)
                else:
                    df_plot = df.copy()
                    df_plot[values_col] = pd.to_numeric(df_plot[values_col], errors='coerce')
                    fig = px.pie(df_plot, names=names_col, values=values_col)
                st.plotly_chart(fig, use_container_width=True, key=next_chart_key())
            else:
                st.warning("Не удалось определить поле для имен (секторов) круговой диаграммы")
         
        elif chart_type == "scatter":
            # Need two numeric axes; prefer month on x if present
            df_plot = df.copy()
            # Coerce potential numeric targets
            for col in ["total_usage", "total_amount", "usage_amount", "active_devices"]:
                if col in df_plot.columns:
                    df_plot[col] = pd.to_numeric(df_plot[col], errors='coerce')
            # Determine y
            y_col = 'total_usage' if 'total_usage' in df_plot.columns else ('total_amount' if 'total_amount' in df_plot.columns else ('usage_amount' if 'usage_amount' in df_plot.columns else None))
            if not y_col:
                numeric_cols = [c for c in df_plot.columns if pd.api.types.is_numeric_dtype(pd.to_numeric(df_plot[c], errors='coerce'))]
                y_col = numeric_cols[0] if numeric_cols else None
            # Determine x
            x_col = None
            if 'month' in df_plot.columns:
                try:
                    df_plot['month_str'] = pd.to_datetime(df_plot['month'], errors='coerce').dt.strftime('%Y-%m').fillna(df_plot['month'].astype(str))
                    x_col = 'month_str'
                except Exception:
                    x_col = 'month'
            elif 'quarter' in df_plot.columns:
                x_col = 'quarter'
            if x_col is None:
                # Prefer a categorical column
                categorical_cols = [c for c in df_plot.columns if not pd.api.types.is_numeric_dtype(pd.to_numeric(df_plot[c], errors='coerce'))]
                # Exclude known non-x meta columns if y might conflict
                preferred = [c for c in ['service_type', 'company', 'device_id', 'imei', 'device_imei'] if c in categorical_cols]
                x_col = preferred[0] if preferred else (categorical_cols[0] if categorical_cols else None)
            if x_col is None:
                # Fall back to second numeric
                numeric_cols = [c for c in df_plot.columns if pd.api.types.is_numeric_dtype(pd.to_numeric(df_plot[c], errors='coerce'))]
                if len(numeric_cols) >= 2:
                    x_col = numeric_cols[0 if y_col != numeric_cols[0] else 1]
                else:
                    st.warning("Недостаточно данных для scatter")
                    return
            color_col = 'service_type' if 'service_type' in df_plot.columns else ('company' if 'company' in df_plot.columns else None)
            fig = px.scatter(df_plot, x=x_col, y=y_col, color=color_col)
            st.plotly_chart(fig, use_container_width=True, key=next_chart_key())
            
    except Exception as e:
        st.error(f"Ошибка построения графика: {str(e)}")
