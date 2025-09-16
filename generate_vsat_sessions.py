#!/usr/bin/env python3
"""
Скрипт для генерации тестовых данных по сессиям VSAT всех типов за 2025 год
"""

import sqlite3
import random
from datetime import datetime, timedelta
import os

def generate_vsat_sessions():
    """Генерирует тестовые сессии для VSAT_DATA и VSAT_VOICE"""
    
    # Подключение к базе данных
    conn = sqlite3.connect('satellite_billing.db')
    cursor = conn.cursor()
    
    # Получаем список устройств и пользователей
    cursor.execute("""
        SELECT d.imei, d.user_id, u.company 
        FROM devices d 
        JOIN users u ON d.user_id = u.id 
        WHERE u.role = 'user'
    """)
    devices = cursor.fetchall()
    
    if not devices:
        print("Нет устройств для генерации сессий")
        return
    
    # Получаем ID типов услуг
    cursor.execute("SELECT id, name FROM service_types")
    service_types = {name: id for id, name in cursor.fetchall()}
    
    print(f"Найдено устройств: {len(devices)}")
    print(f"Типы услуг: {service_types}")
    
    # Генерируем сессии для каждого месяца 2025 года
    sessions_data = []
    
    for month in range(1, 13):
        print(f"Генерируем сессии для {month:02d}/2025...")
        
        for device_imei, user_id, company in devices:
            # Генерируем сессии для VSAT_DATA (передача данных)
            if 'VSAT_DATA' in service_types:
                vsat_data_sessions = generate_vsat_data_sessions(
                    device_imei, service_types['VSAT_DATA'], month, 2025
                )
                sessions_data.extend(vsat_data_sessions)
            
            # Генерируем сессии для VSAT_VOICE (голосовая связь)
            if 'VSAT_VOICE' in service_types:
                vsat_voice_sessions = generate_vsat_voice_sessions(
                    device_imei, service_types['VSAT_VOICE'], month, 2025
                )
                sessions_data.extend(vsat_voice_sessions)
    
    # Вставляем данные в базу
    if sessions_data:
        cursor.executemany("""
            INSERT INTO sessions (imei, service_type_id, session_start, session_end, usage_amount)
            VALUES (?, ?, ?, ?, ?)
        """, sessions_data)
        
        conn.commit()
        print(f"Добавлено {len(sessions_data)} сессий")
    
    conn.close()

def generate_vsat_data_sessions(imei, service_type_id, month, year):
    """Генерирует сессии VSAT_DATA (передача данных)"""
    sessions = []
    
    # Количество сессий в месяц (от 5 до 20)
    num_sessions = random.randint(5, 20)
    
    for _ in range(num_sessions):
        # Случайная дата в месяце
        day = random.randint(1, 28)
        hour = random.randint(8, 22)  # Рабочие часы
        minute = random.randint(0, 59)
        
        session_start = datetime(year, month, day, hour, minute)
        
        # Длительность сессии от 5 до 120 минут
        duration_minutes = random.randint(5, 120)
        session_end = session_start + timedelta(minutes=duration_minutes)
        
        # Объем данных в MB (от 1 до 500 MB)
        usage_amount = random.randint(1, 500)
        
        sessions.append((
            imei,
            service_type_id,
            session_start.strftime('%Y-%m-%d %H:%M:%S'),
            session_end.strftime('%Y-%m-%d %H:%M:%S'),
            usage_amount
        ))
    
    return sessions

def generate_vsat_voice_sessions(imei, service_type_id, month, year):
    """Генерирует сессии VSAT_VOICE (голосовая связь)"""
    sessions = []
    
    # Количество звонков в месяц (от 10 до 50)
    num_sessions = random.randint(10, 50)
    
    for _ in range(num_sessions):
        # Случайная дата в месяце
        day = random.randint(1, 28)
        hour = random.randint(6, 23)  # Расширенные часы для звонков
        minute = random.randint(0, 59)
        
        session_start = datetime(year, month, day, hour, minute)
        
        # Длительность звонка от 1 до 30 минут
        duration_minutes = random.randint(1, 30)
        session_end = session_start + timedelta(minutes=duration_minutes)
        
        # Длительность в минутах (использование)
        usage_amount = duration_minutes
        
        sessions.append((
            imei,
            service_type_id,
            session_start.strftime('%Y-%m-%d %H:%M:%S'),
            session_end.strftime('%Y-%m-%d %H:%M:%S'),
            usage_amount
        ))
    
    return sessions

def generate_vsat_billing_records():
    """Генерирует записи биллинга для VSAT_DATA и VSAT_VOICE"""
    
    conn = sqlite3.connect('satellite_billing.db')
    cursor = conn.cursor()
    
    # Получаем активные соглашения
    cursor.execute("""
        SELECT a.id, a.user_id, t.service_type_id, t.price_per_unit
        FROM agreements a
        JOIN tariffs t ON a.tariff_id = t.id
        JOIN service_types st ON t.service_type_id = st.id
        WHERE a.status = 'active' 
        AND st.name IN ('VSAT_DATA', 'VSAT_VOICE')
    """)
    agreements = cursor.fetchall()
    
    if not agreements:
        print("Нет активных соглашений для VSAT_DATA/VSAT_VOICE")
        return
    
    # Получаем устройства пользователей
    cursor.execute("""
        SELECT d.imei, d.user_id 
        FROM devices d 
        JOIN users u ON d.user_id = u.id 
        WHERE u.role = 'user'
    """)
    devices = cursor.fetchall()
    
    billing_data = []
    
    # Генерируем записи биллинга для каждого месяца 2025
    for month in range(1, 13):
        print(f"Генерируем биллинг для {month:02d}/2025...")
        
        for agreement_id, user_id, service_type_id, price_per_unit in agreements:
            # Находим устройства этого пользователя
            user_devices = [d for d in devices if d[1] == user_id]
            
            for device_imei, _ in user_devices:
                # Суммируем сессии за месяц
                cursor.execute("""
                    SELECT SUM(usage_amount) as total_usage
                    FROM sessions 
                    WHERE imei = ? 
                    AND service_type_id = ?
                    AND strftime('%Y-%m', session_start) = ?
                """, (device_imei, service_type_id, f"2025-{month:02d}"))
                
                result = cursor.fetchone()
                total_usage = result[0] if result[0] else 0
                
                if total_usage > 0:
                    amount = total_usage * price_per_unit
                    billing_date = f"2025-{month:02d}-28"  # Конец месяца
                    
                    billing_data.append((
                        agreement_id,
                        device_imei,
                        service_type_id,
                        billing_date,
                        total_usage,
                        amount,
                        0,  # paid = False
                        None  # payment_date = None
                    ))
    
    # Вставляем данные биллинга
    if billing_data:
        cursor.executemany("""
            INSERT INTO billing_records (agreement_id, imei, service_type_id, billing_date, usage_amount, amount, paid, payment_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, billing_data)
        
        conn.commit()
        print(f"Добавлено {len(billing_data)} записей биллинга")
    
    conn.close()

if __name__ == "__main__":
    print("Генерация тестовых данных VSAT...")
    
    # Проверяем, существует ли база данных
    if not os.path.exists('satellite_billing.db'):
        print("База данных не найдена. Запустите приложение для создания базы.")
        exit(1)
    
    # Генерируем сессии
    generate_vsat_sessions()
    
    # Генерируем записи биллинга
    generate_vsat_billing_records()
    
    print("Генерация завершена!")
