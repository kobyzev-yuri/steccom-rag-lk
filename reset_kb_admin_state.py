#!/usr/bin/env python3
"""
Скрипт для сброса состояния KB Admin
"""

import streamlit as st
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append('kb_admin/modules')

def reset_session_state():
    """Сбрасываем состояние session_state"""
    print("🧹 Сбрасываем состояние KB Admin...")
    
    # Список ключей для очистки
    keys_to_clear = [
        'analysis_in_progress',
        'analysis_results', 
        'selected_files',
        'doc_status',
        'show_save_dialog',
        'pending_kb_params',
        'last_saved_selection',
        'show_category_kbs',
        'show_rename_dialog',
        'original_kb_name',
        'original_kb_category', 
        'original_kb_description'
    ]
    
    # Очищаем основные ключи
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            print(f"✅ Очищен ключ: {key}")
    
    # Очищаем ключи выбора документов
    keys_to_clear_patterns = [
        'selected_doc_',
        'select_doc_',
        'select_img_',
        'show_full_text_',
        'saved_text_',
        'edit_text_',
        'analyze_new_'
    ]
    
    keys_to_remove = []
    for key in st.session_state.keys():
        for pattern in keys_to_clear_patterns:
            if key.startswith(pattern):
                keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]
        print(f"✅ Очищен ключ: {key}")
    
    print(f"🎉 Состояние KB Admin сброшено! Очищено {len(keys_to_clear) + len(keys_to_remove)} ключей")

if __name__ == "__main__":
    # Инициализируем пустое session_state
    if not hasattr(st, 'session_state'):
        st.session_state = {}
    
    reset_session_state()
    print("✅ Готово! Теперь можно перезапустить KB Admin и начать анализ заново.")
