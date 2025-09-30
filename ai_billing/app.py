"""
AI Billing System - Main Application
Focused on billing operations with RAG system integration
"""

import streamlit as st
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

# Load environment variables from config file
def load_config():
    """Load configuration from config.env file"""
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.env')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load configuration on startup
load_config()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core modules
from modules.core import init_db, verify_login
from modules.ui import render_user_view, render_staff_view
from modules.rag.multi_kb_rag import MultiKBRAG

# Configure application logging
def _configure_logging() -> None:
    """Configure logging for the application"""
    try:
        os.makedirs("logs", exist_ok=True)
        log_path = os.path.join("logs", "ai_billing.log")
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Avoid adding multiple handlers on reruns
        if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
            fh = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding='utf-8')
            fh.setLevel(logging.INFO)
            fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            fh.setFormatter(fmt)
            logger.addHandler(fh)

        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in logger.handlers):
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s'))
            logger.addHandler(ch)
    except Exception as e:
        print(f"Logging configuration failed: {e}")


def initialize_session_state():
    """Initialize session state variables"""
    # Authentication state
    st.session_state.setdefault('authenticated', False)
    st.session_state.setdefault('username', None)
    st.session_state.setdefault('role', None)
    st.session_state.setdefault('company', None)
    st.session_state.setdefault('is_staff', False)
    
    # UI state
    st.session_state.setdefault('current_report_type', "Текущий договор")
    st.session_state.setdefault('current_user_question', "")
    st.session_state.setdefault('current_assistant_question', "")
    st.session_state.setdefault('current_sql_query', "")
    st.session_state.setdefault('current_query_explanation', "")
    st.session_state.setdefault('current_query_results', None)
    st.session_state.setdefault('assistant_answer', "")
    
    # RAG system state
    st.session_state.setdefault('rag_initialized', False)
    st.session_state.setdefault('rag_initializing', False)
    st.session_state.setdefault('multi_rag', None)
    st.session_state.setdefault('kb_loaded_count', 0)
    st.session_state.setdefault('loaded_kbs_info', [])
    
    # Model configuration
    st.session_state.setdefault('sql_assistant_model', 'qwen2.5:1.5b')
    st.session_state.setdefault('rag_assistant_model', 'qwen2.5:1.5b')


def initialize_rag_system():
    """Initialize RAG system for Knowledge Base access"""
    if st.session_state.get('rag_initializing'):
        return

    if not st.session_state.rag_initialized:
        try:
            st.session_state.rag_initializing = True
            
            # Initialize Multi-KB RAG
            st.session_state.multi_rag = MultiKBRAG()
            
            # Set default RAG model
            if 'rag_assistant_model' not in st.session_state:
                st.session_state.rag_assistant_model = 'qwen2.5:1.5b'
            
            # Apply the selected RAG model
            try:
                st.session_state.multi_rag.set_chat_backend("ollama", st.session_state.rag_assistant_model)
            except Exception as e:
                print(f"Не удалось установить RAG модель: {e}")
            
            # Load active knowledge bases
            try:
                loaded_count = st.session_state.multi_rag.load_all_active_kbs()
                print(f"✅ Загружено активных БЗ: {loaded_count}")
            except Exception as e:
                print(f"Ошибка при загрузке активных БЗ: {e}")
            
            # Get available KBs info
            available_kbs = st.session_state.multi_rag.get_available_kbs()
            st.session_state.kb_loaded_count = len(available_kbs)
            st.session_state.loaded_kbs_info = available_kbs
            st.session_state.rag_initialized = True
            
        except Exception as e:
            print(f"Ошибка инициализации RAG: {e}")
        finally:
            st.session_state.rag_initializing = False


def render_staff_view():
    """Render staff/admin view"""
    st.title("🔧 Административная панель СТЭККОМ")
    
    # Navigation tabs
    tab_logs, tab_models, tab_admin = st.tabs([
        "📜 Логи", "🤖 Модели", "🔧 Админ-панель"
    ])

    # Logs tab
    with tab_logs:
        st.subheader("Логи приложения")
        try:
            import os
            log_file = os.path.join("logs", "ai_billing.log")
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

    # Models tab - removed, models are now managed in "Управление моделями" section
    with tab_models:
        st.info("🤖 Управление моделями перенесено в отдельный раздел 'Управление моделями'")
        st.markdown("""
        **Доступные функции:**
        - 🧮 **SQL Assistant** - выбор между Ollama и GPT-4o
        - 🤖 **RAG Assistant** - настройка моделей для работы с базами знаний
        - 📊 **Статистика токенов** - мониторинг использования
        """)


        # Token usage statistics
        try:
            import os as _os
            import sqlite3 as _sqlite3
            import pandas as pd
            db_path = _os.path.join("data", "knowledge_bases", "kbs.db")
            if _os.path.exists(db_path):
                conn = _sqlite3.connect(db_path)
                try:
                    df_usage = pd.read_sql_query(
                        "SELECT timestamp, provider, model, prompt_tokens, completion_tokens, total_tokens, LENGTH(question) as question_len, response_length FROM llm_usage ORDER BY id DESC LIMIT 500",
                        conn
                    )
                except Exception as e:
                    df_usage = None
                    st.warning(f"Таблица llm_usage недоступна: {e}")
                finally:
                    conn.close()

                if df_usage is not None and not df_usage.empty:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Всего записей", len(df_usage))
                    with col_b:
                        st.metric("Σ prompt tokens", int(pd.to_numeric(df_usage["prompt_tokens"], errors='coerce').fillna(0).sum()))
                    with col_c:
                        st.metric("Σ total tokens", int(pd.to_numeric(df_usage["total_tokens"], errors='coerce').fillna(0).sum()))

                    st.markdown("### Последние запросы")
                    st.dataframe(df_usage)
                else:
                    st.info("Пока нет данных об использовании токенов.")
            else:
                st.info("База данных с метриками не найдена: data/knowledge_bases/kbs.db")
        except Exception as e:
            st.error(f"Ошибка загрузки метрик: {e}")

    # Admin panel tab
    with tab_admin:
        st.header("Admin Panel")
        st.write("Administrative functions: RAG reload and KB management.")

        st.subheader("RAG Management")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🔄 Перезагрузить RAG систему", key="admin_reload_rag"):
                try:
                    st.session_state.rag_initialized = False
                    st.session_state.rag_initializing = False
                    st.session_state.multi_rag = None
                    initialize_rag_system()
                    st.success("RAG система перезагружена")
                except Exception as e:
                    st.error(f"Ошибка перезагрузки RAG: {e}")
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
        except Exception as e:
            st.error(f"Ошибка управления KB: {e}")


def render_model_management():
    """Render model management page"""
    st.header("🤖 Управление моделями")
    st.markdown("---")
    
    # SQL Assistant Model Configuration
    st.subheader("🧮 SQL Assistant")
    
    # Provider selection
    current_sql_model = st.session_state.get('sql_assistant_model', 'qwen2.5:1.5b')
    default_provider_index = 1 if current_sql_model == 'gpt-4o' else 0
    
    sql_provider = st.radio(
        "Выберите провайдера для SQL Assistant:",
        ["Ollama (локальные модели)", "GPT-4o (быстро и качественно)"],
        index=default_provider_index,
        key="sql_provider_select"
    )
    
    if sql_provider == "Ollama (локальные модели)":
        import subprocess
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                available_models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]  # Get first column (model name)
                        available_models.append(model_name)
                
                if available_models:
                    current_sql_model = st.session_state.get('sql_assistant_model', 'qwen2.5:1.5b')
                    # Filter to only show current model if it's Ollama
                    if current_sql_model in available_models:
                        default_index = available_models.index(current_sql_model)
                    else:
                        default_index = 0
                    
                    selected_sql_model = st.selectbox(
                        "Модель Ollama для SQL Assistant:",
                        available_models,
                        index=default_index,
                        key="sql_ollama_model_select"
                    )
                    
                    if st.button("Применить Ollama модель", key="apply_sql_ollama_model"):
                        st.session_state.sql_assistant_model = selected_sql_model
                        # Обновляем SQL Agent для использования Ollama
                        try:
                            from modules.core.rag import sql_agent
                            sql_agent.set_provider("ollama", selected_sql_model)
                            st.success(f"SQL Assistant настроен на Ollama модель: {selected_sql_model}")
                            st.rerun()  # Обновляем интерфейс
                        except Exception as e:
                            st.error(f"Ошибка при обновлении SQL Agent: {e}")
                else:
                    st.warning("Не удалось получить список моделей Ollama")
            else:
                st.error("Ошибка выполнения ollama list")
        except Exception as e:
            if "TimeoutExpired" in str(type(e)):
                st.error("Таймаут при получении списка моделей")
            elif "FileNotFoundError" in str(type(e)):
                st.error("Ollama не найден. Убедитесь, что Ollama установлен и запущен.")
            else:
                st.error(f"Ошибка при получении списка моделей: {e}")
    
    else:  # GPT-4o
        st.info("🚀 GPT-4o - быстрая и качественная генерация SQL запросов")
        st.markdown("""
        **Преимущества GPT-4o:**
        - ⚡ Быстрая генерация (1-2 минуты вместо 10+ минут)
        - 🎯 Высокое качество SQL запросов
        - 📊 Обработка сложных схем БД
        - 🔧 Автоматическая пост-обработка
        """)
        
        if st.button("Переключить на GPT-4o", key="apply_sql_gpt4o"):
            st.session_state.sql_assistant_model = 'gpt-4o'
            # Обновляем SQL Agent для использования ProxyAPI
            try:
                from modules.core.rag import sql_agent
                sql_agent.set_provider("proxyapi", "gpt-4o")
                st.success("SQL Assistant настроен на GPT-4o через ProxyAPI")
                st.rerun()  # Обновляем интерфейс
            except Exception as e:
                st.error(f"Ошибка при обновлении SQL Agent: {e}")
    
    st.markdown("---")
    
    # RAG Assistant Model Configuration
    st.subheader("🤖 RAG Assistant")
    
    import subprocess
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            available_models = []
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]  # Get first column (model name)
                    available_models.append(model_name)
            
            if available_models:
                current_rag_model = st.session_state.get('rag_assistant_model', 'qwen2.5:1.5b')
                selected_rag_model = st.selectbox(
                    "Модель для RAG Assistant:",
                    available_models,
                    index=available_models.index(current_rag_model) if current_rag_model in available_models else 0,
                    key="rag_model_select"
                )
                
                if st.button("Применить для RAG Assistant", key="apply_rag_model"):
                    st.session_state.rag_assistant_model = selected_rag_model
                    # Update RAG system with new model
                    if st.session_state.get('multi_rag'):
                        try:
                            st.session_state.multi_rag.set_chat_backend("ollama", selected_rag_model)
                            st.success(f"RAG Assistant настроен на модель: {selected_rag_model}")
                        except Exception as e:
                            st.error(f"Ошибка при обновлении RAG модели: {e}")
                    else:
                        st.success(f"RAG Assistant настроен на модель: {selected_rag_model}")
            else:
                st.warning("Не удалось получить список моделей Ollama")
        else:
            st.error("Ошибка выполнения ollama list")
    except Exception as e:
        if "TimeoutExpired" in str(type(e)):
            st.error("Таймаут при получении списка моделей")
        elif "FileNotFoundError" in str(type(e)):
            st.error("Ollama не найден. Убедитесь, что Ollama установлен и запущен.")
        else:
            st.error(f"Ошибка при получении списка моделей: {e}")
    
    st.markdown("---")
    
    # Current Model Status
    st.subheader("📊 Текущие настройки")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**SQL Assistant:**")
        current_sql_model = st.session_state.get('sql_assistant_model', 'qwen2.5:1.5b')
        if current_sql_model == 'gpt-4o':
            st.success(f"🚀 GPT-4o (быстро)")
        else:
            st.info(f"🦙 Ollama: {current_sql_model}")
    
    with col2:
        st.markdown("**RAG Assistant:**")
        st.info(f"Модель: {st.session_state.get('rag_assistant_model', 'qwen2.5:1.5b')}")
    
    st.markdown("---")
    
    # Token usage statistics
    st.subheader("📊 Статистика использования токенов")
    try:
        import os as _os
        import sqlite3 as _sqlite3
        import pandas as pd
        db_path = _os.path.join("data", "knowledge_bases", "kbs.db")
        if _os.path.exists(db_path):
            conn = _sqlite3.connect(db_path)
            try:
                df_usage = pd.read_sql_query(
                    "SELECT timestamp, provider, model, prompt_tokens, completion_tokens, total_tokens, LENGTH(question) as question_len, response_length FROM llm_usage ORDER BY id DESC LIMIT 500",
                    conn
                )
            except Exception as e:
                df_usage = None
                st.warning(f"Таблица llm_usage недоступна: {e}")
            finally:
                conn.close()

            if df_usage is not None and not df_usage.empty:
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    total_tokens = df_usage['total_tokens'].sum()
                    st.metric("Всего токенов", f"{total_tokens:,}")
                
                with col_b:
                    total_requests = len(df_usage)
                    st.metric("Всего запросов", f"{total_requests:,}")
                
                with col_c:
                    avg_tokens = df_usage['total_tokens'].mean()
                    st.metric("Среднее токенов/запрос", f"{avg_tokens:.0f}")
                
                # Показать последние 10 запросов
                st.markdown("**Последние запросы:**")
                recent_usage = df_usage.head(10)[['timestamp', 'provider', 'model', 'total_tokens', 'question_len']]
                recent_usage.columns = ['Время', 'Провайдер', 'Модель', 'Токены', 'Длина вопроса']
                st.dataframe(recent_usage, use_container_width=True)
                
                # Показать статистику по моделям
                st.markdown("**Статистика по моделям:**")
                model_stats = df_usage.groupby(['provider', 'model']).agg({
                    'total_tokens': ['sum', 'count', 'mean'],
                    'prompt_tokens': 'sum',
                    'completion_tokens': 'sum'
                }).round(0)
                model_stats.columns = ['Всего токенов', 'Запросов', 'Среднее токенов', 'Входные токены', 'Выходные токены']
                st.dataframe(model_stats, use_container_width=True)
            else:
                st.info("Нет данных об использовании токенов")
        else:
            st.warning("База данных не найдена")
    except Exception as e:
        st.error(f"Ошибка при загрузке статистики: {e}")


def login_page():
    """Render login page"""
    st.title("🛰️ СТЭККОМ - AI Billing System")
    st.markdown("### Вход в систему")
    
    with st.form("login_form"):
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        submit_button = st.form_submit_button("Войти")
        
        if submit_button:
            if username and password:
                success, role, company = verify_login(username, password)
                if success:
                    # Reset per-user UI/session state to avoid leakage across logins
                    ui_keys = [
                        'current_report_type', 'current_user_question', 'current_assistant_question',
                        'current_sql_query', 'current_query_explanation', 'current_query_results',
                        'assistant_answer', 'chart_widget_counter', 'download_widget_counter',
                        'plotly_chart_counter'
                    ]
                    for k in ui_keys:
                        if k in st.session_state:
                            del st.session_state[k]

                    # Set authentication state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.role = role
                    st.session_state.company = company
                    st.session_state.is_staff = (role == 'staff')
                    st.success(f"Добро пожаловать, {username}!")
                    st.rerun()
                else:
                    st.error("Неверное имя пользователя или пароль")
            else:
                st.error("Пожалуйста, заполните все поля")


def main():
    """Main application function"""
    # Configure logging
    _configure_logging()
    
    # Initialize database
    init_db()
    
    # Initialize session state
    initialize_session_state()
    
    # Hide Streamlit main menu
    st.markdown("""
    <style>
    [data-testid="stMainMenu"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize RAG system
    if not st.session_state.rag_initialized:
        initialize_rag_system()
    
    # Check authentication
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Main application interface
    if st.session_state.is_staff:
        # Staff view with choice between user and admin interfaces
        view_choice = st.sidebar.radio(
            "Выберите режим:",
            ["🏠 Личный кабинет", "🔧 Админ-панель", "🤖 Управление моделями"],
            key="staff_view_choice"
        )
        
        if view_choice == "🏠 Личный кабинет":
            render_user_view()
        elif view_choice == "🔧 Админ-панель":
            render_staff_view()
        else:  # Управление моделями
            render_model_management()
    else:
        # Regular user view with model management option
        view_choice = st.sidebar.radio(
            "Выберите режим:",
            ["🏠 Личный кабинет", "🤖 Управление моделями"],
            key="user_view_choice"
        )
        
        if view_choice == "🏠 Личный кабинет":
            render_user_view()
        else:  # Управление моделями
            render_model_management()
    
    # Logout button
    if st.sidebar.button("🚪 Выйти"):
        # Clear authentication-related and per-user UI session state
        keys_to_clear = [
            'authenticated', 'username', 'role', 'company', 'is_staff',
            'current_report_type', 'current_user_question', 'current_assistant_question',
            'current_sql_query', 'current_query_explanation', 'current_query_results',
            'assistant_answer', 'chart_widget_counter', 'download_widget_counter',
            'plotly_chart_counter'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    main()