"""
SQL queries module for satellite billing system
Contains all standard queries and quick questions
"""

# Standard queries for users
STANDARD_QUERIES = {
    "My monthly traffic": """
    SELECT 
        strftime('%Y-%m', b.billing_date) as month,
        st.name as service_type,
        st.unit as unit,
        SUM(b.usage_amount) as total_usage,
        ROUND(SUM(b.amount), 2) as total_amount,
        COUNT(DISTINCT b.imei) as active_devices
    FROM billing_records b
    JOIN agreements a ON b.agreement_id = a.id
    JOIN users u ON a.user_id = u.id
    JOIN service_types st ON b.service_type_id = st.id
    WHERE u.company = ?
    GROUP BY strftime('%Y-%m', b.billing_date), st.name, st.unit
    ORDER BY month DESC, st.name;
    """,
    
    "My devices": """
    SELECT 
        d.imei as device_id,
        d.device_type as type,
        d.model as model,
        d.activated_at as activation_date,
        COALESCE(SUM(b.usage_amount), 0) as total_usage,
        ROUND(COALESCE(SUM(b.amount), 0), 2) as total_amount
    FROM devices d
    LEFT JOIN billing_records b ON d.imei = b.imei
    JOIN users u ON d.user_id = u.id
    WHERE u.company = ?
    GROUP BY d.imei, d.device_type, d.model, d.activated_at
    ORDER BY d.imei;
    """,
    
    "Current month usage": """
    SELECT 
        d.imei as device_id,
        d.model as model,
        st.name as service_type,
        st.unit as unit,
        SUM(b.usage_amount) as usage_amount,
        ROUND(SUM(b.amount), 2) as total_amount
    FROM billing_records b
    JOIN devices d ON b.imei = d.imei
    JOIN users u ON d.user_id = u.id
    JOIN service_types st ON b.service_type_id = st.id
    WHERE u.company = ?
    AND strftime('%Y-%m', b.billing_date) = strftime('%Y-%m', 'now')
    GROUP BY d.imei, st.name, st.unit
    ORDER BY d.imei, st.name;
    """,
    
    "Current agreement": """
    SELECT 
        t.name as tariff_name,
        st.name as service_type,
        st.unit as unit,
        t.price_per_unit as price_per_unit,
        t.monthly_fee as monthly_fee,
        t.traffic_limit as traffic_limit,
        a.start_date as start_date,
        a.end_date as end_date,
        a.status as status
    FROM agreements a
    JOIN users u ON a.user_id = u.id
    JOIN tariffs t ON a.tariff_id = t.id
    JOIN service_types st ON t.service_type_id = st.id
    WHERE u.company = ?
        AND date('now') BETWEEN date(a.start_date) AND date(a.end_date)
        AND a.status = 'active';
    """,
    
    "Service sessions": """
    SELECT 
        u.company,
        s.imei as device_id,
        d.device_type,
        d.model,
        st.name as service_type,
        st.unit as unit,
        s.session_start as start_time,
        s.session_end as end_time,
        s.usage_amount as usage_amount
    FROM sessions s
    JOIN devices d ON s.imei = d.imei
    JOIN users u ON d.user_id = u.id
    JOIN service_types st ON s.service_type_id = st.id
    WHERE u.company = ?
    AND date(s.session_start) >= date('now', '-30 days')
    ORDER BY s.session_start DESC
    LIMIT 100;
    """,
    
    "SBD monthly traffic": """
    SELECT 
        strftime('%Y-%m', b.billing_date) as month,
        st.name as service_type,
        st.unit as unit,
        SUM(b.usage_amount) as total_usage,
        ROUND(SUM(b.amount), 2) as total_amount,
        COUNT(DISTINCT b.imei) as active_devices
    FROM billing_records b
    JOIN agreements a ON b.agreement_id = a.id
    JOIN users u ON a.user_id = u.id
    JOIN service_types st ON b.service_type_id = st.id
    WHERE u.company = ?
    AND st.name = 'SBD'
    GROUP BY strftime('%Y-%m', b.billing_date), st.name, st.unit
    ORDER BY month DESC;
    """,
    
    "VSAT_DATA monthly traffic": """
    SELECT 
        strftime('%Y-%m', b.billing_date) as month,
        st.name as service_type,
        st.unit as unit,
        SUM(b.usage_amount) as total_usage,
        ROUND(SUM(b.amount), 2) as total_amount,
        COUNT(DISTINCT b.imei) as active_devices
    FROM billing_records b
    JOIN agreements a ON b.agreement_id = a.id
    JOIN users u ON a.user_id = u.id
    JOIN service_types st ON b.service_type_id = st.id
    WHERE u.company = ?
    AND st.name = 'VSAT_DATA'
    GROUP BY strftime('%Y-%m', b.billing_date), st.name, st.unit
    ORDER BY month DESC;
    """,
    
    "SBD sessions": """
    SELECT 
        s.imei as device_id,
        d.device_type,
        d.model,
        st.name as service_type,
        st.unit as unit,
        s.session_start as start_time,
        s.session_end as end_time,
        s.usage_amount as usage_amount,
        ROUND((julianday(s.session_end) - julianday(s.session_start)) * 24 * 60, 2) as duration_minutes
    FROM sessions s
    JOIN devices d ON s.imei = d.imei
    JOIN users u ON d.user_id = u.id
    JOIN service_types st ON s.service_type_id = st.id
    WHERE u.company = ?
    AND st.name = 'SBD'
    ORDER BY s.session_start DESC
    LIMIT 100;
    """,
    
    "VSAT_DATA sessions": """
    SELECT 
        s.imei as device_id,
        d.device_type,
        d.model,
        st.name as service_type,
        st.unit as unit,
        s.session_start as start_time,
        s.session_end as end_time,
        s.usage_amount as usage_amount,
        ROUND((julianday(s.session_end) - julianday(s.session_start)) * 24 * 60, 2) as duration_minutes
    FROM sessions s
    JOIN devices d ON s.imei = d.imei
    JOIN users u ON d.user_id = u.id
    JOIN service_types st ON s.service_type_id = st.id
    WHERE u.company = ?
    AND st.name = 'VSAT_DATA'
    ORDER BY s.session_start DESC
    LIMIT 100;
    """,
    
    "VSAT_VOICE monthly traffic": """
    SELECT 
        strftime('%Y-%m', b.billing_date) as month,
        st.name as service_type,
        st.unit as unit,
        SUM(b.usage_amount) as total_usage,
        ROUND(SUM(b.amount), 2) as total_amount,
        COUNT(DISTINCT b.imei) as active_devices
    FROM billing_records b
    JOIN agreements a ON b.agreement_id = a.id
    JOIN users u ON a.user_id = u.id
    JOIN service_types st ON b.service_type_id = st.id
    WHERE u.company = ?
    AND st.name = 'VSAT_VOICE'
    GROUP BY strftime('%Y-%m', b.billing_date), st.name, st.unit
    ORDER BY month DESC;
    """,
    
    "VSAT_VOICE sessions": """
    SELECT 
        s.imei as device_id,
        d.device_type,
        d.model,
        st.name as service_type,
        st.unit as unit,
        s.session_start as start_time,
        s.session_end as end_time,
        s.usage_amount as usage_amount,
        ROUND((julianday(s.session_end) - julianday(s.session_start)) * 24 * 60, 2) as duration_minutes
    FROM sessions s
    JOIN devices d ON s.imei = d.imei
    JOIN users u ON d.user_id = u.id
    JOIN service_types st ON s.service_type_id = st.id
    WHERE u.company = ?
    AND st.name = 'VSAT_VOICE'
    ORDER BY s.session_start DESC
    LIMIT 100;
    """
}

# Quick questions for users
QUICK_QUESTIONS = [
    "Покажи статистику трафика за последний месяц",
    "Какие устройства потребляют больше всего трафика?",
    "Сколько у меня активных соглашений?",
    "Покажи сессии за последние 30 дней",
    "Какие тарифы у меня подключены?",
    "Покажи использование SBD за текущий месяц",
    "Сколько трафика VSAT_DATA за последние 3 месяца?",
    "Какие устройства у меня зарегистрированы?",
    "Покажи детали текущего договора",
    "Сколько я потратил на связь в этом месяце?"
]

