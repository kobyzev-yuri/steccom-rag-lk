#!/usr/bin/env python3
"""
Create FAISS Files - Convert pickle-only vectorstores to FAISS format
Создание файлов FAISS - конвертация pickle-only векторных хранилищ в формат FAISS
"""

import sys
from pathlib import Path
import pickle
import numpy as np

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

def create_faiss_files():
    """Создаем недостающие файлы FAISS"""
    
    try:
        from langchain_community.vectorstores import FAISS
        from sentence_transformers import SentenceTransformer
        
        print("🔄 Создание файлов FAISS...")
        
        # Инициализируем embeddings
        embedding_model = SentenceTransformer("intfloat/multilingual-e5-base")
        
        # Проверяем активные базы знаний
        import sqlite3
        db_path = "kb_admin/kbs.db"
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        c.execute("SELECT id, name, is_active FROM knowledge_bases WHERE is_active = 1")
        active_kbs = c.fetchall()
        
        print(f"📚 Активные базы знаний: {len(active_kbs)}")
        
        created_count = 0
        
        for kb_id, name, is_active in active_kbs:
            print(f"\n🔄 Обработка KB {kb_id}: {name}")
            
            vectorstore_path = Path(f"kb_admin/data/knowledge_bases/vectorstore_{kb_id}")
            pkl_file = vectorstore_path / "index.pkl"
            faiss_file = vectorstore_path / "index.faiss"
            
            if pkl_file.exists() and not faiss_file.exists():
                print(f"   📄 Найден только pickle файл: {pkl_file}")
                
                try:
                    # Пытаемся загрузить pickle файл
                    with open(pkl_file, 'rb') as f:
                        vectorstore = pickle.load(f)
                    
                    print(f"   ✅ Успешно загружен векторный индекс из pickle")
                    
                    # Создаем FAISS-совместимый объект
                    if hasattr(vectorstore, 'docstore') and hasattr(vectorstore, 'index'):
                        # Это уже FAISS объект, просто сохраняем в правильном формате
                        vectorstore.save_local(str(vectorstore_path))
                        print(f"   💾 Сохранен в формате FAISS")
                        created_count += 1
                    else:
                        print(f"   ⚠️ Неизвестный формат векторного хранилища")
                        
                except Exception as e:
                    print(f"   ❌ Ошибка при обработке KB {kb_id}: {e}")
                    
            elif faiss_file.exists():
                print(f"   ✅ FAISS файл уже существует: {faiss_file}")
                created_count += 1
            else:
                print(f"   ⚠️ Векторный индекс не найден: {vectorstore_path}")
        
        conn.close()
        
        print(f"\n📊 Результат:")
        print(f"   - Обработано баз знаний: {created_count}")
        
        if created_count > 0:
            print("✅ Файлы FAISS созданы!")
            return True
        else:
            print("❌ Файлы FAISS не созданы!")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка при создании файлов FAISS: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_faiss_files()












