#!/usr/bin/env python3
"""
Migration script to transfer knowledge bases from kbs.db to satellite_billing.db
Скрипт миграции для переноса баз знаний из kbs.db в satellite_billing.db
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def migrate_kb_data():
    """Перенос данных о базах знаний из kbs.db в satellite_billing.db"""
    
    # Пути к базам данных
    source_db = Path("data/knowledge_bases/kbs.db")
    target_db = Path("satellite_billing.db")
    
    if not source_db.exists():
        print(f"❌ Исходная база данных не найдена: {source_db}")
        return False
        
    if not target_db.exists():
        print(f"❌ Целевая база данных не найдена: {target_db}")
        return False
    
    print(f"🔄 Начинаем миграцию из {source_db} в {target_db}")
    
    # Подключаемся к базам данных
    source_conn = sqlite3.connect(source_db)
    target_conn = sqlite3.connect(target_db)
    
    try:
        # Создаем таблицы в целевой базе, если их нет
        target_cursor = target_conn.cursor()
        target_cursor.executescript('''
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            category TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_by TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kb_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            file_path TEXT,
            content_type TEXT NOT NULL,
            file_size INTEGER,
            upload_date TEXT NOT NULL,
            processed BOOLEAN DEFAULT 0,
            processing_status TEXT DEFAULT 'pending',
            metadata TEXT,
            image_path TEXT,
            image_description TEXT,
            image_analysis TEXT,
            FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
        );
        
        CREATE TABLE IF NOT EXISTS knowledge_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kb_id INTEGER NOT NULL,
            topic_name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
        );
        ''')
        
        # Получаем данные из исходной базы
        source_cursor = source_conn.cursor()
        
        # Переносим базы знаний
        source_cursor.execute("SELECT * FROM knowledge_bases")
        kb_rows = source_cursor.fetchall()
        
        print(f"📊 Найдено {len(kb_rows)} баз знаний для переноса")
        
        now = datetime.now().isoformat()
        
        for kb_row in kb_rows:
            kb_id, name, description, category, created_at, updated_at, is_active, created_by = kb_row
            
            # Проверяем, есть ли уже такая база знаний
            target_cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (name,))
            existing_kb = target_cursor.fetchone()
            
            if existing_kb:
                print(f"⚠️ База знаний '{name}' уже существует, пропускаем")
                continue
            
            # Вставляем базу знаний
            target_cursor.execute('''
                INSERT INTO knowledge_bases (name, description, category, created_at, updated_at, is_active, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, category, created_at or now, updated_at or now, is_active, created_by or "admin"))
            
            new_kb_id = target_cursor.lastrowid
            print(f"✅ Перенесена база знаний: {name} (новый ID: {new_kb_id})")
        
        # Переносим документы
        source_cursor.execute("SELECT * FROM knowledge_documents")
        doc_rows = source_cursor.fetchall()
        
        print(f"📄 Найдено {len(doc_rows)} документов для переноса")
        
        for doc_row in doc_rows:
            # Получаем структуру таблицы
            source_cursor.execute("PRAGMA table_info(knowledge_documents)")
            columns = [col[1] for col in source_cursor.fetchall()]
            
            # Создаем словарь с данными
            doc_data = dict(zip(columns, doc_row))
            
            # Находим новый ID базы знаний
            target_cursor.execute("SELECT id FROM knowledge_bases WHERE name = (SELECT name FROM knowledge_bases WHERE id = ?)", (doc_data['kb_id'],))
            new_kb_id = target_cursor.fetchone()
            
            if new_kb_id:
                new_kb_id = new_kb_id[0]
                
                # Вставляем документ
                target_cursor.execute('''
                    INSERT INTO knowledge_documents (kb_id, title, file_path, content_type, file_size, upload_date, processed, processing_status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    new_kb_id,
                    doc_data.get('title', ''),
                    doc_data.get('file_path', ''),
                    doc_data.get('content_type', 'text/plain'),
                    doc_data.get('file_size', 0),
                    doc_data.get('upload_date', now),
                    doc_data.get('processed', 0),
                    doc_data.get('processing_status', 'pending'),
                    doc_data.get('metadata', '')
                ))
        
        # Переносим темы
        source_cursor.execute("SELECT * FROM knowledge_topics")
        topic_rows = source_cursor.fetchall()
        
        print(f"🏷️ Найдено {len(topic_rows)} тем для переноса")
        
        for topic_row in topic_rows:
            topic_id, kb_id, topic_name, description, created_at = topic_row
            
            # Находим новый ID базы знаний
            target_cursor.execute("SELECT id FROM knowledge_bases WHERE name = (SELECT name FROM knowledge_bases WHERE id = ?)", (kb_id,))
            new_kb_id = target_cursor.fetchone()
            
            if new_kb_id:
                new_kb_id = new_kb_id[0]
                
                # Вставляем тему
                target_cursor.execute('''
                    INSERT INTO knowledge_topics (kb_id, topic_name, description, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (new_kb_id, topic_name, description, created_at or now))
        
        # Копируем векторные индексы
        source_vector_dir = Path("data/knowledge_bases")
        target_vector_dir = Path("kb_admin/data/knowledge_bases")
        
        if source_vector_dir.exists() and target_vector_dir.exists():
            print("🔄 Копируем векторные индексы...")
            
            for vector_dir in source_vector_dir.glob("vectorstore_*"):
                target_vector_path = target_vector_dir / vector_dir.name
                if not target_vector_path.exists():
                    shutil.copytree(vector_dir, target_vector_path)
                    print(f"✅ Скопирован векторный индекс: {vector_dir.name}")
                else:
                    print(f"⚠️ Векторный индекс уже существует: {vector_dir.name}")
        
        target_conn.commit()
        print("✅ Миграция завершена успешно!")
        
        # Проверяем результат
        target_cursor.execute("SELECT COUNT(*) FROM knowledge_bases")
        kb_count = target_cursor.fetchone()[0]
        target_cursor.execute("SELECT COUNT(*) FROM knowledge_documents")
        doc_count = target_cursor.fetchone()[0]
        
        print(f"📊 Результат миграции:")
        print(f"   - Баз знаний: {kb_count}")
        print(f"   - Документов: {doc_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        target_conn.rollback()
        return False
        
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    migrate_kb_data()


