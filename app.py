"""
Satellite Billing System - Main Application
Refactored version with modular structure
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
import hashlib
from openai import OpenAI
# Optional import for RAGHelper
try:
    from modules.rag.rag_helper import RAGHelper
    RAG_HELPER_AVAILABLE = True
except ImportError:
    RAG_HELPER_AVAILABLE = False
    print("⚠️ RAGHelper недоступен: langchain_huggingface не установлен")
import os
import sys
import plotly.express as px
import plotly.graph_objects as go

# Import our custom modules
from modules.core import init_db, verify_login, _generate_quick_question, QUICK_QUESTIONS
from modules.ui import render_user_view, render_staff_view

# Initialize OpenAI client
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def initialize_session_state():
    """Initialize session state variables safely"""
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
    st.session_state.setdefault('rag_helper', None)
    st.session_state.setdefault('multi_rag', None)
    st.session_state.setdefault('kb_loaded_count', 0)
    st.session_state.setdefault('loaded_kbs_info', [])


def initialize_rag_system():
    """Initialize RAG system safely"""
    print(f"🔍 DEBUG: initialize_rag_system вызвана, rag_initialized = {st.session_state.rag_initialized}")
    
    if not st.session_state.rag_initialized:
        try:
            print("🔍 DEBUG: Начинаем инициализацию RAG системы...")
            print(f"🔍 DEBUG: RAG_HELPER_AVAILABLE = {RAG_HELPER_AVAILABLE}")
            
            # Initialize RAG helper only if available
            if RAG_HELPER_AVAILABLE:
                print("🔍 DEBUG: RAGHelper доступен, инициализируем...")
                st.session_state.rag_helper = RAGHelper()
                st.session_state.rag_initialized = True
                print("✅ RAGHelper инициализирован")
            else:
                st.session_state.rag_helper = None
                st.session_state.rag_initialized = False
                print("⚠️ RAGHelper недоступен")
            
            # Try to initialize multi-KB RAG if available
            try:
                print("🔍 DEBUG: Пытаемся импортировать MultiKBRAG...")
                print("🔍 DEBUG: Путь к модулю: modules.rag.multi_kb_rag")
                
                # Проверяем, существует ли файл
                import os
                module_path = "modules/rag/multi_kb_rag.py"
                if os.path.exists(module_path):
                    print(f"🔍 DEBUG: Файл {module_path} существует")
                else:
                    print(f"❌ DEBUG: Файл {module_path} НЕ существует!")
                
                from modules.rag.multi_kb_rag import MultiKBRAG
                print("🔍 DEBUG: MultiKBRAG импортирован успешно, создаем экземпляр...")
                st.session_state.multi_rag = MultiKBRAG()
                
                # Load available knowledge bases
                print("🔍 DEBUG: Загружаем базы знаний...")
                available_kbs = st.session_state.multi_rag.get_available_kbs()
                st.session_state.kb_loaded_count = len(available_kbs)
                st.session_state.loaded_kbs_info = available_kbs
                print(f"✅ Multi-KB RAG инициализирован: {len(available_kbs)} БЗ")
                
            except ImportError as e:
                print(f"❌ DEBUG: ImportError при импорте MultiKBRAG: {e}")
                print(f"🔍 DEBUG: Тип ошибки: {type(e)}")
                st.session_state.multi_rag = None
                st.session_state.kb_loaded_count = 0
                st.session_state.loaded_kbs_info = []
                print(f"⚠️ Multi-KB RAG недоступен: {e}")
            except Exception as e:
                print(f"❌ DEBUG: Exception при инициализации MultiKBRAG: {e}")
                print(f"🔍 DEBUG: Тип ошибки: {type(e)}")
                st.session_state.multi_rag = None
                st.session_state.kb_loaded_count = 0
                st.session_state.loaded_kbs_info = []
                print(f"⚠️ Multi-KB RAG недоступен: {e}")
                
        except Exception as e:
            print(f"❌ DEBUG: Общая ошибка инициализации RAG: {e}")
            print(f"🔍 DEBUG: Тип ошибки: {type(e)}")
            st.session_state.rag_initialized = False
            st.session_state.rag_helper = None
            st.session_state.multi_rag = None
            print(f"❌ Ошибка инициализации RAG: {e}")
    else:
        print("🔍 DEBUG: RAG система уже инициализирована, пропускаем")


def login_page():
    """Render login page"""
    st.title("🛰️ СТЭККОМ - Система спутниковой связи")
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


def main():
    """Main application function"""
    # Initialize database
    init_db()
    
    # Initialize session state
    initialize_session_state()
    
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
            ["🏠 Личный кабинет", "🔧 Админ-панель"],
            key="staff_view_choice"
        )
        
        if view_choice == "🏠 Личный кабинет":
            render_user_view()
        else:
            render_staff_view()
    else:
        # Regular user view
        render_user_view()
    
    # Logout button
    if st.sidebar.button("🚪 Выйти"):
        # Clear only authentication-related session state
        auth_keys = ['authenticated', 'username', 'role', 'company', 'is_staff']
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]
        # Don't use st.rerun() to avoid cache issues
        st.rerun()


if __name__ == "__main__":
    main()
