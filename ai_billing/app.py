"""
AI Billing System - Main Application
Focused on billing operations with RAG system integration
"""

import streamlit as st
import logging
from logging.handlers import RotatingFileHandler
import os
import sys

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
    st.session_state.setdefault('sql_assistant_model', 'qwen3:8b')
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

    # Models tab
    with tab_models:
        st.subheader("🤖 RAG Assistant - Конфигурация моделей")
        try:
            import os
            provider = st.selectbox("Провайдер чата", ["ollama", "proxyapi", "openai"], index=0, key="model_provider")
            if provider == "ollama":
                model = st.text_input("OLLAMA_CHAT_MODEL", value=os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:1.5b"), key="ollama_model")
                if st.button("Применить", key="apply_ollama_model"):
                    try:
                        if st.session_state.get('multi_rag'):
                            st.session_state.multi_rag.set_chat_backend("ollama", model)
                            st.success("Применено: Ollama → " + model)
                    except Exception as e:
                        st.error(f"Не удалось применить: {e}")
            elif provider == "proxyapi":
                base_url = st.text_input("PROXYAPI_BASE_URL", value=os.getenv("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1"), key="proxyapi_base")
                api_key = st.text_input("PROXYAPI_API_KEY", type="password", value=os.getenv("PROXYAPI_API_KEY", ""), key="proxyapi_key")
                model = st.text_input("PROXYAPI_CHAT_MODEL", value=os.getenv("PROXYAPI_CHAT_MODEL", "gpt-4o"), key="proxyapi_model")
                temp = st.slider("Температура", 0.0, 1.0, 0.2, 0.1, key="proxyapi_temp")
                if st.button("Применить", key="apply_proxyapi_model"):
                    try:
                        if st.session_state.get('multi_rag'):
                            st.session_state.multi_rag.set_chat_backend("proxyapi", model, base_url, api_key, temp)
                            st.success("Применено: ProxyAPI → " + model)
                    except Exception as e:
                        st.error(f"Не удалось применить: {e}")
            else:
                model = st.text_input("OPENAI_CHAT_MODEL", value=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"), key="openai_model")
                api_key = st.text_input("OPENAI_API_KEY", type="password", value=os.getenv("OPENAI_API_KEY", ""), key="openai_key")
                temp = st.slider("Температура", 0.0, 1.0, 0.2, 0.1, key="openai_temp")
                if st.button("Применить", key="apply_openai_model"):
                    try:
                        if st.session_state.get('multi_rag'):
                            st.session_state.multi_rag.set_chat_backend("openai", model, api_key=api_key, temperature=temp)
                            st.success("Применено: OpenAI → " + model)
                    except Exception as e:
                        st.error(f"Не удалось применить: {e}")
        except Exception as e:
            st.error(f"Ошибка конфигурации моделей: {e}")

        # SQL Assistant configuration
        st.markdown("---")
        st.subheader("🧮 SQL Assistant")
        try:
            import subprocess
            
            # Get available Ollama models
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
                        current_sql_model = st.session_state.get('sql_assistant_model', 'qwen3:8b')
                        selected_model = st.selectbox(
                            "Модель для SQL Assistant:",
                            available_models,
                            index=available_models.index(current_sql_model) if current_sql_model in available_models else 0,
                            key="sql_model_select"
                        )
                        
                        if st.button("Применить для SQL Assistant", key="apply_sql_model"):
                            st.session_state.sql_assistant_model = selected_model
                            st.success(f"SQL Assistant настроен на модель: {selected_model}")
                    else:
                        st.warning("Не удалось получить список моделей Ollama")
                else:
                    st.error("Ошибка выполнения ollama list")
            except subprocess.TimeoutExpired:
                st.error("Таймаут при получении списка моделей")
            except FileNotFoundError:
                st.error("Ollama не найден. Убедитесь, что Ollama установлен и запущен.")
            except Exception as e:
                st.error(f"Ошибка получения моделей: {e}")
                
        except Exception as e:
            st.error(f"Ошибка конфигурации SQL Assistant: {e}")

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
    
    try:
        import subprocess
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            available_models = []
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]  # Get first column (model name)
                    available_models.append(model_name)
            
            if available_models:
                current_sql_model = st.session_state.get('sql_assistant_model', 'qwen3:8b')
                selected_sql_model = st.selectbox(
                    "Модель для SQL Assistant:",
                    available_models,
                    index=available_models.index(current_sql_model) if current_sql_model in available_models else 0,
                    key="sql_model_select"
                )
                
                if st.button("Применить для SQL Assistant", key="apply_sql_model"):
                    st.session_state.sql_assistant_model = selected_sql_model
                    st.success(f"SQL Assistant настроен на модель: {selected_sql_model}")
            else:
                st.warning("Не удалось получить список моделей Ollama")
        else:
            st.error("Ошибка выполнения ollama list")
    except subprocess.TimeoutExpired:
        st.error("Таймаут при получении списка моделей")
    except FileNotFoundError:
        st.error("Ollama не найден. Убедитесь, что Ollama установлен и запущен.")
    except Exception as e:
        st.error(f"Ошибка при получении списка моделей: {e}")
    
    st.markdown("---")
    
    # RAG Assistant Model Configuration
    st.subheader("🤖 RAG Assistant")
    
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
    except subprocess.TimeoutExpired:
        st.error("Таймаут при получении списка моделей")
    except FileNotFoundError:
        st.error("Ollama не найден. Убедитесь, что Ollama установлен и запущен.")
    except Exception as e:
        st.error(f"Ошибка при получении списка моделей: {e}")
    
    st.markdown("---")
    
    # Current Model Status
    st.subheader("📊 Текущие настройки")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**SQL Assistant:**")
        st.info(f"Модель: {st.session_state.get('sql_assistant_model', 'qwen3:8b')}")
    
    with col2:
        st.markdown("**RAG Assistant:**")
        st.info(f"Модель: {st.session_state.get('rag_assistant_model', 'qwen2.5:1.5b')}")


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