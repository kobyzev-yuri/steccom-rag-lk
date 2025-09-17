"""
UI Components module for satellite billing system
Contains all Streamlit UI rendering functions
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from typing import Optional

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


def render_standard_reports():
    """Render standard reports page"""
    st.subheader("📊 Стандартные отчеты")
    st.write("Выберите готовый отчет из списка ниже:")
    
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
    
    # Update session_state when report type changes
    if report_type != st.session_state.current_report_type:
        st.session_state.current_report_type = report_type
    
    if st.button("Показать отчет", key="show_report"):
        st.write(f"🔍 DEBUG: Кнопка 'Показать отчет' нажата для: {report_type}")
        with st.spinner("Загрузка отчета..."):
            # Determine user role for access control
            user_role = 'staff' if st.session_state.is_staff else 'user'
            st.write(f"🔍 DEBUG: Роль пользователя: {user_role}")
            
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
            st.write(f"🔍 DEBUG: Выполняем запрос для компании: {st.session_state.company}")
            df, error = execute_query(query, (st.session_state.company,))
            st.write(f"🔍 DEBUG: Результат запроса: {type(df)}, ошибка: {error}")
            
            if error:
                st.error(f"Ошибка выполнения запроса: {error}")
            else:
                # Сохраняем данные отчета в session_state
                report_key = f"standard_report_{report_type}"
                st.session_state[f"{report_key}_data"] = df
                st.session_state[f"{report_key}_query"] = query
                
                st.write(f"🔍 DEBUG: Данные получены: {df.shape}, колонки: {list(df.columns)}")
                st.write(f"🔍 DEBUG: DataFrame пустой: {df.empty}")
                st.write(f"🔍 DEBUG: Первые 3 строки:")
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
                
                # Chart section - автоматическое построение графика
                if not df.empty:
                    st.markdown("### 📊 График")
                    
                    # Создаем уникальный ключ для этого отчета
                    chart_key = f"chart_{hash(report_type)}"
                    
                    # Выбор типа графика
                    chart_type = st.selectbox(
                        "Тип графика:",
                        ["line", "bar", "pie", "scatter"],
                        format_func=lambda x: {
                            "line": "📈 Линейный график",
                            "bar": "📊 Столбчатая диаграмма", 
                            "pie": "🥧 Круговая диаграмма",
                            "scatter": "🔍 Точечная диаграмма"
                        }[x],
                        key=f"standard_chart_type_{chart_key}"
                    )
                    
                    # Автоматически строим график
                    st.write(f"🔍 DEBUG: Автоматически строим график типа: {chart_type}")
                    st.write(f"🔍 DEBUG: Данные: {df.shape}, колонки: {list(df.columns)}")
                    create_chart(df, chart_type)


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
            print(f"🔍 DEBUG: User question in render_custom_query: '{user_question}'")
            print(f"🔍 DEBUG: Question length: {len(user_question)}")
            
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
                print(f"🔍 DEBUG: About to call generate_sql with: '{user_question}'")
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
    
    # Display stored results if available
    if st.session_state.current_query_explanation and st.session_state.current_sql_query:
        st.markdown("#### Последний запрос")
        st.markdown("**Объяснение запроса**")
        st.info(st.session_state.current_query_explanation)
        st.markdown("**SQL Запрос**")
        st.code(st.session_state.current_sql_query, language="sql")
        st.markdown("**Результаты**")
        display_query_results(st.session_state.current_sql_query)


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
    tab1, tab2, tab3 = st.tabs(["📊 Аналитика трафика", "📋 Стандартные отчеты", "🔧 Админ-панель"])
    
    with tab1:
        # Company selector
        companies_query = "SELECT DISTINCT company FROM users WHERE role = 'user' ORDER BY company"
        conn = sqlite3.connect('satellite_billing.db')
        df = pd.read_sql_query(companies_query, conn)
        conn.close()
        
        selected_company = st.selectbox("Select Company:", ["All Companies"] + df['company'].tolist())
    
    # AI Query Assistant
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
                    if company_filter:
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
                            # Создаем уникальный ключ для staff панели
                            import time
                            staff_unique_key = f"staff_{int(time.time() * 1000)}"
                            chart_type = st.selectbox(
                                "Chart Type:",
                                ["line", "bar", "pie", "scatter"],
                                key=f"staff_chart_type_{staff_unique_key}"
                            )
                            if st.button("Create Chart", key=f"create_staff_chart_{staff_unique_key}"):
                                create_chart(df, chart_type)
                else:
                    st.error("Failed to generate query. Please try rephrasing your question.")
        else:
            st.warning("Please enter a question.")
    
    with tab2:
        st.header("Standard Reports")
        # Standard reports functionality for staff
        render_standard_reports()
    
    with tab3:
        st.header("Admin Panel")
        st.write("Administrative functions will be implemented here.")
