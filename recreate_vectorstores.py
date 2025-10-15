#!/usr/bin/env python3
"""
Recreate Vectorstores - Create new FAISS vectorstores from database documents
Пересоздание векторных хранилищ - создание новых FAISS векторных хранилищ из документов БД
"""

import sys
from pathlib import Path
import sqlite3
import json

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent / "kb_admin"))

def recreate_vectorstores():
    """Пересоздаем векторные хранилища из документов в БД"""
    
    try:
        from langchain_community.vectorstores import FAISS
        from langchain.schema import Document
        from langchain_huggingface import HuggingFaceEmbeddings
        
        print("🔄 Пересоздание векторных хранилищ...")
        
        # Инициализируем embeddings
        embedding_model = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-base",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Подключаемся к базе данных
        db_path = "kb_admin/kbs.db"
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Получаем активные базы знаний
        c.execute("SELECT id, name, is_active FROM knowledge_bases WHERE is_active = 1")
        active_kbs = c.fetchall()
        
        print(f"📚 Активные базы знаний: {len(active_kbs)}")
        
        created_count = 0
        
        for kb_id, name, is_active in active_kbs:
            print(f"\n🔄 Обработка KB {kb_id}: {name}")
            
            # Получаем документы для этой базы знаний
            c.execute("""
                SELECT dc.content, dc.metadata, kd.title, kd.file_path
                FROM document_chunks dc
                JOIN knowledge_documents kd ON dc.doc_id = kd.id
                WHERE kd.kb_id = ? AND kd.processed = 1
                ORDER BY dc.chunk_index
            """, (kb_id,))
            
            chunks = c.fetchall()
            
            if not chunks:
                print(f"   ⚠️ Нет документов для KB {kb_id}")
                continue
            
            print(f"   📄 Найдено {len(chunks)} фрагментов документов")
            
            # Создаем документы LangChain
            documents = []
            for i, (content, metadata_json, title, file_path) in enumerate(chunks):
                try:
                    metadata = json.loads(metadata_json) if metadata_json else {}
                except:
                    metadata = {}
                
                # Добавляем дополнительную информацию в метаданные
                metadata.update({
                    'kb_id': kb_id,
                    'kb_name': name,
                    'title': title,
                    'file_path': file_path,
                    'chunk_index': i
                })
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            
            if documents:
                # Создаем векторное хранилище
                vectorstore = FAISS.from_documents(documents, embedding_model)
                
                # Сохраняем в правильном формате
                vectorstore_path = Path(f"kb_admin/data/knowledge_bases/vectorstore_{kb_id}")
                vectorstore_path.mkdir(parents=True, exist_ok=True)
                
                # Удаляем старые файлы
                for old_file in vectorstore_path.glob("*"):
                    old_file.unlink()
                
                # Сохраняем новые файлы
                vectorstore.save_local(str(vectorstore_path))
                
                print(f"   ✅ Создано векторное хранилище: {len(documents)} документов")
                created_count += 1
            else:
                print(f"   ⚠️ Нет документов для создания векторного хранилища")
        
        conn.close()
        
        print(f"\n📊 Результат:")
        print(f"   - Создано векторных хранилищ: {created_count}")
        
        if created_count > 0:
            print("✅ Векторные хранилища пересозданы!")
            return True
        else:
            print("❌ Векторные хранилища не созданы!")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка при пересоздании векторных хранилищ: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    recreate_vectorstores()
