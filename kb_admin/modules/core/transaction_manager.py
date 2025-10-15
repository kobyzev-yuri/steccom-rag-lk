"""
Transaction Manager - Менеджер транзакций для KB Admin
Обеспечивает атомарность операций с возможностью отката
"""

import sqlite3
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class TransactionManager:
    """Менеджер транзакций для обеспечения атомарности операций"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            from pathlib import Path
            current_dir = Path(__file__).parent
            self.db_path = current_dir.parent.parent / "kbs.db"
        else:
            self.db_path = db_path
        
        self.active_transactions = {}
        self.init_transaction_tables()
    
    def init_transaction_tables(self):
        """Инициализация таблиц для транзакций"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Таблица для отслеживания активных транзакций
        c.execute('''
            CREATE TABLE IF NOT EXISTS active_transactions (
                transaction_id TEXT PRIMARY KEY,
                operation_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Таблица для отслеживания изменений в транзакциях
        c.execute('''
            CREATE TABLE IF NOT EXISTS transaction_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                table_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                record_id TEXT,
                old_data TEXT,
                new_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES active_transactions (transaction_id)
            )
        ''')
        
        # Таблица для отслеживания файловых операций
        c.execute('''
            CREATE TABLE IF NOT EXISTS transaction_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                source_path TEXT,
                target_path TEXT,
                file_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transaction_id) REFERENCES active_transactions (transaction_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def begin_transaction(self, operation_type: str, metadata: Dict = None) -> str:
        """Начало новой транзакции"""
        transaction_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO active_transactions (transaction_id, operation_type, status, metadata)
            VALUES (?, ?, 'active', ?)
        ''', (transaction_id, operation_type, json.dumps(metadata or {})))
        
        conn.commit()
        conn.close()
        
        self.active_transactions[transaction_id] = {
            'operation_type': operation_type,
            'status': 'active',
            'metadata': metadata or {},
            'changes': [],
            'file_operations': []
        }
        
        logger.info(f"Начата транзакция {transaction_id} для операции {operation_type}")
        return transaction_id
    
    def log_database_change(self, transaction_id: str, table_name: str, 
                           operation: str, record_id: str = None, 
                           old_data: Dict = None, new_data: Dict = None):
        """Логирование изменения в базе данных"""
        if transaction_id not in self.active_transactions:
            raise ValueError(f"Транзакция {transaction_id} не найдена")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO transaction_changes 
            (transaction_id, table_name, operation, record_id, old_data, new_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            transaction_id, table_name, operation, record_id,
            json.dumps(old_data) if old_data else None,
            json.dumps(new_data) if new_data else None
        ))
        
        conn.commit()
        conn.close()
        
        # Сохраняем в памяти для быстрого доступа
        self.active_transactions[transaction_id]['changes'].append({
            'table_name': table_name,
            'operation': operation,
            'record_id': record_id,
            'old_data': old_data,
            'new_data': new_data
        })
    
    def log_file_operation(self, transaction_id: str, operation: str, 
                          source_path: str = None, target_path: str = None):
        """Логирование файловой операции"""
        if transaction_id not in self.active_transactions:
            raise ValueError(f"Транзакция {transaction_id} не найдена")
        
        # Вычисляем хеш файла если он существует
        file_hash = None
        file_path = Path(source_path) if source_path else Path(target_path)
        if file_path.exists():
            file_hash = self._calculate_file_hash(file_path)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO transaction_files 
            (transaction_id, operation, source_path, target_path, file_hash)
            VALUES (?, ?, ?, ?, ?)
        ''', (transaction_id, operation, source_path, target_path, file_hash))
        
        conn.commit()
        conn.close()
        
        # Сохраняем в памяти
        self.active_transactions[transaction_id]['file_operations'].append({
            'operation': operation,
            'source_path': source_path,
            'target_path': target_path,
            'file_hash': file_hash
        })
    
    def commit_transaction(self, transaction_id: str) -> bool:
        """Подтверждение транзакции"""
        if transaction_id not in self.active_transactions:
            raise ValueError(f"Транзакция {transaction_id} не найдена")
        
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Обновляем статус транзакции
            c.execute('''
                UPDATE active_transactions 
                SET status = 'committed' 
                WHERE transaction_id = ?
            ''', (transaction_id,))
            
            conn.commit()
            conn.close()
            
            # Удаляем из активных транзакций
            del self.active_transactions[transaction_id]
            
            logger.info(f"Транзакция {transaction_id} успешно подтверждена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подтверждения транзакции {transaction_id}: {e}")
            return False
    
    def rollback_transaction(self, transaction_id: str) -> bool:
        """Откат транзакции"""
        if transaction_id not in self.active_transactions:
            # Попробуем найти в базе данных
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('SELECT * FROM active_transactions WHERE transaction_id = ?', (transaction_id,))
            if not c.fetchone():
                conn.close()
                raise ValueError(f"Транзакция {transaction_id} не найдена")
            conn.close()
        
        try:
            logger.info(f"Начинаем откат транзакции {transaction_id}")
            
            # Откатываем файловые операции
            self._rollback_file_operations(transaction_id)
            
            # Откатываем изменения в базе данных
            self._rollback_database_changes(transaction_id)
            
            # Обновляем статус транзакции
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                UPDATE active_transactions 
                SET status = 'rolled_back' 
                WHERE transaction_id = ?
            ''', (transaction_id,))
            conn.commit()
            conn.close()
            
            # Удаляем из активных транзакций
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
            
            logger.info(f"Транзакция {transaction_id} успешно откачена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отката транзакции {transaction_id}: {e}")
            return False
    
    def _rollback_file_operations(self, transaction_id: str):
        """Откат файловых операций"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM transaction_files 
            WHERE transaction_id = ? 
            ORDER BY id DESC
        ''', (transaction_id,))
        
        file_operations = c.fetchall()
        conn.close()
        
        for op in file_operations:
            operation = op[2]  # operation
            source_path = op[3]  # source_path
            target_path = op[4]  # target_path
            
            try:
                if operation == 'move':
                    # Откатываем перемещение: возвращаем файл обратно
                    if target_path and Path(target_path).exists():
                        shutil.move(target_path, source_path)
                        logger.info(f"Откат перемещения: {target_path} -> {source_path}")
                
                elif operation == 'copy':
                    # Откатываем копирование: удаляем скопированный файл
                    if target_path and Path(target_path).exists():
                        Path(target_path).unlink()
                        logger.info(f"Откат копирования: удален {target_path}")
                
                elif operation == 'delete':
                    # Откатываем удаление: восстанавливаем файл из архива
                    if source_path and target_path:
                        if Path(target_path).exists():
                            shutil.move(target_path, source_path)
                            logger.info(f"Откат удаления: восстановлен {source_path}")
                
            except Exception as e:
                logger.error(f"Ошибка отката файловой операции {operation}: {e}")
    
    def _rollback_database_changes(self, transaction_id: str):
        """Откат изменений в базе данных"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM transaction_changes 
            WHERE transaction_id = ? 
            ORDER BY id DESC
        ''', (transaction_id,))
        
        changes = c.fetchall()
        
        for change in changes:
            table_name = change[2]  # table_name
            operation = change[3]  # operation
            record_id = change[4]  # record_id
            old_data = json.loads(change[5]) if change[5] else None  # old_data
            new_data = json.loads(change[6]) if change[6] else None  # new_data
            
            try:
                if operation == 'INSERT':
                    # Откатываем вставку: удаляем запись
                    if record_id:
                        c.execute(f'DELETE FROM {table_name} WHERE id = ?', (record_id,))
                        logger.info(f"Откат INSERT: удалена запись {record_id} из {table_name}")
                
                elif operation == 'UPDATE':
                    # Откатываем обновление: восстанавливаем старые данные
                    if old_data and record_id:
                        set_clause = ', '.join([f"{k} = ?" for k in old_data.keys()])
                        values = list(old_data.values()) + [record_id]
                        c.execute(f'UPDATE {table_name} SET {set_clause} WHERE id = ?', values)
                        logger.info(f"Откат UPDATE: восстановлена запись {record_id} в {table_name}")
                
                elif operation == 'DELETE':
                    # Откатываем удаление: восстанавливаем запись
                    if old_data:
                        columns = ', '.join(old_data.keys())
                        placeholders = ', '.join(['?' for _ in old_data.keys()])
                        values = list(old_data.values())
                        c.execute(f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})', values)
                        logger.info(f"Откат DELETE: восстановлена запись в {table_name}")
                
            except Exception as e:
                logger.error(f"Ошибка отката изменения БД {operation} в {table_name}: {e}")
        
        conn.commit()
        conn.close()
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Вычисление хеша файла"""
        import hashlib
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_transaction_status(self, transaction_id: str) -> Dict:
        """Получение статуса транзакции"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT transaction_id, operation_type, status, created_at, metadata
            FROM active_transactions 
            WHERE transaction_id = ?
        ''', (transaction_id,))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'transaction_id': result[0],
                'operation_type': result[1],
                'status': result[2],
                'created_at': result[3],
                'metadata': json.loads(result[4]) if result[4] else {}
            }
        return None
    
    def cleanup_old_transactions(self, days_old: int = 7):
        """Очистка старых транзакций"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Удаляем старые транзакции и связанные данные
        c.execute('''
            DELETE FROM transaction_files 
            WHERE transaction_id IN (
                SELECT transaction_id FROM active_transactions 
                WHERE created_at < datetime('now', '-{} days')
            )
        '''.format(days_old))
        
        c.execute('''
            DELETE FROM transaction_changes 
            WHERE transaction_id IN (
                SELECT transaction_id FROM active_transactions 
                WHERE created_at < datetime('now', '-{} days')
            )
        '''.format(days_old))
        
        c.execute('''
            DELETE FROM active_transactions 
            WHERE created_at < datetime('now', '-{} days')
        '''.format(days_old))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Очищены транзакции старше {days_old} дней")
