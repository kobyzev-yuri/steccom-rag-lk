#!/usr/bin/env python3
"""
Test RAG Status - Check RAG system status in the interface
Проверка статуса RAG системы в интерфейсе
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

def test_rag_status():
    """Проверяем статус RAG системы"""
    
    try:
        from modules.rag.multi_kb_rag import MultiKBRAG
        
        print("🔄 Инициализация RAG системы...")
        rag = MultiKBRAG()
        
        # Проверяем статус
        print(f"📊 Векторные хранилища: {len(rag.vectorstores)}")
        print(f"📊 Метаданные: {len(rag.kb_metadata)}")
        
        # Определяем статус как в интерфейсе
        rag_status = "🟢 Активна" if hasattr(rag, 'vectorstores') and len(rag.vectorstores) > 0 else "🔴 Неактивна"
        print(f"📊 Статус RAG системы: {rag_status}")
        
        if rag.vectorstores:
            print("✅ RAG система активна!")
            for kb_id, vectorstore in rag.vectorstores.items():
                print(f"   - KB {kb_id}: {type(vectorstore)}")
        else:
            print("❌ RAG система неактивна!")
            
            # Пытаемся загрузить базы знаний
            print("🔄 Попытка загрузки баз знаний...")
            loaded_count = rag.load_all_active_kbs()
            print(f"📊 Загружено: {loaded_count}")
            
            if loaded_count > 0:
                print("✅ Базы знаний загружены!")
                rag_status = "🟢 Активна" if len(rag.vectorstores) > 0 else "🔴 Неактивна"
                print(f"📊 Новый статус: {rag_status}")
        
        return len(rag.vectorstores) > 0
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_status()
    if success:
        print("✅ RAG система работает!")
    else:
        print("❌ RAG система не работает!")












