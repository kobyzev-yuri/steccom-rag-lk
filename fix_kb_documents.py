#!/usr/bin/env python3
"""
Fix KB Documents - Create missing knowledge_documents records
Исправление документов KB - создание недостающих записей knowledge_documents
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def fix_kb_documents():
    """Создать недостающие записи в knowledge_documents"""
    
    db_path = Path("kb_admin/kbs.db")
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Получаем все уникальные doc_id из document_chunks
        c.execute("SELECT DISTINCT doc_id FROM document_chunks ORDER BY doc_id")
        doc_ids = [row[0] for row in c.fetchall()]
        
        print(f"📊 Найдено {len(doc_ids)} уникальных doc_id в document_chunks")
        
        # Получаем существующие doc_id в knowledge_documents
        c.execute("SELECT id FROM knowledge_documents")
        existing_doc_ids = {row[0] for row in c.fetchall()}
        
        print(f"📄 Существующих документов в knowledge_documents: {len(existing_doc_ids)}")
        
        # Создаем недостающие записи
        now = datetime.now().isoformat()
        created_count = 0
        
        for doc_id in doc_ids:
            if doc_id not in existing_doc_ids:
                # Получаем информацию о фрагментах для этого документа
                c.execute("""
                    SELECT content, metadata 
                    FROM document_chunks 
                    WHERE doc_id = ? 
                    ORDER BY chunk_index 
                    LIMIT 1
                """, (doc_id,))
                
                chunk_data = c.fetchone()
                if chunk_data:
                    content, metadata = chunk_data
                    
                    # Парсим метаданные для получения названия
                    import json
                    try:
                        meta_dict = json.loads(metadata) if metadata else {}
                        title = meta_dict.get('title', f'Документ {doc_id}')
                    except:
                        title = f'Документ {doc_id}'
                    
                    # Определяем kb_id на основе doc_id (простая логика)
                    # Можно улучшить, если есть более точная информация
                    if doc_id <= 7:
                        kb_id = 1  # Технические регламенты
                    elif doc_id <= 14:
                        kb_id = 2  # Пользовательские инструкции
                    else:
                        kb_id = 3  # Политики безопасности
                    
                    # Создаем запись в knowledge_documents
                    c.execute('''
                        INSERT INTO knowledge_documents 
                        (id, kb_id, title, file_path, content_type, file_size, upload_date, processed, processing_status, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        doc_id,
                        kb_id,
                        title,
                        f"document_{doc_id}.pdf",  # Заглушка для пути
                        "application/pdf",
                        0,  # Заглушка для размера
                        now,
                        1,  # Обработан
                        "completed",
                        metadata
                    ))
                    
                    created_count += 1
                    print(f"✅ Создана запись для документа {doc_id}: {title} (KB: {kb_id})")
        
        conn.commit()
        print(f"🎉 Создано {created_count} недостающих записей в knowledge_documents")
        
        # Проверяем результат
        c.execute("SELECT COUNT(*) FROM knowledge_documents")
        total_docs = c.fetchone()[0]
        
        c.execute("SELECT kb_id, COUNT(*) FROM knowledge_documents GROUP BY kb_id")
        kb_stats = c.fetchall()
        
        print(f"📊 Итоговая статистика:")
        print(f"   - Всего документов: {total_docs}")
        for kb_id, count in kb_stats:
            c.execute("SELECT name FROM knowledge_bases WHERE id = ?", (kb_id,))
            kb_name = c.fetchone()[0] if c.fetchone() else f"KB {kb_id}"
            print(f"   - {kb_name}: {count} документов")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении документов: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    fix_kb_documents()












