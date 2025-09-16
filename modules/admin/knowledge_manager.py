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
    def __init__(self, db_path: str = "satellite_billing.db"):
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
                    file_size: int, metadata: Dict = None) -> int:
        """Add document to knowledge base"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None
        
        c.execute('''
            INSERT INTO knowledge_documents (kb_id, title, file_path, content_type, 
                                           file_size, upload_date, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (kb_id, title, file_path, content_type, file_size, now, metadata_json))
        
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
