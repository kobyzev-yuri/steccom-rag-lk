"""
AI Billing System - Simplified Application
Focused on using Knowledge Bases through RAG system
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
    
    # RAG system state
    st.session_state.setdefault('rag_initialized', False)
    st.session_state.setdefault('rag_initializing', False)
    st.session_state.setdefault('multi_rag', None)
    st.session_state.setdefault('kb_loaded_count', 0)
    st.session_state.setdefault('loaded_kbs_info', [])
    
    # UI state
    st.session_state.setdefault('user_question', "")
    st.session_state.setdefault('rag_response', "")


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
                st.error(f"Не удалось установить RAG модель: {e}")
            
            # Load active knowledge bases
            try:
                loaded_count = st.session_state.multi_rag.load_all_active_kbs()
                st.success(f"✅ Загружено активных БЗ: {loaded_count}")
            except Exception as e:
                st.error(f"Ошибка при загрузке активных БЗ: {e}")
            
            # Get available KBs info
            available_kbs = st.session_state.multi_rag.get_available_kbs()
            st.session_state.kb_loaded_count = len(available_kbs)
            st.session_state.loaded_kbs_info = available_kbs
            st.session_state.rag_initialized = True
            
        except Exception as e:
            st.error(f"Ошибка инициализации RAG: {e}")
        finally:
            st.session_state.rag_initializing = False


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


def render_rag_interface():
    """Render RAG interface for Knowledge Base queries"""
    st.title("🤖 AI Assistant - Работа с Базами Знаний")
    
    # System status
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
    
    # RAG query interface
    st.markdown("### 💬 Задайте вопрос по базам знаний")
    
    # Model selection
    col1, col2 = st.columns([2, 1])
    with col1:
        model_options = ['qwen2.5:1.5b', 'qwen3:8b', 'llama3.1:8b']
        selected_model = st.selectbox(
            "Выберите модель для RAG:",
            model_options,
            index=model_options.index(st.session_state.get('rag_assistant_model', 'qwen2.5:1.5b'))
        )
        
        if selected_model != st.session_state.get('rag_assistant_model'):
            st.session_state.rag_assistant_model = selected_model
            if st.session_state.multi_rag:
                try:
                    st.session_state.multi_rag.set_chat_backend("ollama", selected_model)
                    st.success(f"Модель изменена на: {selected_model}")
                except Exception as e:
                    st.error(f"Ошибка смены модели: {e}")
    
    with col2:
        if st.button("🔄 Перезагрузить БЗ"):
            if st.session_state.multi_rag:
                try:
                    loaded_count = st.session_state.multi_rag.load_all_active_kbs()
                    st.success(f"✅ Перезагружено БЗ: {loaded_count}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка перезагрузки БЗ: {e}")
    
    # Question input
    user_question = st.text_area(
        "Введите ваш вопрос:",
        value=st.session_state.get('user_question', ''),
        height=100,
        placeholder="Например: Какие документы есть по спутниковой связи?"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        ask_button = st.button("🔍 Задать вопрос", type="primary")
    
    # Process question
    if ask_button and user_question:
        if not st.session_state.rag_initialized or not st.session_state.multi_rag:
            st.error("RAG система не инициализирована")
        else:
            with st.spinner("Ищу ответ в базах знаний..."):
                try:
                    response = st.session_state.multi_rag.query(user_question)
                    st.session_state.rag_response = response
                    st.session_state.user_question = user_question
                except Exception as e:
                    st.error(f"Ошибка при поиске ответа: {e}")
    
    # Display response
    if st.session_state.get('rag_response'):
        st.markdown("### 📝 Ответ:")
        st.markdown(st.session_state.rag_response)
        
        # Clear response button
        if st.button("🗑️ Очистить ответ"):
            st.session_state.rag_response = ""
            st.session_state.user_question = ""
            st.rerun()


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
    
    # Main interface
    st.sidebar.title(f"👋 {st.session_state.username}")
    st.sidebar.markdown(f"**Роль:** {st.session_state.role}")
    st.sidebar.markdown(f"**Компания:** {st.session_state.company}")
    
    # Render RAG interface
    render_rag_interface()
    
    # Logout button
    if st.sidebar.button("🚪 Выйти"):
        keys_to_clear = [
            'authenticated', 'username', 'role', 'company', 'is_staff',
            'user_question', 'rag_response'
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    main()