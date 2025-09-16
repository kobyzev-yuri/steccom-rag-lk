"""
Database module for satellite billing system
Contains all database-related functions and queries
"""

import sqlite3
import pandas as pd
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple


def init_db():
    """Initialize database with tables and sample data"""
    conn = sqlite3.connect('satellite_billing.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        company TEXT NOT NULL,
        role TEXT CHECK(role IN ('staff', 'user')) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS service_types (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        unit TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS tariffs (
        id INTEGER PRIMARY KEY,
        service_type_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        price_per_unit REAL NOT NULL,
        monthly_fee REAL NOT NULL DEFAULT 0,
        traffic_limit INTEGER NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (service_type_id) REFERENCES service_types(id)
    );

    CREATE TABLE IF NOT EXISTS agreements (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        tariff_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        status TEXT CHECK(status IN ('active', 'pending', 'terminated')) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (tariff_id) REFERENCES tariffs(id)
    );

    CREATE TABLE IF NOT EXISTS devices (
        imei TEXT PRIMARY KEY,
        user_id INTEGER,
        device_type TEXT NOT NULL,
        model TEXT NOT NULL,
        activated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY,
        imei TEXT NOT NULL,
        service_type_id INTEGER NOT NULL,
        session_start TEXT NOT NULL,
        session_end TEXT NOT NULL,
        usage_amount INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (imei) REFERENCES devices(imei),
        FOREIGN KEY (service_type_id) REFERENCES service_types(id)
    );

    CREATE TABLE IF NOT EXISTS billing_records (
        id INTEGER PRIMARY KEY,
        agreement_id INTEGER,
        imei TEXT NOT NULL,
        service_type_id INTEGER NOT NULL,
        billing_date TEXT NOT NULL,
        usage_amount INTEGER NOT NULL,
        amount REAL NOT NULL,
        paid BOOLEAN NOT NULL DEFAULT 0,
        payment_date TEXT,
        FOREIGN KEY (agreement_id) REFERENCES agreements(id),
        FOREIGN KEY (imei) REFERENCES devices(imei),
        FOREIGN KEY (service_type_id) REFERENCES service_types(id)
    );
    ''')
    
    # Insert sample data only if tables are empty
    if not c.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        _insert_sample_data(c)
    
    # Create knowledge base tables
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


def _insert_sample_data(cursor):
    """Insert sample data into database"""
    # Hash passwords
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    # Insert service types
    cursor.executescript('''
    INSERT OR IGNORE INTO service_types (id, name, unit, description) VALUES 
        (1, 'SBD', 'KB', 'Short Burst Data - спутниковая передача данных'),
        (2, 'VSAT_DATA', 'MB', 'VSAT Data - высокоскоростная передача данных'),
        (3, 'VSAT_VOICE', 'minutes', 'VSAT Voice - спутниковая телефония');
    ''')
    
    # Insert tariffs
    cursor.executescript('''
    INSERT OR IGNORE INTO tariffs (id, service_type_id, name, price_per_unit, monthly_fee, traffic_limit) VALUES 
        (1, 1, 'SBD Basic', 0.05, 50.00, 10000),
        (2, 1, 'SBD Premium', 0.03, 100.00, 50000),
        (3, 2, 'VSAT Data 1GB', 0.10, 200.00, 1024),
        (4, 2, 'VSAT Data 5GB', 0.08, 400.00, 5120),
        (5, 3, 'VSAT Voice 100min', 0.50, 150.00, 100),
        (6, 3, 'VSAT Voice 500min', 0.40, 300.00, 500);
    ''')
    
    # Insert users with IGNORE to avoid conflicts
    cursor.executescript(f'''
    INSERT OR IGNORE INTO users (username, password, company, role) VALUES 
        ('staff1', '{hash_password("staff123")}', 'Admin', 'staff'),
        ('arctic_user', '{hash_password("arctic123")}', 'Arctic Research Station', 'user'),
        ('desert_user', '{hash_password("desert123")}', 'Desert Observatory', 'user');
    ''')
    
    # Get user IDs
    arctic_user_id = cursor.execute("SELECT id FROM users WHERE username = 'arctic_user'").fetchone()[0]
    desert_user_id = cursor.execute("SELECT id FROM users WHERE username = 'desert_user'").fetchone()[0]
    
    # Insert agreements with IGNORE (using tariff_id instead of plan_type)
    cursor.executescript(f'''
    INSERT OR IGNORE INTO agreements (user_id, tariff_id, start_date, end_date, status) VALUES 
        ({arctic_user_id}, 2, '2025-01-01', '2025-12-31', 'active'),
        ({desert_user_id}, 4, '2025-01-01', '2025-12-31', 'active');
    ''')
    
    # Get agreement IDs
    arctic_agreement_id = cursor.execute(f"SELECT id FROM agreements WHERE user_id = {arctic_user_id}").fetchone()[0]
    desert_agreement_id = cursor.execute(f"SELECT id FROM agreements WHERE user_id = {desert_user_id}").fetchone()[0]
    
    # Insert devices with IGNORE
    cursor.executescript(f'''
    INSERT OR IGNORE INTO devices (imei, user_id, device_type, model, activated_at) VALUES 
        ('123456789012345', {arctic_user_id}, 'SBD', 'SAT-100', '2025-01-01'),
        ('123456789012346', {arctic_user_id}, 'VSAT', 'SAT-200', '2025-01-01'),
        ('223456789012345', {desert_user_id}, 'VSAT', 'SAT-300', '2025-01-01');
    ''')

    # Generate 2025 traffic data for all 12 months
    _generate_sample_traffic_data(cursor, arctic_agreement_id, desert_agreement_id)


def _generate_sample_traffic_data(cursor, arctic_agreement_id, desert_agreement_id):
    """Generate sample traffic data for 2025"""
    # Generate sessions and billing records for all 2025 months
    for month in range(1, 13):  # January to December
        # Arctic Research Station - SBD device (123456789012345)
        for day in range(1, 29):  # Generate data for most days
            if random.random() > 0.1:  # 90% chance of activity
                # Generate 1-5 sessions per day
                num_sessions = random.randint(1, 5)
                daily_usage = 0
                
                for session in range(num_sessions):
                    # SBD usage: 1-50 KB per session
                    session_usage = random.randint(1, 50)
                    daily_usage += session_usage
                    
                    # Session start time (random hour)
                    start_hour = random.randint(8, 20)
                    session_start = f"2025-{month:02d}-{day:02d} {start_hour:02d}:{random.randint(0,59):02d}:00"
                    session_end = f"2025-{month:02d}-{day:02d} {start_hour:02d}:{random.randint(0,59):02d}:00"
                    
                    cursor.execute('''
                    INSERT OR IGNORE INTO sessions (imei, service_type_id, session_start, session_end, usage_amount)
                    VALUES (?, 1, ?, ?, ?)
                    ''', ('123456789012345', session_start, session_end, session_usage))
                
                # Monthly billing record (sum of daily usage)
                if day == 28:  # End of month
                    amount = round(daily_usage * 0.05, 2)  # $0.05 per KB
                    cursor.execute('''
                    INSERT OR IGNORE INTO billing_records (agreement_id, imei, service_type_id, billing_date, usage_amount, amount, paid)
                    VALUES (?, ?, 1, ?, ?, ?, 1)
                    ''', (arctic_agreement_id, '123456789012345', f"2025-{month:02d}-28", daily_usage, amount))
        
        # Arctic Research Station - VSAT Data device (123456789012346)
        for day in range(1, 29):
            if random.random() > 0.2:  # 80% chance of activity
                # VSAT Data usage: 10-200 MB per day
                daily_usage = random.randint(10, 200)
                
                # Generate 1-3 sessions per day
                num_sessions = random.randint(1, 3)
                session_usage = daily_usage // num_sessions
                
                for session in range(num_sessions):
                    start_hour = random.randint(9, 18)
                    session_start = f"2025-{month:02d}-{day:02d} {start_hour:02d}:{random.randint(0,59):02d}:00"
                    session_end = f"2025-{month:02d}-{day:02d} {start_hour+1:02d}:{random.randint(0,59):02d}:00"
                    
                    cursor.execute('''
                    INSERT OR IGNORE INTO sessions (imei, service_type_id, session_start, session_end, usage_amount)
                    VALUES (?, 2, ?, ?, ?)
                    ''', ('123456789012346', session_start, session_end, session_usage))
                
                # Monthly billing record
                if day == 28:
                    amount = round(daily_usage * 0.08, 2)  # $0.08 per MB
                    cursor.execute('''
                    INSERT OR IGNORE INTO billing_records (agreement_id, imei, service_type_id, billing_date, usage_amount, amount, paid)
                    VALUES (?, ?, 2, ?, ?, ?, 1)
                    ''', (arctic_agreement_id, '123456789012346', f"2025-{month:02d}-28", daily_usage, amount))
        
        # Desert Observatory - VSAT device (223456789012345)
        for day in range(1, 29):
            if random.random() > 0.15:  # 85% chance of activity
                # VSAT Data usage: 50-500 MB per day
                daily_usage = random.randint(50, 500)
                
                # Generate 2-4 sessions per day
                num_sessions = random.randint(2, 4)
                session_usage = daily_usage // num_sessions
                
                for session in range(num_sessions):
                    start_hour = random.randint(8, 19)
                    session_start = f"2025-{month:02d}-{day:02d} {start_hour:02d}:{random.randint(0,59):02d}:00"
                    session_end = f"2025-{month:02d}-{day:02d} {start_hour+1:02d}:{random.randint(0,59):02d}:00"
                    
                    cursor.execute('''
                    INSERT OR IGNORE INTO sessions (imei, service_type_id, session_start, session_end, usage_amount)
                    VALUES (?, 2, ?, ?, ?)
                    ''', ('223456789012345', session_start, session_end, session_usage))
                
                # Monthly billing record
                if day == 28:
                    amount = round(daily_usage * 0.08, 2)  # $0.08 per MB
                    cursor.execute('''
                    INSERT OR IGNORE INTO billing_records (agreement_id, imei, service_type_id, billing_date, usage_amount, amount, paid)
                    VALUES (?, ?, 2, ?, ?, ?, 1)
                    ''', (desert_agreement_id, '223456789012345', f"2025-{month:02d}-28", daily_usage, amount))


def verify_login(username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Verify login credentials and return (success, role, company)"""
    conn = sqlite3.connect('satellite_billing.db')
    c = conn.cursor()
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        c.execute("""
            SELECT role, company 
            FROM users 
            WHERE username = ? AND password = ?
        """, (username, hashed_password))
        result = c.fetchone()
        if result:
            return True, result[0], result[1]
        return False, None, None
    finally:
        conn.close()


def execute_standard_query(query_name: str, company: str, user_role: str = 'user') -> Tuple[pd.DataFrame, Optional[str]]:
    """Execute a standard query and return results"""
    from .queries import STANDARD_QUERIES
    
    if query_name not in STANDARD_QUERIES:
        return pd.DataFrame(), f"Query '{query_name}' not found"
    
    query = STANDARD_QUERIES[query_name]
    return execute_query(query, (company,))


def get_table_schema(conn, table_name: str) -> str:
    """Get schema information for a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    schema = f"Table: {table_name}\n"
    schema += "Columns:\n"
    for col in columns:
        schema += f"  - {col[1]} ({col[2]})"
        if col[3]:  # NOT NULL
            schema += " NOT NULL"
        if col[5]:  # PRIMARY KEY
            schema += " PRIMARY KEY"
        schema += "\n"
    
    return schema


def get_database_schema() -> str:
    """Get complete database schema"""
    conn = sqlite3.connect('satellite_billing.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    schema = "Database Schema:\n\n"
    for table in tables:
        table_name = table[0]
        schema += get_table_schema(conn, table_name) + "\n"
    
    conn.close()
    return schema


def execute_query(query: str, params: Tuple = ()) -> Tuple[pd.DataFrame, Optional[str]]:
    """Execute a SQL query and return results as DataFrame"""
    try:
        conn = sqlite3.connect('satellite_billing.db')
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)
