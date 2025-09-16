import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
import hashlib
from openai import OpenAI
from rag_helper import RAGHelper
import os
import sys

# Add modules to path
sys.path.append(os.path.dirname(__file__))

# Import admin panel and multi-KB RAG
try:
    from modules.admin.admin_panel import AdminPanel
    from modules.rag.multi_kb_rag import MultiKBRAG
    ADMIN_AVAILABLE = True
    MULTI_RAG_AVAILABLE = True
except ImportError as e:
    st.warning(f"Admin panel not available: {e}")
    ADMIN_AVAILABLE = False
    MULTI_RAG_AVAILABLE = False

# Initialize OpenAI client for Ollama
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'is_staff' not in st.session_state:
    st.session_state.is_staff = False
if 'company' not in st.session_state:
    st.session_state.company = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Initialize state for preserving data between interactions
if 'assistant_answer' not in st.session_state:
    st.session_state.assistant_answer = ""
if 'assistant_question' not in st.session_state:
    st.session_state.assistant_question = ""
if 'current_report_type' not in st.session_state:
    st.session_state.current_report_type = "Текущий договор"
if 'current_user_question' not in st.session_state:
    st.session_state.current_user_question = ""
if 'current_query_results' not in st.session_state:
    st.session_state.current_query_results = None
if 'current_query_explanation' not in st.session_state:
    st.session_state.current_query_explanation = ""
if 'current_sql_query' not in st.session_state:
    st.session_state.current_sql_query = ""

# Database initialization
def init_db():
    conn = sqlite3.connect('satellite_billing.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        company TEXT NOT NULL,
        role TEXT CHECK(role IN ('staff', 'user')) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agreements (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        plan_type TEXT NOT NULL,
        monthly_fee REAL NOT NULL,
        traffic_limit_bytes INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        status TEXT CHECK(status IN ('active', 'pending', 'terminated')) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS devices (
        imei TEXT PRIMARY KEY,
        user_id INTEGER,
        device_type TEXT NOT NULL,
        model TEXT NOT NULL,
        activated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS billing_records (
        id INTEGER PRIMARY KEY,
        agreement_id INTEGER,
        imei TEXT NOT NULL,
        billing_date TEXT NOT NULL,
        traffic_bytes INTEGER NOT NULL,
        amount REAL NOT NULL,
        paid BOOLEAN NOT NULL DEFAULT 0,
        payment_date TEXT,
        FOREIGN KEY (agreement_id) REFERENCES agreements(id),
        FOREIGN KEY (imei) REFERENCES devices(imei)
    );
    ''')
    
    # Insert sample data only if tables are empty
    if not c.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        # Hash passwords
        def hash_password(password: str) -> str:
            return hashlib.sha256(password.encode()).hexdigest()
        
        # Insert users with IGNORE to avoid conflicts
        c.executescript(f'''
        INSERT OR IGNORE INTO users (username, password, company, role) VALUES 
            ('staff1', '{hash_password("staff123")}', 'Admin', 'staff'),
            ('arctic_user', '{hash_password("arctic123")}', 'Arctic Research Station', 'user'),
            ('desert_user', '{hash_password("desert123")}', 'Desert Observatory', 'user');
        ''')
        
        # Get user IDs
        arctic_user_id = c.execute("SELECT id FROM users WHERE username = 'arctic_user'").fetchone()[0]
        desert_user_id = c.execute("SELECT id FROM users WHERE username = 'desert_user'").fetchone()[0]
        
        # Insert agreements with IGNORE
        c.executescript(f'''
        INSERT OR IGNORE INTO agreements (user_id, plan_type, monthly_fee, traffic_limit_bytes, start_date, end_date, status) VALUES 
            ({arctic_user_id}, 'premium', 1000.00, 1099511627776, '2025-01-01', '2025-12-31', 'active'),
            ({desert_user_id}, 'standard', 500.00, 549755813888, '2025-01-01', '2025-12-31', 'active');
        ''')
        
        # Get agreement IDs
        arctic_agreement_id = c.execute(f"SELECT id FROM agreements WHERE user_id = {arctic_user_id}").fetchone()[0]
        desert_agreement_id = c.execute(f"SELECT id FROM agreements WHERE user_id = {desert_user_id}").fetchone()[0]
        
        # Insert devices with IGNORE
        c.executescript(f'''
        INSERT OR IGNORE INTO devices (imei, user_id, device_type, model, activated_at) VALUES 
            ('123456789012345', {arctic_user_id}, 'satellite', 'SAT-100', '2025-01-01'),
            ('123456789012346', {arctic_user_id}, 'satellite', 'SAT-100', '2025-01-01'),
            ('223456789012345', {desert_user_id}, 'satellite', 'SAT-200', '2025-01-01');
        ''')

        # Generate 2025 traffic data (January to July)
        traffic_data = []
        
        # Arctic Research Station (2 devices)
        for month in range(1, 8):  # January to July
            # First device - higher usage pattern
            base_traffic = 5 * 1024 * 1024 * 1024  # 5 GB base
            monthly_variation = month * 0.5 * 1024 * 1024 * 1024  # Increasing by 0.5 GB per month
            traffic_bytes = int(base_traffic + monthly_variation)
            amount = round(traffic_bytes / (1024 * 1024 * 1024) * 100, 2)  # $100 per GB
            traffic_data.append(
                f"({arctic_agreement_id}, '123456789012345', '2025-{month:02d}-15', {traffic_bytes}, {amount}, 1)"
            )
            
            # Second device - lower usage pattern
            base_traffic = 3 * 1024 * 1024 * 1024  # 3 GB base
            monthly_variation = month * 0.3 * 1024 * 1024 * 1024  # Increasing by 0.3 GB per month
            traffic_bytes = int(base_traffic + monthly_variation)
            amount = round(traffic_bytes / (1024 * 1024 * 1024) * 100, 2)
            traffic_data.append(
                f"({arctic_agreement_id}, '123456789012346', '2025-{month:02d}-15', {traffic_bytes}, {amount}, 1)"
            )

        # Desert Observatory (1 device)
        for month in range(1, 8):  # January to July
            base_traffic = 4 * 1024 * 1024 * 1024  # 4 GB base
            monthly_variation = month * 0.4 * 1024 * 1024 * 1024  # Increasing by 0.4 GB per month
            traffic_bytes = int(base_traffic + monthly_variation)
            amount = round(traffic_bytes / (1024 * 1024 * 1024) * 100, 2)
            traffic_data.append(
                f"({desert_agreement_id}, '223456789012345', '2025-{month:02d}-15', {traffic_bytes}, {amount}, 1)"
            )

        # Insert traffic data with IGNORE
        if traffic_data:
            c.execute(f'''
            INSERT OR IGNORE INTO billing_records (agreement_id, imei, billing_date, traffic_bytes, amount, paid) 
            VALUES {','.join(traffic_data)};
            ''')
    
    conn.commit()
    conn.close()

def verify_login(username: str, password: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Verify login credentials and return (success, role, company)"""
    conn = sqlite3.connect('satellite_billing.db')
    c = conn.cursor()
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        c.execute("""
            SELECT role, company 
            FROM users 
            WHERE username = ? AND password = ?
        """, (username, hashed_password))
        result = c.fetchone()
        if result:
            return True, result[0], result[1]
        return False, None, None
    finally:
        conn.close()

# Standard queries for users
STANDARD_QUERIES = {
    "My monthly traffic": """
    SELECT 
        strftime('%Y-%m', b.billing_date) as month,
        ROUND(CAST(SUM(b.traffic_bytes) AS FLOAT) / (1024.0 * 1024.0 * 1024.0), 2) as traffic_gb,
        COUNT(DISTINCT b.imei) as active_devices,
        ROUND(SUM(b.amount), 2) as total_amount
    FROM billing_records b
    JOIN agreements a ON b.agreement_id = a.id
    JOIN users u ON a.user_id = u.id
    WHERE u.company = ?
    GROUP BY strftime('%Y-%m', b.billing_date)
    ORDER BY month DESC;
    """,
    
    "My devices": """
    SELECT 
        d.imei as device_id,
        d.device_type as type,
        d.model as model,
        d.activated_at as activation_date,
        ROUND(CAST(SUM(b.traffic_bytes) AS FLOAT) / (1024.0 * 1024.0 * 1024.0), 2) as total_traffic_gb
    FROM devices d
    LEFT JOIN billing_records b ON d.imei = b.imei
    JOIN users u ON d.user_id = u.id
    WHERE u.company = ?
    GROUP BY d.imei;
    """,
    
    "Current month usage": """
    SELECT 
        d.imei as device_id,
        d.model as model,
        ROUND(CAST(SUM(b.traffic_bytes) AS FLOAT) / (1024.0 * 1024.0 * 1024.0), 2) as traffic_gb,
        ROUND(SUM(b.amount), 2) as total_amount
    FROM billing_records b
    JOIN devices d ON b.imei = d.imei
    JOIN users u ON d.user_id = u.id
    WHERE u.company = ?
    AND strftime('%Y-%m', b.billing_date) = strftime('%Y-%m', 'now')
    GROUP BY d.imei;
    """,
    
    "Current agreement": """
    SELECT 
        a.plan_type as plan,
        a.monthly_fee as fee,
        a.start_date as start_date,
        a.end_date as end_date,
        a.status as status
    FROM agreements a
    JOIN users u ON a.user_id = u.id
    WHERE u.company = ?
        AND date('now') BETWEEN date(a.start_date) AND date(a.end_date)
        AND a.status = 'active';
    """
}

def execute_standard_query(query_name: str, company: str) -> tuple[pd.DataFrame, Optional[str]]:
    """Execute a standard query with company parameter"""
    try:
        conn = sqlite3.connect('satellite_billing.db')
        df = pd.read_sql_query(STANDARD_QUERIES[query_name], conn, params=(company,))
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)
    finally:
        conn.close()

def get_table_schema(conn, table_name: str) -> str:
    """Get schema information for a specific table."""
    cursor = conn.cursor()
    
    # Get column info
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    
    # Get foreign key info
    cursor.execute(f"PRAGMA foreign_key_list({table_name});")
    foreign_keys = cursor.fetchall()
    
    # Format column descriptions
    schema = []
    for col in columns:
        # col: (cid, name, type, notnull, dflt_value, pk)
        desc = f"  - {col[1]} ({col[2]})"
        if col[5]:  # is primary key
            desc += " PRIMARY KEY"
        if col[3]:  # not null
            desc += " NOT NULL"
        # Add foreign key info if exists
        for fk in foreign_keys:
            if fk[3] == col[1]:  # if column is a foreign key
                desc += f" -> references {fk[2]}.{fk[4]}"
        schema.append(desc)
    
    return "\n".join(schema)

def get_database_schema() -> str:
    """Get complete database schema with relationships."""
    conn = sqlite3.connect('satellite_billing.db')
    try:
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Build schema description
        schema_parts = ["Database schema (EXACT column names):"]
        for table in tables:
            table_name = table[0]
            schema_parts.append(f"\n{table_name}:")
            schema_parts.append(get_table_schema(conn, table_name))
        
        return "\n".join(schema_parts)
    finally:
        conn.close()

def generate_sql(question: str, company: Optional[str] = None) -> str:
    """Generate SQL query from natural language question."""
    # Add company context if provided
    company_context = f"for the company '{company}'" if company else "across all companies"
    
    # Get current database schema
    schema = get_database_schema()
    
    prompt = f"""You are a SQLite expert for a satellite communications billing system. Generate a query for the following question {company_context}.

{schema}

Key Information:
1. Date and Time:
   - Month format: strftime('%Y-%m', billing_date)
   - Last N months: date(billing_date) >= date('now', '-N months')
   - Current month: strftime('%Y-%m', billing_date) = strftime('%Y-%m', 'now')
   - IMPORTANT: Date filtering should be done in the main query, not in WHERE clause of CTEs

2. Traffic and Money:
   - Traffic in GB: ROUND(CAST(traffic_bytes AS FLOAT) / (1024.0 * 1024.0 * 1024.0), 2)
   - Monthly totals: GROUP BY strftime('%Y-%m', billing_date)
   - Money totals: ROUND(SUM(amount), 2)

3. Table Relationships:
   billing_records -> agreements (agreement_id)
   agreements -> users (user_id)
   devices -> users (user_id)

Example Query - Traffic by company in last 3 months:
SELECT 
    strftime('%Y-%m', b.billing_date) as month,
    u.company,
    ROUND(CAST(SUM(b.traffic_bytes) AS FLOAT) / (1024.0 * 1024.0 * 1024.0), 2) as total_gb
FROM billing_records b
JOIN agreements a ON b.agreement_id = a.id
JOIN users u ON a.user_id = u.id
WHERE date(b.billing_date) >= date('now', '-3 months')
GROUP BY strftime('%Y-%m', b.billing_date), u.company
ORDER BY month DESC, total_gb DESC;

Question: {question}

Return ONLY the query, no explanation."""

    response = client.chat.completions.create(
        model="qwen2.5:3b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    query = response.choices[0].message.content.strip()
    # Remove any markdown formatting
    if query.startswith("```"):
        query = query.split("```")[1]
    if query.startswith("sql"):
        query = query[3:]
    return query.strip()

def execute_query(query: str, params: tuple = ()) -> tuple[pd.DataFrame, Optional[str]]:
    """Execute a query and return results as DataFrame"""
    try:
        conn = sqlite3.connect('satellite_billing.db')
        df = pd.read_sql_query(query, conn, params=params)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)
    finally:
        conn.close()

def display_query_results(query: str, params: tuple = ()):
    """Helper function to display query results."""
    results = execute_query(query, params)
    
    if isinstance(results, tuple) and len(results) == 2:
        df, error = results
        if error:
            st.error(f"Error executing query: {error}")
        else:
            st.dataframe(df)
            
            # Download option
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    else:
        st.error("Unexpected query result format")

def render_user_view():
    st.header(f"Личный кабинет: {st.session_state.company}")
    
    # Show system status
    if st.session_state.get('rag_initialized'):
        st.sidebar.success("✅ RAG система активна")
    else:
        st.sidebar.warning("⚠️ RAG система недоступна")
    
    # Show KB status
    if st.session_state.get('kb_loaded_count', 0) > 0:
        st.sidebar.success(f"📚 Загружено БЗ: {st.session_state.kb_loaded_count}")
        
        # Show detailed KB info
        if st.session_state.get('loaded_kbs_info'):
            with st.sidebar.expander("📋 Детали БЗ"):
                for kb in st.session_state.loaded_kbs_info:
                    st.write(f"• **{kb['name']}**")
                    st.write(f"  └ {kb['doc_count']} документов, {kb['chunk_count']} фрагментов")
    else:
        st.sidebar.info("📚 Базы знаний не загружены")
    
    # Add documentation assistant to sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 Умный помощник")
    
    # Show what the assistant can help with
    with st.sidebar.expander("💡 Что я могу помочь?"):
        st.markdown("""
        **📚 По документации:**
        - Технические требования
        - Процедуры настройки
        - Стандарты и регламенты
        
        **🔧 По системе:**
        - Как создать запрос
        - Анализ трафика
        - Работа с устройствами
        
        **❓ Задайте любой вопрос!**
        """)
        
        # Quick question generator
        if st.button("🎯 Сгенерировать вопрос", key="sidebar_question_gen"):
            quick_question = _generate_quick_question()
            st.session_state.assistant_question = quick_question
    
    # Controls for retrieval
    k_sources = st.sidebar.slider("Количество фрагментов (K)", 1, 8, 3, 1)

    # Use session_state for assistant question
    doc_question = st.sidebar.text_area(
        "Задайте вопрос:",
        value=st.session_state.assistant_question,
        placeholder="Например: какие требования к антенне?",
        key="doc_question"
    )
    
    # Rephrase button
    if st.sidebar.button("♻️ Переформулировать", key="rephrase_question"):
        if doc_question and st.session_state.get('rag_helper'):
            try:
                rephrased = st.session_state.rag_helper.get_response(
                    f"Переформулируй вопрос кратко и однозначно: {doc_question}. Верни только текст вопроса." 
                )
                if rephrased:
                    st.session_state.assistant_question = rephrased.strip()
                    st.session_state.assistant_answer = ""
                    doc_question = st.session_state.assistant_question
            except Exception:
                pass

    # Update session_state when question changes
    if doc_question != st.session_state.assistant_question:
        st.session_state.assistant_question = doc_question
        st.session_state.assistant_answer = ""  # Clear previous answer
    
    if st.sidebar.button("Получить ответ", key="get_doc_answer"):
        if doc_question:
            with st.spinner("Ищу ответ..."):
                # Try multi-KB RAG first
                if st.session_state.get('multi_rag') and st.session_state.multi_rag.get_available_kbs():
                    # Show sources first
                    try:
                        docs = st.session_state.multi_rag.search_across_kbs(doc_question, k=k_sources)
                    except Exception:
                        docs = []

                    if docs:
                        st.sidebar.markdown("**Источники:**")
                        for i, d in enumerate(docs, 1):
                            title = d.metadata.get('title', 'Документ')
                            kb_name = d.metadata.get('kb_name', '')
                            search_type = d.metadata.get('search_type', 'vector_search')
                            preview = d.page_content[:200].replace("\n", " ") + ("…" if len(d.page_content) > 200 else "")
                            st.sidebar.write(f"{i}. {title} — {kb_name} ({search_type})")
                            st.sidebar.caption(preview)

                    answer = st.session_state.multi_rag.get_response_with_context(doc_question, context_limit=k_sources)
                    if answer and "Не найдено релевантной информации" not in answer:
                        st.session_state.assistant_answer = answer
                    else:
                        # Fallback to original RAG helper
                        if st.session_state.rag_helper:
                            answer = st.session_state.rag_helper.get_response(doc_question)
                            st.session_state.assistant_answer = answer
                        else:
                            st.session_state.assistant_answer = "Система помощи недоступна."
                elif st.session_state.rag_helper:
                    # Use original RAG helper
                    answer = st.session_state.rag_helper.get_response(doc_question)
                    st.session_state.assistant_answer = answer
                else:
                    st.session_state.assistant_answer = "Система помощи недоступна."
        else:
            st.sidebar.warning("Пожалуйста, введите ваш вопрос.")
    
    # Display assistant answer if available
    if st.session_state.assistant_answer:
        st.sidebar.markdown("**Ответ:**")
        st.sidebar.markdown(st.session_state.assistant_answer)
    
    # Create tabs for different features
    tab1, tab2, tab3 = st.tabs(["📊 Стандартные отчеты", "📝 Пользовательский запрос", "❓ Помощь"])
    
    with tab1:
        st.subheader("Выберите готовый отчет")
        
        # Use session_state for report type
        report_type = st.selectbox(
            "Тип отчета:",
            [
                "Текущий договор",
                "Список устройств",
                "Трафик за неделю",
                "Трафик за месяц",
                "Статистика по типам устройств",
                "Дни максимальной нагрузки"
            ],
            index=["Текущий договор", "Список устройств", "Трафик за неделю", 
                   "Трафик за месяц", "Статистика по типам устройств", "Дни максимальной нагрузки"].index(st.session_state.current_report_type),
            key="report_type"
        )
        
        # Update session_state when report type changes
        if report_type != st.session_state.current_report_type:
            st.session_state.current_report_type = report_type
        
        if st.button("Показать отчет"):
            with st.spinner("Загрузка отчета..."):
                if report_type == "Текущий договор":
                    query = """
                    SELECT 
                        a.plan_type as plan,
                        a.monthly_fee as fee,
                        a.start_date as start_date,
                        a.end_date as end_date,
                        a.status as status
                    FROM agreements a
                    JOIN users u ON a.user_id = u.id
                    WHERE u.company = ?
                        AND date('now') BETWEEN date(a.start_date) AND date(a.end_date)
                        AND a.status = 'active'
                    """
                elif report_type == "Список устройств":
                    query = """
                    SELECT 
                        d.imei as device_id,
                        d.device_type as type,
                        d.model as model,
                        d.activated_at as activation_date
                    FROM devices d
                    JOIN users u ON d.user_id = u.id
                    WHERE u.company = ?
                    ORDER BY d.activated_at DESC
                    """
                elif report_type == "Трафик за неделю":
                    query = """
                    SELECT 
                        date(b.billing_date) as date,
                        ROUND(CAST(SUM(b.traffic_bytes) AS FLOAT) / (1024.0 * 1024.0 * 1024.0), 2) as traffic_gb,
                        COUNT(DISTINCT b.imei) as active_devices,
                        ROUND(SUM(b.amount), 2) as total_amount
                    FROM billing_records b
                    JOIN devices d ON b.imei = d.imei
                    JOIN users u ON d.user_id = u.id
                    WHERE u.company = ?
                        AND date(b.billing_date) >= date('now', '-7 days')
                    GROUP BY date(b.billing_date)
                    ORDER BY date DESC
                    """
                elif report_type == "Трафик за месяц":
                    query = """
                    SELECT 
                        date(b.billing_date) as date,
                        ROUND(CAST(SUM(b.traffic_bytes) AS FLOAT) / (1024.0 * 1024.0 * 1024.0), 2) as traffic_gb,
                        COUNT(DISTINCT b.imei) as active_devices,
                        ROUND(SUM(b.amount), 2) as total_amount
                    FROM billing_records b
                    JOIN devices d ON b.imei = d.imei
                    JOIN users u ON d.user_id = u.id
                    WHERE u.company = ?
                        AND date(b.billing_date) >= date('now', '-30 days')
                    GROUP BY date(b.billing_date)
                    ORDER BY date DESC
                    """
                elif report_type == "Статистика по типам устройств":
                    query = """
                    SELECT 
                        d.device_type as type,
                        COUNT(*) as count,
                        MIN(d.activated_at) as first_activation,
                        MAX(d.activated_at) as last_activation
                    FROM devices d
                    JOIN users u ON d.user_id = u.id
                    WHERE u.company = ?
                    GROUP BY d.device_type
                    """
                elif report_type == "Дни максимальной нагрузки":
                    query = """
                    SELECT 
                        date(b.billing_date) as date,
                        ROUND(CAST(SUM(b.traffic_bytes) AS FLOAT) / (1024.0 * 1024.0 * 1024.0), 2) as traffic_gb,
                        COUNT(DISTINCT b.imei) as active_devices,
                        ROUND(SUM(b.amount), 2) as total_amount
                    FROM billing_records b
                    JOIN devices d ON b.imei = d.imei
                    JOIN users u ON d.user_id = u.id
                    WHERE u.company = ?
                        AND date(b.billing_date) >= date('now', '-30 days')
                    GROUP BY date(b.billing_date)
                    ORDER BY traffic_gb DESC
                    LIMIT 5
                    """
                
                # Store results in session_state
                results = execute_query(query, params=(st.session_state.company,))
                st.session_state.current_query_results = results
                st.session_state.current_sql_query = query
                st.session_state.current_query_explanation = f"Результаты отчета: {report_type}"
        
        # Display stored results if available
        if st.session_state.current_query_results:
            df, error = st.session_state.current_query_results
            if error:
                st.error(f"Ошибка выполнения запроса: {error}")
            else:
                st.markdown("#### Результаты отчета")
                st.dataframe(df)
                
                # Download option
                if not df.empty:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Скачать результаты как CSV",
                        data=csv,
                        file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    
    with tab2:
        st.subheader("Создание пользовательского запроса")
        
        # Show example questions
        with st.expander("📝 Примеры вопросов"):
            st.markdown("""
            **Анализ трафика:**
            - Покажи мой трафик за вчера
            - Сколько трафика было в прошлом месяце?
            - Дни с максимальным трафиком
            
            **Информация об устройствах:**
            - Какие у меня установлены устройства?
            - Когда установили последнее устройство?
            - Список устройств по типам
            
            **Договоры и оплата:**
            - Информация о текущем договоре
            - Когда заканчивается договор?
            - Сумма оплаты по договору
            """)
        
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
        
        if st.button("Создать запрос"):
            if user_question:
                with st.spinner("Генерирую запрос..."):
                    # Try to use multi-KB RAG first for enhanced context
                    if st.session_state.get('multi_rag') and st.session_state.multi_rag.get_available_kbs():
                        # Use multi-KB RAG for enhanced context
                        kb_response = st.session_state.multi_rag.get_response_with_context(
                            user_question, context_limit=3
                        )
                        
                        # Show KB context if available
                        if kb_response and "Не найдено релевантной информации" not in kb_response:
                            st.markdown("#### 📚 Контекст из базы знаний")
                            st.info(kb_response)
                            st.markdown("---")
                    
                    # Generate SQL query
                    query, explanation = st.session_state.rag_helper.get_query_suggestion(
                        user_question, st.session_state.company
                    )
                    if query:
                        # Store results in session_state
                        st.session_state.current_sql_query = query
                        st.session_state.current_query_explanation = explanation
                        st.session_state.current_query_results = execute_query(query)
                        
                        st.markdown("#### Объяснение запроса")
                        st.info(explanation)
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
            
            if st.session_state.current_query_results:
                df, error = st.session_state.current_query_results
                if error:
                    st.error(f"Ошибка выполнения запроса: {error}")
                else:
                    st.markdown("**Результаты**")
                    st.dataframe(df)
                    
                    # Download option
                    if not df.empty:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Скачать результаты как CSV",
                            data=csv,
                            file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
    
    with tab3:
        st.markdown("""
        ### Как пользоваться личным кабинетом
        
        #### 1. Стандартные отчеты
        - Выберите готовый отчет из списка
        - Нажмите "Показать отчет"
        - Результаты можно скачать в формате CSV
        
        #### 2. Пользовательские запросы
        - Задайте вопрос на русском языке
        - Система создаст SQL-запрос и покажет результаты
        - Используйте примеры для подсказки
        
        #### 3. Ограничения
        - Доступны только данные вашей компании
        - Некоторые сложные запросы могут требовать уточнения
        - При ошибках попробуйте переформулировать вопрос
        """)
        
        if st.button("Показать подробную справку"):
            with st.spinner("Загружаю справку..."):
                help_text = st.session_state.rag_helper.get_response("Как пользоваться личным кабинетом?")
                st.markdown(help_text)

def render_staff_view():
    st.title("🔧 Административная панель СТЭККОМ")
    
    # Navigation tabs
    tab1, tab2 = st.tabs(["📊 Аналитика трафика", "🔧 Админ-панель"])
    
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
            help="Example: 'Show me total traffic per company in the last month' or 'List all active devices'"
        )
        
        if st.button("Generate Query"):
            with st.spinner("Generating query..."):
                company = None if selected_company == "All Companies" else selected_company
                query = generate_sql(user_question, company)
                results = execute_query(query)
                
                # Show query
                with st.expander("Show SQL Query"):
                    st.code(query, language="sql")
                
                # Show results
                if isinstance(results, tuple) and len(results) == 2:
                    df, error = results
                    if error:
                        st.error(f"Error executing query: {error}")
                    else:
                        st.dataframe(df)
                        
                        # Download option
                        if not df.empty:
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="Download results as CSV",
                                data=csv,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
    
    with tab2:
        if ADMIN_AVAILABLE:
            admin_panel = AdminPanel()
            admin_panel.render_main_panel()
        else:
            st.error("Админ-панель недоступна. Проверьте установку модулей.")

def _generate_quick_question():
    """Generate a quick question for the assistant"""
    import random
    
    questions = [
        "Какие требования к антенне для спутниковой связи?",
        "Как настроить GPS трекинг устройство?",
        "Какие параметры конфигурации нужны?",
        "Что такое SBD протокол?",
        "Какие стандарты безопасности применяются?",
        "Как провести калибровку антенны?",
        "Какие требования к мощности передатчика?",
        "Что указано в технических регламентах?",
        "Как настроить параметры связи?",
        "Какие стандарты качества связи?"
    ]
    
    return random.choice(questions)

def main():
    st.set_page_config(page_title="СТЭККОМ - Личный кабинет", layout="wide")
    st.title("🛰️ СТЭККОМ - Личный кабинет оператора спутниковой связи")
    
    # Initialize RAG helper (only once, silently)
    if 'rag_helper' not in st.session_state:
        try:
            st.session_state.rag_helper = RAGHelper()
            st.session_state.rag_initialized = True
        except Exception as e:
            st.session_state.rag_helper = None
            st.session_state.rag_initialized = False

    # Initialize Multi-KB RAG system (only once, silently)
    if 'multi_rag' not in st.session_state and MULTI_RAG_AVAILABLE:
        try:
            st.session_state.multi_rag = MultiKBRAG()
            # Auto-load all active knowledge bases silently
            loaded_count = st.session_state.multi_rag.load_all_active_kbs()
            # Store the count for later display
            st.session_state.kb_loaded_count = loaded_count
            # Store loaded KBs info for display
            st.session_state.loaded_kbs_info = st.session_state.multi_rag.get_available_kbs()
        except Exception as e:
            st.session_state.multi_rag = None
            st.session_state.kb_loaded_count = 0
            st.session_state.loaded_kbs_info = []

    # Initialize database
    init_db()
    
    # Sidebar with logout button if logged in
    if st.session_state.logged_in and st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    
    # Login screen
    if not st.session_state.logged_in:
        st.title("Login")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            success, role, company = verify_login(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.is_staff = (role == 'staff')
                st.session_state.company = company
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")
                
        # Show sample credentials
        with st.expander("Sample Credentials"):
            st.write("""
            Staff user:
            - Username: staff1
            - Password: staff123
            
            Regular users:
            - Username: arctic_user
            - Password: arctic123
            
            - Username: desert_user
            - Password: desert123
            """)
    else:
        # Render appropriate view based on role
        if st.session_state.is_staff:
            render_staff_view()
        else:
            render_user_view()

if __name__ == "__main__":
    main() 