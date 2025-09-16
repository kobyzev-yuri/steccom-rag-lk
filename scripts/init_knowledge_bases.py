#!/usr/bin/env python3
"""
Скрипт для инициализации баз знаний
Создает базовые базы знаний для работы RAG системы
"""

import os
import sys
import sqlite3
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from modules.admin.knowledge_manager import KnowledgeBaseManager

def init_knowledge_bases():
    """Инициализация баз знаний"""
    print("🔧 Инициализация баз знаний...")
    
    # Создаем директории
    os.makedirs("data/knowledge_bases", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    
    # Инициализируем менеджер баз знаний
    kb_manager = KnowledgeBaseManager("data/knowledge_bases/kbs.db")
    
    # Создаем базовые базы знаний
    base_kbs = [
        {
            "name": "Технические регламенты",
            "description": "Технические регламенты и стандарты спутниковой связи",
            "category": "Технические регламенты"
        },
        {
            "name": "Пользовательские инструкции", 
            "description": "Инструкции для пользователей системы",
            "category": "Пользовательские инструкции"
        },
        {
            "name": "Политики безопасности",
            "description": "Политики и процедуры безопасности",
            "category": "Политики безопасности"
        }
    ]
    
    for kb_data in base_kbs:
        try:
            kb_id = kb_manager.create_knowledge_base(
                name=kb_data["name"],
                description=kb_data["description"],
                category=kb_data["category"],
                created_by="system"
            )
            print(f"✅ Создана БЗ: {kb_data['name']} (ID: {kb_id})")
        except Exception as e:
            print(f"⚠️ БЗ {kb_data['name']} уже существует или ошибка: {e}")
    
    # Создаем базу данных для Multi-KB RAG
    kb_db_path = "data/knowledge_bases/kbs.db"
    if not os.path.exists(kb_db_path):
        print("🔧 Создание базы данных для Multi-KB RAG...")
        conn = sqlite3.connect(kb_db_path)
        c = conn.cursor()
        
        c.executescript('''
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
            FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
        );
        
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            embedding BLOB,
            FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id)
        );
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Создана база данных: {kb_db_path}")
    else:
        print(f"✅ База данных уже существует: {kb_db_path}")
    
    print("🎉 Инициализация баз знаний завершена!")

if __name__ == "__main__":
    init_knowledge_bases()
