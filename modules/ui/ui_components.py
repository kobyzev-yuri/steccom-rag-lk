"""
UI Components module for satellite billing system
Contains all Streamlit UI rendering functions
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from typing import Optional
import plotly.express as px

# Optional RAG helper import for admin actions
try:
    from ..rag.rag_helper import RAGHelper
    _RAG_AVAILABLE = True
except Exception:
    _RAG_AVAILABLE = False

from ..core.database import execute_standard_query, execute_query
from ..core.rag import generate_sql
from ..core.utils import display_query_results
from ..core.charts import create_chart
from ..core.queries import STANDARD_QUERIES, QUICK_QUESTIONS


def render_user_view():
    """Render the main user interface"""
    st.title("🏠 Личный кабинет СТЭККОМ")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Выберите раздел:",
        ["📊 Стандартные отчеты", "📝 Пользовательский запрос", "🤖 Умный помощник", "❓ Помощь"],
        key="user_page"
    )
    
    # System status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Статус системы")
    
    if st.session_state.get('rag_initialized'):
        st.sidebar.success("✅ RAG система активна")
    else:
        st.sidebar.warning("⚠️ RAG система недоступна")
    
    if st.session_state.get('kb_loaded_count', 0) > 0:
        st.sidebar.success(f"📚 Загружено БЗ: {st.session_state.kb_loaded_count}")
        
        if st.session_state.get('loaded_kbs_info'):
            with st.sidebar.expander("📋 Детали БЗ"):
                for kb in st.session_state.loaded_kbs_info:
                    st.write(f"• {kb}")
    else:
        st.sidebar.warning("📚 Базы знаний не загружены")
    
    # Route to appropriate page
    if page == "📊 Стандартные отчеты":
        render_standard_reports()
    elif page == "📝 Пользовательский запрос":
        render_custom_query()
    elif page == "🤖 Умный помощник":
        render_smart_assistant()
    elif page == "❓ Помощь":
        render_help()


def render_standard_reports(company_override: Optional[str] = None):
    """Render standard reports page"""
    st.subheader("📊 Стандартные отчеты")
    st.write("Выберите готовый отчет из списка ниже:")
    
    # For staff: inline company selector (with All Companies)
    if st.session_state.is_staff:
        try:
            companies_query = "SELECT DISTINCT company FROM users WHERE role = 'user' ORDER BY company"
            conn = sqlite3.connect('satellite_billing.db')
            _df_companies = pd.read_sql_query(companies_query, conn)
            conn.close()
            company_options = ["All Companies"] + _df_companies['company'].tolist()
        except Exception:
            company_options = ["All Companies"]
        selected_company_sr = st.selectbox("Компания:", company_options, key="standard_reports_company_selector")
        # Prefer inline selector over external override
        company_override = selected_company_sr
    
    # Use session_state for report type
    report_type = st.selectbox(
        "Тип отчета:",
        [
            "Текущий договор",
            "Список устройств",
            "Трафик за месяц",
            "Использование за текущий месяц",
            "Сессии за последние 30 дней",
            "Статистика по типам услуг",
            "Помесячный SBD трафик",
            "Помесячный VSAT_DATA трафик",
            "Помесячный VSAT_VOICE трафик",
            "SBD сессии",
            "VSAT_DATA сессии",
            "VSAT_VOICE сессии"
        ],
        index=["Текущий договор", "Список устройств", "Трафик за месяц", 
               "Использование за текущий месяц", "Сессии за последние 30 дней", "Статистика по типам услуг", "Помесячный SBD трафик", "Помесячный VSAT_DATA трафик", "Помесячный VSAT_VOICE трафик", "SBD сессии", "VSAT_DATA сессии", "VSAT_VOICE сессии"].index(st.session_state.current_report_type),
        key="report_type"
    )
    
    # Pre-select chart type before running
    chart_type_selection = st.selectbox(
        "Тип графика:",
        ["line", "bar", "pie", "scatter"],
        format_func=lambda x: {
            "line": "📈 Линейный график",
            "bar": "📊 Столбчатая диаграмма", 
            "pie": "🥧 Круговая диаграмма",
            "scatter": "🔍 Точечная диаграмма"
        }[x],
        key="standard_chart_type_global"
    )
    
    # Update session_state when report type changes
    if report_type != st.session_state.current_report_type:
        st.session_state.current_report_type = report_type
    
    if st.button("Показать отчет", key="show_report"):
        with st.spinner("Загрузка отчета..."):
            # Determine user role for access control
            user_role = 'staff' if st.session_state.is_staff else 'user'
            
            # Determine target company for query execution
            if st.session_state.is_staff:
                # Staff uses inline selector (may be All Companies)
                if report_type == "Текущий договор" and (company_override is None or company_override == "All Companies"):
                    st.warning("Для отчета 'Текущий договор' выберите конкретную компанию.")
                    return
                company_for_query = company_override if company_override and company_override != "All Companies" else None
            else:
                company_for_query = st.session_state.company
            
            if report_type == "Текущий договор":
                query = STANDARD_QUERIES["Current agreement"]
            elif report_type == "Список устройств":
                query = STANDARD_QUERIES["My devices"]
            elif report_type == "Трафик за месяц":
                query = STANDARD_QUERIES["My monthly traffic"]
            elif report_type == "Использование за текущий месяц":
                query = STANDARD_QUERIES["Current month usage"]
            elif report_type == "Сессии за последние 30 дней":
                query = STANDARD_QUERIES["Service sessions"]
            elif report_type == "Статистика по типам услуг":
                query = """
                SELECT 
                    st.name as service_type,
                    st.unit as unit,
                    COUNT(DISTINCT d.imei) as device_count,
                    SUM(b.usage_amount) as total_usage,
                    ROUND(SUM(b.amount), 2) as total_amount,
                    ROUND(AVG(b.usage_amount), 2) as avg_usage_per_device
                FROM billing_records b
                JOIN agreements a ON b.agreement_id = a.id
                JOIN users u ON a.user_id = u.id
                JOIN service_types st ON b.service_type_id = st.id
                LEFT JOIN devices d ON b.imei = d.imei
                WHERE u.company = ?
                GROUP BY st.name, st.unit
                ORDER BY total_usage DESC;
                """
            elif report_type == "Помесячный SBD трафик":
                query = STANDARD_QUERIES["SBD monthly traffic"]
            elif report_type == "Помесячный VSAT_DATA трафик":
                query = STANDARD_QUERIES["VSAT_DATA monthly traffic"]
            elif report_type == "Помесячный VSAT_VOICE трафик":
                query = STANDARD_QUERIES["VSAT_VOICE monthly traffic"]
            elif report_type == "SBD сессии":
                query = STANDARD_QUERIES["SBD sessions"]
            elif report_type == "VSAT_DATA сессии":
                query = STANDARD_QUERIES["VSAT_DATA sessions"]
            elif report_type == "VSAT_VOICE сессии":
                query = STANDARD_QUERIES["VSAT_VOICE sessions"]
            
            # Execute query
            if report_type != "Текущий договор" and st.session_state.is_staff and (company_override == "All Companies"):
                # Remove company filter for aggregated admin view
                query_to_run = query.replace("WHERE u.company = ?", "WHERE 1=1")
                df, error = execute_query(query_to_run)
            else:
                if st.session_state.is_staff and company_for_query is None:
                    # Safety fallback (should not happen due to early return)
                    st.warning("Не выбрана компания для отчета.")
                    return
                df, error = execute_query(query, (company_for_query,))
            
            if error:
                st.error(f"Ошибка выполнения запроса: {error}")
            else:
                # Сохраняем данные отчета в session_state
                report_key = f"standard_report_{report_type}"
                st.session_state[f"{report_key}_data"] = df
                st.session_state[f"{report_key}_query"] = query
                
                st.write(df.head(3))
                
                st.markdown("#### Результаты отчета")
                if df.empty:
                    st.warning("Нет данных для отображения")
                else:
                    st.table(df)
                
                # Download option - сразу после таблицы
                if not df.empty:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Скачать результаты как CSV",
                        data=csv,
                        file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                # Chart section - use pre-selected chart type
                if not df.empty:
                    st.markdown("### 📊 График")
                    try:
                        if "service_type" in df.columns and df["service_type"].nunique() > 1:
                            for svc in df["service_type"].dropna().unique():
                                st.markdown(f"#### {svc}")
                                df_svc = df[df["service_type"] == svc]
                                create_chart(df_svc, chart_type_selection)
                        else:
                            # Guard: different units without service_type separation → skip chart
                            if "unit" in df.columns and df["unit"].nunique() > 1 and "service_type" not in df.columns:
                                st.warning("Найдено несколько единиц измерения без разделения по типам услуг. Построение общего графика отключено.")
                            else:
                                create_chart(df, chart_type_selection)
                    except Exception as e:
                        st.warning(f"Не удалось построить график: {e}")


def render_custom_query():
    """Render custom query page"""
    st.subheader("📝 Пользовательский запрос")
    st.write("Задайте вопрос на русском языке, и система создаст SQL-запрос для анализа ваших данных.")
    
    # Show example questions
    with st.expander("💡 Примеры вопросов"):
        st.markdown("""
        **📊 Аналитика:**
        - Покажи статистику трафика за последний месяц
        - Какие устройства потребляют больше всего трафика?
        - Сколько у меня активных соглашений?
        
        **🔧 Технические:**
        - Какие требования к антенне для спутниковой связи?
        - Как настроить GPS трекинг?
        - Какие параметры конфигурации нужны?
        
        **📋 Документы:**
        - Покажи технические регламенты
        - Какие стандарты безопасности?
        - Процедуры настройки оборудования
        """)
    
    # Use session_state for user question
    user_question = st.text_area(
        "💬 Задайте ваш вопрос:",
        value=st.session_state.current_user_question,
        placeholder="Например: Покажи статистику трафика за последнюю неделю",
        height=100,
        key="user_question"
    )
    
    # Update session_state when question changes
    if user_question != st.session_state.current_user_question:
        st.session_state.current_user_question = user_question
    
    if st.button("Создать запрос", key="create_query"):
        if user_question:
            # DEBUG: Print the user question before processing
            
            with st.spinner("Генерирую запрос..."):
                # Try to use multi-KB RAG first for enhanced context
                if st.session_state.get('multi_rag') and st.session_state.multi_rag.get_available_kbs():
                    # Use multi-KB RAG for enhanced context
                    kb_response = st.session_state.multi_rag.get_response_with_context(
                        user_question, context_limit=3
                    )
                    if kb_response and "Не найдено релевантной информации" not in kb_response:
                        st.markdown("#### 📚 Контекст из базы знаний")
                        st.info(kb_response)
                        st.markdown("---")
                
                # Generate SQL query using direct function (preserves full user question)
                query = generate_sql(user_question, st.session_state.company)
                if query:
                    # Store results in session_state
                    st.session_state.current_sql_query = query
                    st.session_state.current_query_explanation = f"SQL запрос для: {user_question}"
                    st.session_state.current_query_results = execute_query(query)
                    
                    st.markdown("#### Объяснение запроса")
                    st.info(st.session_state.current_query_explanation)
                    st.markdown("#### SQL Запрос")
                    st.code(query, language="sql")
                    st.markdown("#### Результаты")
                    display_query_results(query)
                else:
                    st.error("Не удалось сгенерировать запрос. Попробуйте переформулировать вопрос.")
        else:
            st.warning("Пожалуйста, введите ваш вопрос.")
    
    # Note: убрано повторное отображение "Последний запрос", чтобы избежать дублирования


def render_smart_assistant():
    """Render smart assistant page"""
    st.subheader("🤖 Умный помощник")
    st.write("Задайте вопрос по документации, техническим требованиям или процедурам.")
    
    # Quick questions
    st.markdown("### 🚀 Быстрые вопросы")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Статистика трафика", key="quick_traffic"):
            st.session_state.current_assistant_question = "Покажи статистику трафика за последний месяц"
    
    with col2:
        if st.button("🔧 Технические требования", key="quick_tech"):
            st.session_state.current_assistant_question = "Какие технические требования к спутниковой связи?"
    
    with col3:
        if st.button("📋 Документация", key="quick_docs"):
            st.session_state.current_assistant_question = "Покажи техническую документацию"
    
    # Question input
    assistant_question = st.text_area(
        "💬 Ваш вопрос:",
        value=st.session_state.current_assistant_question,
        placeholder="Например: Какие требования к антенне для спутниковой связи?",
        height=100,
        key="assistant_question"
    )
    
    # Update session_state when question changes
    if assistant_question != st.session_state.current_assistant_question:
        st.session_state.current_assistant_question = assistant_question
    
    if st.button("Задать вопрос", key="ask_assistant"):
        if assistant_question:
            with st.spinner("Ищу ответ..."):
                if st.session_state.rag_helper:
                    # Determine role for filtering (admin can see user docs too)
                    role = 'admin' if st.session_state.get('is_staff') else 'user'
                    response = st.session_state.rag_helper.get_response(assistant_question, role=role)
                    st.session_state.assistant_answer = response
                else:
                    st.error("Система помощи недоступна. Пожалуйста, обратитесь к администратору.")
        else:
            st.warning("Пожалуйста, введите ваш вопрос.")
    
    # Display assistant answer if available
    if st.session_state.assistant_answer:
        st.markdown("#### 💬 Ответ:")
        st.markdown(st.session_state.assistant_answer)


def render_help():
    """Render help page"""
    st.subheader("❓ Помощь")
    st.markdown("""
    ### Как пользоваться личным кабинетом
    
    #### 1. Стандартные отчеты
    - Выберите готовый отчет из списка
    - Нажмите "Показать отчет"
    - Результаты можно скачать в формате CSV
    
    #### 2. Пользовательский запрос
    - Задайте вопрос на русском языке
    - Система автоматически создаст SQL-запрос
    - Результаты отображаются в виде таблицы и графика
    
    #### 3. Умный помощник
    - Задавайте вопросы по документации и техническим требованиям
    - Система найдет релевантную информацию в базах знаний
    - Показывает источники информации
    
    #### 4. Ограничения
    - Доступны только данные вашей компании
    - Некоторые сложные запросы могут требовать уточнения
    - При ошибках попробуйте переформулировать вопрос
    """)
    
    if st.button("Показать подробную справку"):
        with st.spinner("Загружаю справку..."):
            if st.session_state.rag_helper:
                help_text = st.session_state.rag_helper.get_response("Как пользоваться личным кабинетом?")
                st.markdown(help_text)
            else:
                st.error("Система помощи недоступна.")


def render_staff_view():
    """Render staff/admin view"""
    st.title("🔧 Административная панель СТЭККОМ")
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["📊 Аналитика трафика", "🤖 Умный помощник", "🔧 Админ-панель"])
    
    with tab1:
        # Company selector
        companies_query = "SELECT DISTINCT company FROM users WHERE role = 'user' ORDER BY company"
        conn = sqlite3.connect('satellite_billing.db')
        df = pd.read_sql_query(companies_query, conn)
        conn.close()
        
        selected_company = st.selectbox("Select Company:", ["All Companies"] + df['company'].tolist())
        # Pre-select chart type for analytics
        chart_type_analytics = st.selectbox(
            "Chart Type:",
            ["line", "bar", "pie", "scatter"],
            key="staff_chart_type_analytics"
        )
    
    # Smart Assistant tab (RAG-only)
    with tab2:
        render_smart_assistant()

    # Admin Panel + SQL Agent
    with tab3:
        # AI Query Assistant (SQL only)
        st.header("AI Query Assistant")
        user_question = st.text_area(
            "Ask a question:",
            placeholder="e.g., Show traffic statistics for last month",
            height=100
        )
        
        if st.button("Generate Query"):
            if user_question:
                with st.spinner("Generating query..."):
                    # Use company filter if specific company selected
                    company_filter = selected_company if selected_company != "All Companies" else None
                    query = generate_sql(user_question, company_filter)
                    
                    if query:
                        st.markdown("#### Generated SQL Query")
                        st.code(query, language="sql")
                        
                        # Execute and display results
                        st.markdown("#### Query Results")
                        # Pass parameters only if the SQL has placeholders
                        if company_filter and ("?" in query):
                            df, error = execute_query(query, (company_filter,))
                        else:
                            df, error = execute_query(query)
                        
                        if error:
                            st.error(f"Query execution error: {error}")
                        else:
                            st.dataframe(df)
                            
                            # Chart
                            if not df.empty:
                                st.markdown("#### Chart")
                                try:
                                    if chart_type_analytics == "pie" and ("month" in df.columns) and ("company" in df.columns):
                                        # Render per-month pies with slices per company
                                        df_local = df.copy()
                                        # Ensure month label
                                        try:
                                            df_local["month_str"] = pd.to_datetime(df_local["month"], errors='coerce').dt.strftime('%Y-%m').fillna(df_local["month"].astype(str))
                                        except Exception:
                                            df_local["month_str"] = df_local["month"].astype(str)
                                        # Determine values column (prefer common metrics)
                                        value_candidates = ["total_usage", "total_amount", "usage_amount", "total_traffic"]
                                        values_col = next((c for c in value_candidates if c in df_local.columns), None)
                                        if values_col is None:
                                            # fallback to first numeric column
                                            exclude = {"month", "month_str", "company", "service_type", "unit", "device_id", "imei"}
                                            numeric_cols = [c for c in df_local.columns if c not in exclude and pd.api.types.is_numeric_dtype(pd.to_numeric(df_local[c], errors='coerce'))]
                                            values_col = numeric_cols[0] if numeric_cols else None
                                        for m in df_local["month_str"].dropna().unique():
                                            st.markdown(f"##### {m}")
                                            df_m = df_local[df_local["month_str"] == m]
                                            if values_col is None:
                                                st.warning("Нет числовой метрики для круговой диаграммы")
                                            else:
                                                df_m = df_m.copy()
                                                df_m[values_col] = pd.to_numeric(df_m[values_col], errors='coerce')
                                                fig = px.pie(df_m, names="company", values=values_col)
                                                st.plotly_chart(fig, use_container_width=True)
                                    elif "service_type" in df.columns and df["service_type"].nunique() > 1:
                                        for svc in df["service_type"].dropna().unique():
                                            st.markdown(f"##### {svc}")
                                            df_svc = df[df["service_type"] == svc]
                                            create_chart(df_svc, chart_type_analytics)
                                    else:
                                        if "unit" in df.columns and df["unit"].nunique() > 1 and "service_type" not in df.columns:
                                            st.warning("Несколько единиц измерения без разделения по типам услуг. График отключен.")
                                        else:
                                            create_chart(df, chart_type_analytics)
                                except Exception as e:
                                    st.warning(f"Не удалось построить график: {e}")
                    else:
                        st.error("Failed to generate query. Please try rephrasing your question.")
            else:
                st.warning("Please enter a question.")

        st.header("Admin Panel")
        st.write("Administrative functions.")

        st.subheader("RAG Management")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Перезагрузить RAG систему", key="admin_reload_rag"):
                if _RAG_AVAILABLE:
                    try:
                        st.session_state.rag_helper = RAGHelper()
                        st.session_state.rag_initialized = True
                        st.success("RAG система перезагружена")
                    except Exception as e:
                        st.error(f"Ошибка перезагрузки RAG: {e}")
                else:
                    st.error("RAGHelper недоступен на этом окружении")
        with col_b:
            if st.button("📚 Проверить доступные KB", key="admin_list_kb"):
                try:
                    import glob
                    kb_files = sorted(glob.glob("docs/kb/*.json"))
                    if kb_files:
                        st.write("Найденные KB файлы:")
                        for f in kb_files:
                            st.write(f"• {f}")
                    else:
                        st.info("KB файлы в docs/kb/ не найдены")
                except Exception as e:
                    st.error(f"Ошибка проверки KB: {e}")

        st.markdown("---")
        st.subheader("Data Utilities")
        st.info("Генерация тестовых VOICE-сессий перенесена в отдельный скрипт: scripts/generate_vsat_voice_data.py")

        st.markdown("---")
        st.subheader("KB Files Management")
        try:
            import glob
            import os
            import json
            kb_files = sorted(glob.glob("docs/kb/*.json"))
            selected_kb = st.selectbox("Выберите KB для действий:", ["—"] + kb_files, key="kb_select")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Удалить выбранный KB", key="kb_delete"):
                    if selected_kb != "—":
                        try:
                            os.remove(selected_kb)
                            st.success(f"Удален: {selected_kb}")
                        except Exception as e:
                            st.error(f"Ошибка удаления: {e}")
                    else:
                        st.info("Выберите файл для удаления")
            with col2:
                if st.button("🔄 Обновить список", key="kb_refresh_list"):
                    st.rerun()

            st.markdown("### Создать/обновить KB")
            new_name = st.text_input("Имя файла (docs/kb/*.json)", value="docs/kb/new_kb.json", key="kb_new_name")
            default_payload = '[\n  {\n    "title": "Пример KB",\n    "audience": ["user", "admin"],\n    "scope": ["legacy_billing"],\n    "status": "reference",\n    "source": {"file": "data/uploads/reg_07032015.pdf", "pointer": "п.9"},\n    "content": [\n      {"title": "Услуга детализированного отчета", "text": "Раздел регламента…"}\n    ]\n  }\n]'
            payload = st.text_area("Содержимое JSON", height=240, value=default_payload, key="kb_payload")
            if st.button("💾 Создать/Обновить", key="kb_save"):
                try:
                    # Validate JSON
                    data = json.loads(payload)
                    # Ensure correct path
                    if not new_name.startswith("docs/kb/") or not new_name.endswith('.json'):
                        st.error("Файл должен быть внутри docs/kb/ и иметь расширение .json")
                    else:
                        os.makedirs("docs/kb", exist_ok=True)
                        with open(new_name, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        st.success(f"Сохранено: {new_name}")
                except Exception as e:
                    st.error(f"Ошибка сохранения: {e}")
        except Exception as e:
            st.error(f"Ошибка управления KB: {e}")

        st.markdown("---")
        st.subheader("Логи приложения")
        try:
            import os
            log_file = os.path.join("logs", "app.log")
            if os.path.exists(log_file):
                max_lines = st.slider("Сколько последних строк показать?", min_value=50, max_value=2000, value=500, step=50, key="log_lines")
                level_filter = st.selectbox("Фильтр по уровню", ["ALL", "ERROR", "WARNING", "INFO"], index=0, key="log_level")
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()[-max_lines:]
                if level_filter != "ALL":
                    lines = [ln for ln in lines if f"[{level_filter}]" in ln]
                st.code("".join(lines) or "(пусто)", language="text")
            else:
                st.info("Лог-файл пока не создан.")
        except Exception as e:
            st.error(f"Не удалось прочитать логи: {e}")

        st.caption("Примечание: при обнаружении ошибок в логах я сначала сообщу вам, а уже затем предложу исправление.")
        st.subheader("PDF Uploads → KB (Legacy)")
        try:
            import os
            os.makedirs("data/uploads", exist_ok=True)
            uploaded = st.file_uploader("Загрузить PDF (сохранится в data/uploads)", type=["pdf"], key="kb_pdf_uploader")
            if uploaded is not None:
                pdf_path = os.path.join("data/uploads", uploaded.name)
                with open(pdf_path, 'wb') as f:
                    f.write(uploaded.getbuffer())
                st.success(f"Загружено: {pdf_path}")

            # List current uploads
            import glob as _glob
            pdfs = sorted(_glob.glob("data/uploads/*.pdf"))
            if pdfs:
                st.write("Загруженные PDF:")
                st.write("\n".join([f"• {p}" for p in pdfs]))
            else:
                st.info("В data/uploads нет PDF")

            st.markdown("### Создать KB из PDF (ссылочный, LEGACY)")
            sel_pdf = st.selectbox("PDF источник:", ["—"] + pdfs, key="pdf_select_for_kb")
            kb_title = st.text_input("Заголовок KB", value="Услуга детализированного отчета (регламент)", key="pdf_kb_title")
            pointer = st.text_input("Указатель в документе (например, 'п.9')", value="п.9", key="pdf_pointer")
            audience = st.multiselect("Аудитория", ["user", "admin"], default=["user", "admin"], key="pdf_audience")
            status = st.selectbox("Статус", ["reference", "released", "preview", "deprecated"], index=0, key="pdf_status")
            target_json = st.text_input("Имя KB файла", value="docs/kb/legacy_reglament.json", key="pdf_target_json")

            if st.button("📄 Сгенерировать KB JSON", key="pdf_create_kb_json"):
                try:
                    if sel_pdf == "—":
                        st.error("Выберите PDF источник")
                    elif not target_json.startswith("docs/kb/") or not target_json.endswith('.json'):
                        st.error("Имя файла должно быть в docs/kb/ и .json")
                    else:
                        payload = [
                            {
                                "title": kb_title,
                                "audience": audience,
                                "scope": ["legacy_billing"],
                                "status": status,
                                "source": {"file": sel_pdf, "pointer": pointer},
                                "content": [
                                    {"title": kb_title, "text": f"См. {pointer} в {sel_pdf}."}
                                ]
                            }
                        ]
                        import json as _json
                        os.makedirs("docs/kb", exist_ok=True)
                        with open(target_json, 'w', encoding='utf-8') as f:
                            _json.dump(payload, f, ensure_ascii=False, indent=2)
                        st.success(f"Создан KB: {target_json}")
                        st.info("Нажмите 'Перезагрузить RAG систему' выше, чтобы подхватить изменения")
                except Exception as e:
                    st.error(f"Ошибка генерации KB: {e}")
        except Exception as e:
            st.error(f"Ошибка загрузки PDF/создания KB: {e}")

        st.markdown("---")
        st.subheader("MediaWiki Integration")
        try:
            from ..integrations import MediaWikiClient, KBToWikiPublisher
            
            # Настройки MediaWiki
            st.markdown("### Настройки подключения")
            wiki_url = st.text_input("URL MediaWiki", value="http://localhost:8080/w/api.php", key="wiki_url")
            wiki_username = st.text_input("Имя пользователя", key="wiki_username")
            wiki_password = st.text_input("Пароль", type="password", key="wiki_password")
            namespace_prefix = st.text_input("Префикс пространства имен", value="СТЭККОМ", key="wiki_namespace")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔗 Тест подключения", key="wiki_test"):
                    if wiki_url and wiki_username and wiki_password:
                        try:
                            client = MediaWikiClient(wiki_url, wiki_username, wiki_password)
                            st.success("✅ Подключение к MediaWiki успешно")
                        except Exception as e:
                            st.error(f"❌ Ошибка подключения: {e}")
                    else:
                        st.warning("Заполните все поля для тестирования")
            
            with col2:
                if st.button("📚 Публиковать все KB", key="wiki_publish_all"):
                    if wiki_url and wiki_username and wiki_password:
                        try:
                            client = MediaWikiClient(wiki_url, wiki_username, wiki_password)
                            publisher = KBToWikiPublisher(client)
                            
                            with st.spinner("Публикация в MediaWiki..."):
                                results = publisher.publish_all_kb_files("docs/kb", namespace_prefix)
                                
                            st.success("Публикация завершена")
                            
                            # Показываем результаты
                            for kb_file, file_results in results.items():
                                with st.expander(f"📄 {kb_file}"):
                                    for success, message in file_results:
                                        if success:
                                            st.success(f"✅ {message}")
                                        else:
                                            st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"Ошибка публикации: {e}")
                    else:
                        st.warning("Заполните настройки подключения")
            
            # Публикация отдельных файлов
            st.markdown("### Публикация отдельных файлов")
            try:
                import glob
                kb_files = sorted(glob.glob("docs/kb/*.json"))
                selected_kb = st.selectbox("Выберите KB файл:", ["—"] + kb_files, key="wiki_kb_select")
                
                if st.button("📤 Публиковать выбранный файл", key="wiki_publish_selected"):
                    if selected_kb != "—" and wiki_url and wiki_username and wiki_password:
                        try:
                            client = MediaWikiClient(wiki_url, wiki_username, wiki_password)
                            publisher = KBToWikiPublisher(client)
                            
                            with st.spinner(f"Публикация {selected_kb}..."):
                                results = publisher.publish_kb_file(selected_kb, namespace_prefix)
                            
                            for success, message in results:
                                if success:
                                    st.success(f"✅ {message}")
                                else:
                                    st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"Ошибка публикации: {e}")
                    else:
                        st.warning("Выберите файл и заполните настройки")
            except Exception as e:
                st.error(f"Ошибка выбора файлов: {e}")
                
        except ImportError as e:
            st.error(f"Модуль MediaWiki недоступен: {e}")
        except Exception as e:
            st.error(f"Ошибка MediaWiki интеграции: {e}")
