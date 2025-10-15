#!/usr/bin/env python3
"""
Fix Vectorstore Loading - Convert pickle-only vectorstores to FAISS format
Исправление загрузки векторных хранилищ - конвертация pickle-only в формат FAISS
"""

import sys
from pathlib import Path
import pickle
import numpy as np

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

def fix_vectorstore_loading():
    """Исправляем загрузку векторных хранилищ"""
    
    try:
        from modules.rag.multi_kb_rag import MultiKBRAG
        from langchain_community.vectorstores import FAISS
        from sentence_transformers import SentenceTransformer
        
        print("🔄 Инициализация RAG системы...")
        rag = MultiKBRAG()
        
        # Проверяем активные базы знаний
        import sqlite3
        conn = sqlite3.connect(rag.db_path)
        c = conn.cursor()
        
        c.execute("SELECT id, name, is_active FROM knowledge_bases WHERE is_active = 1")
        active_kbs = c.fetchall()
        
        print(f"📚 Активные базы знаний: {len(active_kbs)}")
        
        loaded_count = 0
        
        for kb_id, name, is_active in active_kbs:
            print(f"\n🔄 Обработка KB {kb_id}: {name}")
            
            vectorstore_path = Path(f"data/knowledge_bases/vectorstore_{kb_id}")
            pkl_file = vectorstore_path / "index.pkl"
            faiss_file = vectorstore_path / "index.faiss"
            
            if pkl_file.exists() and not faiss_file.exists():
                print(f"   📄 Найден только pickle файл: {pkl_file}")
                
                try:
                    # Пытаемся загрузить pickle файл
                    with open(pkl_file, 'rb') as f:
                        vectorstore = pickle.load(f)
                    
                    print(f"   ✅ Успешно загружен векторный индекс из pickle")
                    
                    # Сохраняем в формате FAISS
                    vectorstore.save_local(str(vectorstore_path))
                    print(f"   💾 Сохранен в формате FAISS")
                    
                    # Теперь пытаемся загрузить через FAISS
                    vectorstore_loaded = FAISS.load_local(str(vectorstore_path), rag.embeddings, allow_dangerous_deserialization=True)
                    
                    # Добавляем в RAG систему
                    rag.vectorstores[kb_id] = vectorstore_loaded
                    
                    # Получаем метаданные из БД
                    c.execute("SELECT COUNT(*) FROM knowledge_documents WHERE kb_id = ? AND processed = 1", (kb_id,))
                    doc_count = c.fetchone()[0]
                    
                    c.execute("SELECT COUNT(*) FROM document_chunks dc JOIN knowledge_documents kd ON dc.doc_id = kd.id WHERE kd.kb_id = ? AND kd.processed = 1", (kb_id,))
                    chunk_count = c.fetchone()[0]
                    
                    rag.kb_metadata[kb_id] = {
                        'name': name,
                        'description': f'База знаний {name}',
                        'category': 'Импортированная',
                        'doc_count': doc_count,
                        'chunk_count': chunk_count
                    }
                    
                    loaded_count += 1
                    print(f"   ✅ KB {kb_id} успешно загружена в RAG систему")
                    
                except Exception as e:
                    print(f"   ❌ Ошибка при загрузке KB {kb_id}: {e}")
                    
            elif faiss_file.exists():
                print(f"   ✅ FAISS файл уже существует: {faiss_file}")
                
                try:
                    # Загружаем через FAISS
                    vectorstore_loaded = FAISS.load_local(str(vectorstore_path), rag.embeddings, allow_dangerous_deserialization=True)
                    
                    # Добавляем в RAG систему
                    rag.vectorstores[kb_id] = vectorstore_loaded
                    
                    # Получаем метаданные из БД
                    c.execute("SELECT COUNT(*) FROM knowledge_documents WHERE kb_id = ? AND processed = 1", (kb_id,))
                    doc_count = c.fetchone()[0]
                    
                    c.execute("SELECT COUNT(*) FROM document_chunks dc JOIN knowledge_documents kd ON dc.doc_id = kd.id WHERE kd.kb_id = ? AND kd.processed = 1", (kb_id,))
                    chunk_count = c.fetchone()[0]
                    
                    rag.kb_metadata[kb_id] = {
                        'name': name,
                        'description': f'База знаний {name}',
                        'category': 'Импортированная',
                        'doc_count': doc_count,
                        'chunk_count': chunk_count
                    }
                    
                    loaded_count += 1
                    print(f"   ✅ KB {kb_id} успешно загружена в RAG систему")
                    
                except Exception as e:
                    print(f"   ❌ Ошибка при загрузке KB {kb_id}: {e}")
            else:
                print(f"   ⚠️ Векторный индекс не найден: {vectorstore_path}")
        
        conn.close()
        
        print(f"\n📊 Результат:")
        print(f"   - Загружено баз знаний: {loaded_count}")
        print(f"   - Векторных хранилищ: {len(rag.vectorstores)}")
        print(f"   - Метаданных: {len(rag.kb_metadata)}")
        
        if loaded_count > 0:
            print("✅ RAG система успешно загружена!")
            return True
        else:
            print("❌ RAG система не загружена!")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении загрузки: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_vectorstore_loading()












