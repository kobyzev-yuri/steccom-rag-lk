#!/usr/bin/env python3
"""
Test Streamlit RAG - Check RAG initialization in Streamlit context
Проверка инициализации RAG в контексте Streamlit
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

def test_streamlit_rag():
    """Проверяем инициализацию RAG в контексте Streamlit"""
    
    try:
        from modules.rag.multi_kb_rag import MultiKBRAG
        
        print("🔄 Инициализация RAG системы (как в Streamlit)...")
        print(f"📁 Текущая рабочая директория: {Path.cwd()}")
        
        rag = MultiKBRAG()
        
        print(f"📊 Векторные хранилища: {len(rag.vectorstores)}")
        print(f"📊 Метаданные: {len(rag.kb_metadata)}")
        
        # Проверяем статус как в интерфейсе
        rag_status = "🟢 Активна" if hasattr(rag, 'vectorstores') and len(rag.vectorstores) > 0 else "🔴 Неактивна"
        print(f"📊 Статус RAG системы: {rag_status}")
        
        if rag.vectorstores:
            print("✅ RAG система активна!")
            for kb_id, vectorstore in rag.vectorstores.items():
                print(f"   - KB {kb_id}: {type(vectorstore)}")
        else:
            print("❌ RAG система неактивна!")
            
            # Попробуем загрузить вручную
            print("🔄 Попытка ручной загрузки...")
            loaded_count = rag.load_all_active_kbs()
            print(f"📊 Загружено: {loaded_count}")
            
            if loaded_count > 0:
                rag_status = "🟢 Активна" if len(rag.vectorstores) > 0 else "🔴 Неактивна"
                print(f"📊 Новый статус: {rag_status}")
        
        return len(rag.vectorstores) > 0
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_streamlit_rag()
    if success:
        print("✅ RAG система работает в контексте Streamlit!")
    else:
        print("❌ RAG система не работает в контексте Streamlit!")












