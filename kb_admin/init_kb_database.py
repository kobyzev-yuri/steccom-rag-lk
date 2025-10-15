#!/usr/bin/env python3
"""
Initialize KB Database for KB Admin
Инициализация базы данных KB для KB Admin
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

def init_kb_database():
    """Инициализация базы данных KB"""
    
    # Путь к общей БД
    db_path = Path(__file__).parent / "kbs.db"
    
    if not db_path.exists():
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Проверяем, есть ли уже KB
        c.execute("SELECT COUNT(*) FROM knowledge_bases")
        kb_count = c.fetchone()[0]
        
        if kb_count > 0:
            print(f"✅ В базе данных уже есть {kb_count} баз знаний")
            return True
        
        # Создаем KB на основе существующих файлов
        kb_files = [
            {
                "name": "Технические регламенты SBD",
                "description": "Регламенты для услуг SBD (Short Burst Data)",
                "category": "Технические регламенты",
                "file": "legacy_reglament_sbd.json"
            },
            {
                "name": "Регламенты GPS трекинга",
                "description": "Регламенты для услуг GPS трекинга",
                "category": "Технические регламенты", 
                "file": "legacy_reglament_gpstrack.json"
            },
            {
                "name": "Регламенты мониторинга",
                "description": "Регламенты для услуг мониторинга",
                "category": "Технические регламенты",
                "file": "legacy_reglament_monitoring.json"
            },
            {
                "name": "Руководство пользователя",
                "description": "Руководство по использованию личного кабинета",
                "category": "Пользовательские инструкции",
                "file": "ui_guide.json"
            },
            {
                "name": "Возможности системы",
                "description": "Описание возможностей личного кабинета",
                "category": "Пользовательские инструкции",
                "file": "ui_capabilities.json"
            },
            {
                "name": "Техническая поддержка",
                "description": "Инструкции по технической поддержке",
                "category": "Техническая поддержка",
                "file": "ui_technical.json"
            },
            {
                "name": "Устранение неполадок",
                "description": "Руководство по устранению неполадок",
                "category": "Техническая поддержка",
                "file": "ui_troubleshooting.json"
            },
            {
                "name": "Примеры использования",
                "description": "Примеры использования системы",
                "category": "Пользовательские инструкции",
                "file": "ui_examples.json"
            },
            {
                "name": "Регламенты SBD (EN)",
                "description": "SBD regulations in English",
                "category": "Технические регламенты",
                "file": "legacy_reglament_sbd_en.json"
            }
        ]
        
        now = datetime.now().isoformat()
        
        for kb_info in kb_files:
            # Создаем KB
            c.execute('''
                INSERT INTO knowledge_bases (name, description, category, created_at, updated_at, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                kb_info["name"],
                kb_info["description"], 
                kb_info["category"],
                now,
                now,
                "admin",
                1
            ))
            
            kb_id = c.lastrowid
            
            # Создаем документ
            file_path = Path(__file__).parent.parent / "docs" / "kb" / kb_info["file"]
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Создаем метаданные
                metadata = {
                    "source": "kb_file",
                    "file": kb_info["file"],
                    "content": content[:1000] + "..." if len(content) > 1000 else content
                }
                
                c.execute('''
                    INSERT INTO knowledge_documents (kb_id, title, file_path, content_type, file_size, upload_date, processed, processing_status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    kb_id,
                    kb_info["name"],
                    str(file_path),
                    "application/json",
                    file_path.stat().st_size,
                    now,
                    1,
                    "completed",
                    json.dumps(metadata, ensure_ascii=False)
                ))
                
                print(f"✅ Создана KB: {kb_info['name']} (ID: {kb_id})")
            else:
                print(f"⚠️ Файл не найден: {file_path}")
        
        conn.commit()
        print(f"🎉 Успешно создано {len(kb_files)} баз знаний!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании KB: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Инициализация базы данных KB для KB Admin...")
    success = init_kb_database()
    if success:
        print("✅ Инициализация завершена успешно!")
    else:
        print("❌ Ошибка инициализации!")
