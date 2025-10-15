"""
Knowledge Base Management Module
Управление базами знаний для оператора спутниковой связи
"""

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd

class KnowledgeBaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Используем абсолютный путь к общей БД
            current_dir = Path(__file__).parent
            self.db_path = current_dir.parent.parent / "kbs.db"
        else:
            self.db_path = db_path
        self.init_knowledge_tables()
    
    def init_knowledge_tables(self):
        """Initialize knowledge base management tables"""
        conn = sqlite3.connect(self.db_path)
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
        
        CREATE TABLE IF NOT EXISTS knowledge_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kb_id INTEGER NOT NULL,
            doc_id INTEGER,
            image_path TEXT NOT NULL,
            image_name TEXT NOT NULL,
            image_description TEXT,
            image_analysis TEXT,
            llava_analysis TEXT,
            image_type TEXT DEFAULT 'extracted',
            upload_date TEXT NOT NULL,
            processed BOOLEAN DEFAULT 0,
            metadata TEXT,
            FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id),
            FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id)
        );
        ''')
        
        conn.commit()
        conn.close()
    
    def create_knowledge_base(self, name: str, description: str, category: str, created_by: str) -> int:
        """Create a new knowledge base"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        c.execute('''
            INSERT INTO knowledge_bases (name, description, category, created_at, updated_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, category, now, now, created_by))
        
        kb_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return kb_id
    
    def get_knowledge_bases(self, active_only: bool = True) -> List[Dict]:
        """Get list of knowledge bases"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        query = "SELECT * FROM knowledge_bases"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY updated_at DESC"
        
        c.execute(query)
        columns = [description[0] for description in c.description]
        results = [dict(zip(columns, row)) for row in c.fetchall()]
        
        conn.close()
        return results
    
    def get_knowledge_base(self, kb_id: int) -> Optional[Dict]:
        """Get specific knowledge base"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT * FROM knowledge_bases WHERE id = ?", (kb_id,))
        row = c.fetchone()
        
        if row:
            columns = [description[0] for description in c.description]
            result = dict(zip(columns, row))
        else:
            result = None
        
        conn.close()
        return result
    
    def update_knowledge_base(self, kb_id: int, **kwargs) -> bool:
        """Update knowledge base"""
        if not kwargs:
            return False
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Add updated_at timestamp
        kwargs['updated_at'] = datetime.now().isoformat()
        
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [kb_id]
        
        c.execute(f"UPDATE knowledge_bases SET {set_clause} WHERE id = ?", values)
        success = c.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
    
    def delete_knowledge_base(self, kb_id: int) -> bool:
        """Soft delete knowledge base"""
        return self.update_knowledge_base(kb_id, is_active=False)
    
    def add_document(self, kb_id: int, title: str, file_path: str, content_type: str, 
                    file_size: int, metadata: Dict = None, processed: bool = True) -> int:
        """Add document to knowledge base"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        c.execute('''
            INSERT INTO knowledge_documents (kb_id, title, file_path, content_type, 
                                           file_size, upload_date, processed, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (kb_id, title, file_path, content_type, file_size, now, processed, metadata_json))
        
        doc_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return doc_id
    
    def get_documents(self, kb_id: int) -> List[Dict]:
        """Get documents for knowledge base"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM knowledge_documents 
            WHERE kb_id = ? 
            ORDER BY upload_date DESC
        ''', (kb_id,))
        
        columns = [description[0] for description in c.description]
        results = [dict(zip(columns, row)) for row in c.fetchall()]
        
        conn.close()
        return results
    
    def update_document_status(self, doc_id: int, processed: bool, status: str) -> bool:
        """Update document processing status"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            UPDATE knowledge_documents 
            SET processed = ?, processing_status = ?
            WHERE id = ?
        ''', (processed, status, doc_id))
        
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_categories(self) -> List[str]:
        """Get available categories"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT DISTINCT category FROM knowledge_bases WHERE is_active = 1")
        categories = [row[0] for row in c.fetchall()]
        
        conn.close()
        return categories
    
    def get_statistics(self) -> Dict:
        """Get knowledge base statistics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Total knowledge bases
        c.execute("SELECT COUNT(*) FROM knowledge_bases WHERE is_active = 1")
        total_kbs = c.fetchone()[0]
        
        # Total documents
        c.execute("SELECT COUNT(*) FROM knowledge_documents")
        total_docs = c.fetchone()[0]
        
        # Processed documents
        c.execute("SELECT COUNT(*) FROM knowledge_documents WHERE processed = 1")
        processed_docs = c.fetchone()[0]
        
        # Documents by category
        c.execute('''
            SELECT kb.category, COUNT(kd.id) as doc_count
            FROM knowledge_bases kb
            LEFT JOIN knowledge_documents kd ON kb.id = kd.kb_id
            WHERE kb.is_active = 1
            GROUP BY kb.category
        ''')
        docs_by_category = dict(c.fetchall())
        
        conn.close()
        
        return {
            'total_knowledge_bases': total_kbs,
            'total_documents': total_docs,
            'processed_documents': processed_docs,
            'processing_rate': (processed_docs / total_docs * 100) if total_docs > 0 else 0,
            'documents_by_category': docs_by_category
        }
    
    def add_image(self, kb_id: int, image_path: str, image_name: str, 
                  doc_id: int = None, image_type: str = 'extracted',
                  image_description: str = None, llava_analysis: str = None,
                  metadata: str = None) -> int:
        """Добавить изображение в базу знаний"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        c.execute('''
            INSERT INTO knowledge_images 
            (kb_id, doc_id, image_path, image_name, image_type, 
             image_description, llava_analysis, upload_date, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (kb_id, doc_id, image_path, image_name, image_type,
              image_description, llava_analysis, now, metadata))
        
        image_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return image_id
    
    def get_images(self, kb_id: int) -> List[Dict]:
        """Получить все изображения из базы знаний"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT id, doc_id, image_path, image_name, image_description, 
                   image_analysis, llava_analysis, image_type, upload_date, 
                   processed, metadata
            FROM knowledge_images 
            WHERE kb_id = ?
            ORDER BY upload_date DESC
        ''', (kb_id,))
        
        images = []
        for row in c.fetchall():
            images.append({
                'id': row[0],
                'doc_id': row[1],
                'image_path': row[2],
                'image_name': row[3],
                'image_description': row[4],
                'image_analysis': row[5],
                'llava_analysis': row[6],
                'image_type': row[7],
                'upload_date': row[8],
                'processed': bool(row[9]),
                'metadata': json.loads(row[10]) if row[10] else {}
            })
        
        conn.close()
        return images
    
    def update_image_analysis(self, image_id: int, image_description: str = None,
                             llava_analysis: str = None, processed: bool = True) -> bool:
        """Обновить анализ изображения"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Строим запрос динамически
        updates = []
        params = []
        
        if image_description is not None:
            updates.append("image_description = ?")
            params.append(image_description)
        
        if llava_analysis is not None:
            updates.append("llava_analysis = ?")
            params.append(llava_analysis)
        
        if processed is not None:
            updates.append("processed = ?")
            params.append(processed)
        
        if updates:
            params.append(image_id)
            query = f"UPDATE knowledge_images SET {', '.join(updates)} WHERE id = ?"
            c.execute(query, params)
            success = c.rowcount > 0
        else:
            success = False
        
        conn.commit()
        conn.close()
        
        return success
    
    def get_image_statistics(self) -> Dict:
        """Получить статистику по изображениям"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Общее количество изображений
        c.execute("SELECT COUNT(*) FROM knowledge_images")
        total_images = c.fetchone()[0]
        
        # Обработанные изображения
        c.execute("SELECT COUNT(*) FROM knowledge_images WHERE processed = 1")
        processed_images = c.fetchone()[0]
        
        # Изображения по типам
        c.execute('''
            SELECT image_type, COUNT(*) as count
            FROM knowledge_images
            GROUP BY image_type
        ''')
        images_by_type = dict(c.fetchall())
        
        # Изображения по базам знаний
        c.execute('''
            SELECT kb.name, COUNT(ki.id) as image_count
            FROM knowledge_bases kb
            LEFT JOIN knowledge_images ki ON kb.id = ki.kb_id
            WHERE kb.is_active = 1
            GROUP BY kb.id, kb.name
        ''')
        images_by_kb = dict(c.fetchall())
        
        conn.close()
        
        return {
            'total_images': total_images,
            'processed_images': processed_images,
            'processing_rate': (processed_images / total_images * 100) if total_images > 0 else 0,
            'images_by_type': images_by_type,
            'images_by_kb': images_by_kb
        }
    
    def export_kb_to_json(self, kb_id: int, output_dir: str = "docs/kb") -> str:
        """Экспорт базы знаний в JSON файл"""
        try:
            # Получаем данные KB
            kb_info = self.get_knowledge_base(kb_id)
            if not kb_info:
                raise ValueError(f"KB с ID {kb_id} не найдена")
            
            # Получаем документы
            documents = self.get_documents(kb_id)
            
            # Получаем изображения
            images = self.get_images(kb_id)
            
            # Создаем структуру для экспорта
            export_data = {
                'kb_info': {
                    'id': kb_info['id'],
                    'name': kb_info['name'],
                    'description': kb_info['description'],
                    'category': kb_info['category'],
                    'created_at': kb_info['created_at'],
                    'updated_at': kb_info['updated_at'],
                    'created_by': kb_info['created_by']
                },
                'documents': [],
                'images': []
            }
            
            # Добавляем документы
            for doc in documents:
                doc_data = {
                    'id': doc['id'],
                    'title': doc['title'],
                    'file_path': doc['file_path'],
                    'content_type': doc['content_type'],
                    'file_size': doc['file_size'],
                    'upload_date': doc['upload_date'],
                    'processed': doc['processed'],
                    'metadata': doc['metadata']
                }
                export_data['documents'].append(doc_data)
            
            # Добавляем изображения
            for img in images:
                img_data = {
                    'id': img['id'],
                    'doc_id': img['doc_id'],
                    'image_path': img['image_path'],
                    'image_name': img['image_name'],
                    'image_description': img['image_description'],
                    'image_analysis': img['image_analysis'],
                    'llava_analysis': img['llava_analysis'],
                    'image_type': img['image_type'],
                    'upload_date': img['upload_date'],
                    'processed': img['processed'],
                    'metadata': img['metadata']
                }
                export_data['images'].append(img_data)
            
            # Создаем имя файла
            safe_name = "".join(c for c in kb_info['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_').lower()
            filename = f"{safe_name}_kb_{kb_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Создаем директорию если не существует
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем JSON
            file_path = output_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return str(file_path)
            
        except Exception as e:
            raise Exception(f"Ошибка экспорта KB в JSON: {e}")
    
    def export_all_kbs_to_json(self, output_dir: str = "docs/kb") -> List[str]:
        """Экспорт всех активных баз знаний в JSON файлы"""
        try:
            kbs = self.get_knowledge_bases(active_only=True)
            exported_files = []
            
            for kb in kbs:
                try:
                    file_path = self.export_kb_to_json(kb['id'], output_dir)
                    exported_files.append(file_path)
                except Exception as e:
                    print(f"Ошибка экспорта KB '{kb['name']}': {e}")
                    continue
            
            return exported_files
            
        except Exception as e:
            raise Exception(f"Ошибка экспорта всех KB: {e}")
    
    def update_knowledge_base_metadata(self, kb_id: int, metadata_key: str, metadata_value: str) -> bool:
        """Обновление метаданных БЗ"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Проверяем существование БЗ
            c.execute("SELECT id FROM knowledge_bases WHERE id = ?", (kb_id,))
            if not c.fetchone():
                conn.close()
                return False
            
            # Создаем таблицу метаданных если не существует
            c.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kb_id INTEGER NOT NULL,
                    metadata_key TEXT NOT NULL,
                    metadata_value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (kb_id) REFERENCES knowledge_bases (id),
                    UNIQUE(kb_id, metadata_key)
                )
            ''')
            
            # Вставляем или обновляем метаданные
            now = datetime.now().isoformat()
            c.execute('''
                INSERT OR REPLACE INTO knowledge_base_metadata 
                (kb_id, metadata_key, metadata_value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (kb_id, metadata_key, metadata_value, now, now))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Ошибка обновления метаданных БЗ: {e}")
            return False
    
    def get_knowledge_base_metadata(self, kb_id: int, metadata_key: str = None) -> Dict[str, str]:
        """Получение метаданных БЗ"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            if metadata_key:
                c.execute('''
                    SELECT metadata_key, metadata_value 
                    FROM knowledge_base_metadata 
                    WHERE kb_id = ? AND metadata_key = ?
                ''', (kb_id, metadata_key))
            else:
                c.execute('''
                    SELECT metadata_key, metadata_value 
                    FROM knowledge_base_metadata 
                    WHERE kb_id = ?
                ''', (kb_id,))
            
            results = c.fetchall()
            conn.close()
            
            return {row[0]: row[1] for row in results}
            
        except Exception as e:
            print(f"Ошибка получения метаданных БЗ: {e}")
            return {}