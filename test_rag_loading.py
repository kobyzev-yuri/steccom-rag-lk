#!/usr/bin/env python3
"""
Test RAG Loading - Debug script to test RAG system loading
Тест загрузки RAG - скрипт для отладки загрузки RAG системы
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

def test_rag_loading():
    """Тестируем загрузку RAG системы"""
    
    try:
        from modules.rag.multi_kb_rag import MultiKBRAG
        
        print("🔄 Инициализация RAG системы...")
        rag = MultiKBRAG()
        
        print(f"📊 Путь к БД: {rag.db_path}")
        print(f"📊 Путь к векторным индексам: {Path('data/knowledge_bases')}")
        
        # Проверяем активные базы знаний
        import sqlite3
        conn = sqlite3.connect(rag.db_path)
        c = conn.cursor()
        
        c.execute("SELECT id, name, is_active FROM knowledge_bases WHERE is_active = 1")
        active_kbs = c.fetchall()
        
        print(f"📚 Активные базы знаний: {len(active_kbs)}")
        for kb_id, name, is_active in active_kbs:
            print(f"   - ID {kb_id}: {name}")
            
            # Проверяем существование векторного индекса
            vectorstore_path = Path(f"data/knowledge_bases/vectorstore_{kb_id}")
            if vectorstore_path.exists():
                print(f"     ✅ Векторный индекс найден: {vectorstore_path}")
            else:
                print(f"     ❌ Векторный индекс не найден: {vectorstore_path}")
        
        conn.close()
        
        # Пытаемся загрузить базы знаний
        print("\n🔄 Попытка загрузки активных баз знаний...")
        loaded_count = rag.load_all_active_kbs()
        print(f"📊 Загружено баз знаний: {loaded_count}")
        
        # Проверяем загруженные векторные хранилища
        print(f"📊 Загруженные векторные хранилища: {len(rag.vectorstores)}")
        for kb_id, vectorstore in rag.vectorstores.items():
            print(f"   - KB {kb_id}: {type(vectorstore)}")
        
        # Проверяем метаданные
        print(f"📊 Метаданные баз знаний: {len(rag.kb_metadata)}")
        for kb_id, metadata in rag.kb_metadata.items():
            print(f"   - KB {kb_id}: {metadata}")
        
        return loaded_count > 0
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании RAG: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_rag_loading()
    if success:
        print("✅ RAG система успешно загружена!")
    else:
        print("❌ RAG система не загружена!")












