"""
Document Manager - Менеджер документов
Система отслеживания и управления документами
"""

import streamlit as st
import os
import sqlite3
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

class DocumentManager:
    """Менеджер документов для отслеживания статуса и архивирования"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            from pathlib import Path
            current_dir = Path(__file__).parent
            self.db_path = current_dir.parent.parent / "kbs.db"
        else:
            self.db_path = db_path
        
        # Определяем абсолютные пути относительно корня проекта
        from pathlib import Path
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent
        
        # Базовые пути по умолчанию
        default_upload_dir = project_root / "data" / "uploads"
        default_archive_dir = project_root / "data" / "archive"
        default_processed_dir = project_root / "data" / "processed"
        
        # Переопределение путей через переменные окружения с безопасным откатом на дефолт
        force_local = (os.getenv("STEC_FORCE_LOCAL_DIRS", "false").lower() == "true")
        env_upload_dir = None if force_local else (os.getenv("STEC_UPLOAD_DIR") or os.getenv("UPLOAD_DIR"))
        env_archive_dir = None if force_local else (os.getenv("STEC_ARCHIVE_DIR") or os.getenv("ARCHIVE_DIR"))
        env_processed_dir = None if force_local else (os.getenv("STEC_PROCESSED_DIR") or os.getenv("PROCESSED_DIR"))
        
        def resolve_dir(env_value: str, default_path: Path, label: str) -> Path:
            """Безопасно выбрать директорию. Если env-путь недоступен — вернуть дефолт."""
            try:
                if env_value:
                    candidate = Path(env_value)
                    # Проверяем существование и доступ
                    if candidate.exists() and candidate.is_dir() and os.access(candidate, os.R_OK | os.W_OK | os.X_OK):
                        return candidate
                    else:
                        # Пытаемся создать директорию, если родитель существует
                        try:
                            candidate.mkdir(parents=True, exist_ok=True)
                            if os.access(candidate, os.R_OK | os.W_OK | os.X_OK):
                                return candidate
                        except Exception:
                            pass
                        # Откат на дефолт
                        try:
                            st.warning(f"{label}: путь '{candidate}' недоступен, используем дефолт '{default_path}'")
                        except Exception:
                            pass
                        return default_path
                return default_path
            except Exception:
                # На любой ошибке откатываемся на дефолт
                return default_path
        
        self.upload_dir = resolve_dir(env_upload_dir, default_upload_dir, "UPLOAD_DIR")
        self.archive_dir = resolve_dir(env_archive_dir, default_archive_dir, "ARCHIVE_DIR")
        self.processed_dir = resolve_dir(env_processed_dir, default_processed_dir, "PROCESSED_DIR")
        
        # Создаем необходимые директории
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.init_document_tracking()
    
    def init_document_tracking(self):
        """Инициализация таблиц для отслеживания документов"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        c.executescript('''
        CREATE TABLE IF NOT EXISTS document_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            kb_id INTEGER,
            processed_date TEXT,
            archived_date TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(file_hash)
        );
        
        CREATE INDEX IF NOT EXISTS idx_document_status_file_name ON document_status(file_name);
        CREATE INDEX IF NOT EXISTS idx_document_status_status ON document_status(status);
        CREATE INDEX IF NOT EXISTS idx_document_status_kb_id ON document_status(kb_id);
        ''')
        
        conn.commit()
        conn.close()
    
    def scan_upload_directory(self) -> Dict[str, List[Dict]]:
        """Сканирование директории uploads и определение статуса документов"""
        if not self.upload_dir.exists():
            return {'new': [], 'processed': [], 'unknown': []}
        
        # Получаем все файлы в uploads
        upload_files = list(self.upload_dir.glob("*"))
        
        # Получаем информацию о обработанных документах из БД
        processed_docs = self.get_processed_documents()
        processed_hashes = {doc['file_hash'] for doc in processed_docs if doc['file_hash']}
        
        # Создаем маппинг по названию файла для обработанных документов
        processed_by_name = {}
        
        # Точное сопоставление файлов с документами в БД
        file_to_title_mapping = {
            'reg_gpstrack_14042014.pdf': 'Регламенты GPS трекинга',
            'reg_07032015.pdf': 'Технические регламенты SBD', 
            'reg_monitor_16112013.pdf': 'Регламенты мониторинга',
            'reg_sbd_en.pdf': 'Регламенты SBD (EN)',
            'reg_sbd.pdf': 'Технические регламенты SBD'
        }
        
        for doc in processed_docs:
            if doc['original_filename']:
                processed_by_name[doc['original_filename']] = doc
            
            # Точное сопоставление по нашему маппингу
            for filename, expected_title in file_to_title_mapping.items():
                if doc['title'] == expected_title:
                    processed_by_name[filename] = doc
                    break
            
            # Также пробуем сопоставить по названию в БД (fallback)
            if doc['title']:
                title_lower = doc['title'].lower()
                for upload_file in upload_files:
                    if upload_file.is_file() and upload_file.name not in processed_by_name:
                        file_name_lower = upload_file.name.lower()
                        # Проверяем различные варианты сопоставления
                        if (file_name_lower in title_lower or 
                            title_lower in file_name_lower or
                            self._is_similar_filename(upload_file.name, doc['title'])):
                            processed_by_name[upload_file.name] = doc
        
        # Получаем информацию о документах из таблицы статуса
        status_docs = self.get_document_status_all()
        status_hashes = {doc['file_hash']: doc for doc in status_docs}
        
        result = {
            'new': [],
            'processed': [],
            'unknown': []
        }
        
        for file_path in upload_files:
            if file_path.is_file():
                file_hash = self.calculate_file_hash(file_path)
                file_info = {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'file_size': file_path.stat().st_size,
                    'file_hash': file_hash,
                    'modified_date': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                
                # Проверяем статус
                if file_hash in processed_hashes:
                    # Документ обработан в БЗ (по хешу)
                    file_info['status'] = 'processed'
                    file_info['kb_info'] = next(doc for doc in processed_docs if doc['file_hash'] == file_hash)
                    result['processed'].append(file_info)
                elif file_path.name in processed_by_name:
                    # Документ обработан в БЗ (по названию)
                    file_info['status'] = 'processed'
                    file_info['kb_info'] = processed_by_name[file_path.name]
                    result['processed'].append(file_info)
                elif file_hash in status_hashes:
                    # Документ есть в таблице статуса
                    status_info = status_hashes[file_hash]
                    file_info['status'] = status_info['status']
                    file_info['kb_id'] = status_info.get('kb_id')
                    result[status_info['status']].append(file_info)
                else:
                    # Новый документ
                    file_info['status'] = 'new'
                    result['new'].append(file_info)
        
        return result
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Вычисление хеша файла"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _is_similar_filename(self, filename: str, title: str) -> bool:
        """Проверяет, похожи ли название файла и заголовок документа"""
        filename_lower = filename.lower().replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        title_lower = title.lower()
        
        # Специальные правила сопоставления
        mapping_rules = {
            'reg_gpstrack': 'gps трекинга',
            'reg_monitor': 'мониторинга', 
            'reg_07032015': 'технические регламенты sbd',
            'billmaster': 'биллинг'
        }
        
        # Проверяем специальные правила
        for key, value in mapping_rules.items():
            if key in filename_lower and value in title_lower:
                return True
        
        # Извлекаем ключевые слова
        filename_words = set(filename_lower.split())
        title_words = set(title_lower.split())
        
        # Проверяем пересечение ключевых слов
        common_words = filename_words.intersection(title_words)
        
        # Если есть общие слова или одно содержится в другом
        return (len(common_words) > 0 or 
                filename_lower in title_lower or 
                title_lower in filename_lower)
    
    def get_processed_documents(self) -> List[Dict]:
        """Получение списка обработанных документов из БД"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        c.execute('''
        SELECT kd.title, kd.kb_id, kd.file_path, kd.file_size, kd.metadata
        FROM knowledge_documents kd
        WHERE kd.processed = 1
        ''')
        
        docs = []
        for row in c.fetchall():
            title, kb_id, file_path, file_size, metadata = row
            
            # Извлекаем хеш из метаданных
            file_hash = None
            original_filename = None
            if metadata:
                try:
                    meta = json.loads(metadata)
                    file_hash = meta.get('file_hash')
                    original_filename = meta.get('original_filename')
                except:
                    pass
            
            # Если хеша нет в метаданных, вычисляем по пути
            if not file_hash and file_path:
                try:
                    file_path_obj = Path(file_path)
                    if file_path_obj.exists():
                        file_hash = self.calculate_file_hash(file_path_obj)
                except:
                    pass
            
            docs.append({
                'title': title,
                'kb_id': kb_id,
                'file_path': file_path,
                'file_size': file_size,
                'file_hash': file_hash,
                'original_filename': original_filename
            })
        
        conn.close()
        return docs
    
    def get_document_status_all(self) -> List[Dict]:
        """Получение всех записей о статусе документов"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        c.execute('''
        SELECT file_name, file_path, file_hash, file_size, status, kb_id, 
               processed_date, archived_date, created_at, updated_at
        FROM document_status
        ORDER BY created_at DESC
        ''')
        
        docs = []
        for row in c.fetchall():
            docs.append({
                'file_name': row[0],
                'file_path': row[1],
                'file_hash': row[2],
                'file_size': row[3],
                'status': row[4],
                'kb_id': row[5],
                'processed_date': row[6],
                'archived_date': row[7],
                'created_at': row[8],
                'updated_at': row[9]
            })
        
        conn.close()
        return docs
    
    def update_document_status(self, file_hash: str, status: str, kb_id: int = None):
        """Обновление статуса документа"""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if status == 'processed':
            c.execute('''
            INSERT OR REPLACE INTO document_status 
            (file_hash, status, kb_id, processed_date, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (file_hash, status, kb_id, now, now))
        elif status == 'archived':
            c.execute('''
            UPDATE document_status 
            SET status = ?, archived_date = ?, updated_at = ?
            WHERE file_hash = ?
            ''', (status, now, now, file_hash))
        else:
            c.execute('''
            INSERT OR REPLACE INTO document_status 
            (file_hash, status, updated_at)
            VALUES (?, ?, ?)
            ''', (file_hash, status, now))
        
        conn.commit()
        conn.close()
    
    def register_new_document(self, file_path: Path):
        """Регистрация нового документа"""
        file_hash = self.calculate_file_hash(file_path)
        
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        
        c.execute('''
        INSERT OR IGNORE INTO document_status 
        (file_name, file_path, file_hash, file_size, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'new', ?, ?)
        ''', (file_path.name, str(file_path), file_hash, file_path.stat().st_size, now, now))
        
        conn.commit()
        conn.close()
    
    def archive_document(self, file_path: Path, reason: str = "processed"):
        """Архивирование документа"""
        try:
            # Создаем поддиректорию по дате
            date_dir = self.archive_dir / datetime.now().strftime("%Y-%m-%d")
            date_dir.mkdir(exist_ok=True)
            
            # Перемещаем файл в архив
            archive_path = date_dir / file_path.name
            shutil.move(str(file_path), str(archive_path))
            
            # Обновляем статус
            file_hash = self.calculate_file_hash(archive_path)
            self.update_document_status(file_hash, 'archived')
            
            return True, str(archive_path)
        except Exception as e:
            return False, str(e)
    
    def get_archive_info(self) -> Dict:
        """Получение информации об архиве"""
        if not self.archive_dir.exists():
            return {'total_files': 0, 'total_size': 0, 'dates': []}
        
        total_files = 0
        total_size = 0
        dates = []
        
        for date_dir in self.archive_dir.iterdir():
            if date_dir.is_dir():
                files_in_date = list(date_dir.glob("*"))
                date_size = sum(f.stat().st_size for f in files_in_date if f.is_file())
                
                dates.append({
                    'date': date_dir.name,
                    'files_count': len(files_in_date),
                    'size': date_size
                })
                
                total_files += len(files_in_date)
                total_size += date_size
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'dates': sorted(dates, key=lambda x: x['date'], reverse=True)
        }
    
    def restore_from_archive(self, archive_path: str) -> bool:
        """Восстановление документа из архива"""
        try:
            archive_file = Path(archive_path)
            if not archive_file.exists():
                return False
            
            # Перемещаем обратно в uploads
            restore_path = self.upload_dir / archive_file.name
            shutil.move(str(archive_file), str(restore_path))
            
            # Обновляем статус
            file_hash = self.calculate_file_hash(restore_path)
            self.update_document_status(file_hash, 'new')
            
            return True
        except Exception as e:
            st.error(f"Ошибка восстановления: {e}")
            return False
