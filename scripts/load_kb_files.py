#!/usr/bin/env python3
"""
Скрипт для загрузки KB файлов в RAG систему
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.append(str(Path(__file__).parent.parent))

def load_kb_files_to_rag():
    """Загружает KB файлы из docs/kb/ в RAG систему"""
    
    # Пути
    kb_dir = Path("docs/kb")
    rag_db_path = "data/knowledge_bases/kbs.db"
    
    if not kb_dir.exists():
        print(f"❌ Папка {kb_dir} не найдена")
        return False
    
    if not Path(rag_db_path).exists():
        print(f"❌ База данных RAG {rag_db_path} не найдена")
        return False
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(rag_db_path)
    c = conn.cursor()
    
    try:
        # Получаем список KB
        c.execute("SELECT id, name FROM knowledge_bases WHERE is_active = 1")
        kbs = c.fetchall()
        
        if not kbs:
            print("❌ Нет активных баз знаний")
            return False
        
        print(f"📚 Найдено {len(kbs)} активных баз знаний:")
        for kb_id, kb_name in kbs:
            print(f"  - {kb_id}: {kb_name}")
        
        # Очищаем существующие документы
        c.execute("DELETE FROM knowledge_documents")
        print("🧹 Очищены существующие документы")
        
        # Загружаем KB файлы
        kb_files = list(kb_dir.glob("*.json"))
        print(f"📄 Найдено {len(kb_files)} KB файлов")
        
        loaded_count = 0
        
        for kb_file in kb_files:
            print(f"\n📖 Обрабатываем {kb_file.name}...")
            
            try:
                # Читаем KB файл
                with open(kb_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                
                # Определяем категорию KB на основе имени файла
                category = "Пользовательские инструкции"  # по умолчанию
                if "legacy_reglament" in kb_file.name:
                    category = "Технические регламенты"
                elif "ui_" in kb_file.name:
                    category = "Пользовательские инструкции"
                
                # Находим соответствующую KB в базе данных
                kb_id = None
                for db_kb_id, db_kb_name in kbs:
                    if category in db_kb_name:
                        kb_id = db_kb_id
                        break
                
                if not kb_id:
                    print(f"  ⚠️  Не найдена подходящая KB для категории {category}")
                    continue
                
                # Создаем документ в базе данных
                title = f"KB: {kb_file.stem}"
                content = json.dumps(kb_data, ensure_ascii=False, indent=2)
                
                c.execute("""
                    INSERT INTO knowledge_documents 
                    (kb_id, title, file_path, content_type, file_size, upload_date, processed, processing_status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    kb_id,
                    title,
                    str(kb_file),
                    "application/json",
                    len(content),
                    "2025-01-20T14:00:00",
                    1,  # processed
                    "completed",
                    json.dumps({"source": "kb_file", "original_file": str(kb_file)})
                ))
                
                # Создаем чанки для документа
                doc_id = c.lastrowid
                
                # Разбиваем контент на чанки
                chunk_size = 1000
                chunks = []
                
                for i, item in enumerate(kb_data):
                    if isinstance(item, dict):
                        chunk_content = json.dumps(item, ensure_ascii=False)
                        if len(chunk_content) > chunk_size:
                            # Разбиваем большой чанк
                            for j in range(0, len(chunk_content), chunk_size):
                                chunk = chunk_content[j:j+chunk_size]
                                chunks.append({
                                    'content': chunk,
                                    'metadata': {
                                        'doc_id': doc_id,
                                        'chunk_index': len(chunks),
                                        'item_index': i,
                                        'title': item.get('title', f'Item {i}')
                                    }
                                })
                        else:
                            chunks.append({
                                'content': chunk_content,
                                'metadata': {
                                    'doc_id': doc_id,
                                    'chunk_index': len(chunks),
                                    'item_index': i,
                                    'title': item.get('title', f'Item {i}')
                                }
                            })
                
                # Сохраняем чанки
                for chunk in chunks:
                    c.execute("""
                        INSERT INTO document_chunks 
                        (doc_id, chunk_index, content, metadata)
                        VALUES (?, ?, ?, ?)
                    """, (
                        doc_id,
                        chunk['metadata']['chunk_index'],
                        chunk['content'],
                        json.dumps(chunk['metadata'])
                    ))
                
                print(f"  ✅ Загружено: {title} ({len(chunks)} чанков)")
                loaded_count += 1
                
            except Exception as e:
                print(f"  ❌ Ошибка при обработке {kb_file.name}: {e}")
                continue
        
        # Сохраняем изменения
        conn.commit()
        
        print(f"\n🎉 Успешно загружено {loaded_count} KB файлов в RAG систему!")
        
        # Показываем статистику
        c.execute("SELECT COUNT(*) FROM knowledge_documents")
        doc_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM document_chunks")
        chunk_count = c.fetchone()[0]
        
        print(f"📊 Статистика:")
        print(f"  - Документов: {doc_count}")
        print(f"  - Чанков: {chunk_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Загрузка KB файлов в RAG систему...")
    success = load_kb_files_to_rag()
    
    if success:
        print("\n✅ Загрузка завершена успешно!")
        print("Теперь можно использовать RAG систему для поиска по базам знаний.")
    else:
        print("\n❌ Загрузка завершилась с ошибками.")
        sys.exit(1)
