# Схема базы данных СТЭККОМ

## Обзор
База данных спутникового оператора связи с поддержкой 3 типов услуг: SBD, VSAT Data, VSAT Voice.

## Таблицы

### 1. users - Пользователи системы
- `id` - уникальный идентификатор
- `username` - имя пользователя
- `password` - хеш пароля
- `company` - название компании
- `role` - роль (staff/user)

### 2. service_types - Типы услуг
- `id` - уникальный идентификатор
- `name` - название услуги (SBD, VSAT_DATA, VSAT_VOICE)
- `unit` - единица измерения (KB, MB, minutes)
- `description` - описание услуги

### 3. tariffs - Тарифы
- `id` - уникальный идентификатор
- `service_type_id` - ссылка на тип услуги
- `name` - название тарифа
- `price_per_unit` - цена за единицу
- `monthly_fee` - месячная плата
- `traffic_limit` - лимит трафика
- `is_active` - активен ли тариф

### 4. agreements - Договоры
- `id` - уникальный идентификатор
- `user_id` - ссылка на пользователя
- `tariff_id` - ссылка на тариф
- `start_date` - дата начала
- `end_date` - дата окончания
- `status` - статус (active/pending/terminated)

### 5. devices - Устройства
- `imei` - уникальный идентификатор устройства
- `user_id` - ссылка на пользователя
- `device_type` - тип устройства (SBD, VSAT)
- `model` - модель устройства
- `activated_at` - дата активации

### 6. sessions - Сессии использования
- `id` - уникальный идентификатор
- `imei` - ссылка на устройство
- `service_type_id` - ссылка на тип услуги
- `session_start` - время начала сессии
- `session_end` - время окончания сессии
- `usage_amount` - количество использованных единиц
- `created_at` - дата создания записи

### 7. billing_records - Биллинговые записи
- `id` - уникальный идентификатор
- `agreement_id` - ссылка на договор
- `imei` - ссылка на устройство
- `service_type_id` - ссылка на тип услуги
- `billing_date` - дата биллинга
- `usage_amount` - количество использованных единиц
- `amount` - сумма к оплате
- `paid` - оплачено ли
- `payment_date` - дата оплаты

## Связи между таблицами

```
users (1) ←→ (N) agreements
users (1) ←→ (N) devices
service_types (1) ←→ (N) tariffs
service_types (1) ←→ (N) sessions
service_types (1) ←→ (N) billing_records
tariffs (1) ←→ (N) agreements
devices (1) ←→ (N) sessions
devices (1) ←→ (N) billing_records
agreements (1) ←→ (N) billing_records
```

## Типы услуг

1. **SBD (Short Burst Data)**
   - Единица: KB
   - Описание: спутниковая передача данных
   - Примеры тарифов: SBD Basic, SBD Premium

2. **VSAT_DATA**
   - Единица: MB
   - Описание: высокоскоростная передача данных
   - Примеры тарифов: VSAT Data 1GB, VSAT Data 5GB

3. **VSAT_VOICE**
   - Единица: minutes
   - Описание: спутниковая телефония
   - Примеры тарифов: VSAT Voice 100min, VSAT Voice 500min

## Логика работы

1. **Создание сессий**: При использовании устройства создаются записи в таблице `sessions`
2. **Биллинг**: На основе сессий формируются месячные записи в `billing_records`
3. **Доступ к данным**: 
   - Админы видят все данные
   - Пользователи видят только данные своей компании

## Примеры запросов

### Все сессии SBD устройств:
```sql
SELECT s.imei, st.name, s.session_start, s.session_end, s.usage_amount
FROM sessions s
JOIN service_types st ON s.service_type_id = st.id
WHERE st.name = 'SBD'
ORDER BY s.session_start DESC;
```

### Трафик по компаниям:
```sql
SELECT u.company, st.name, SUM(b.usage_amount), SUM(b.amount)
FROM billing_records b
JOIN agreements a ON b.agreement_id = a.id
JOIN users u ON a.user_id = u.id
JOIN service_types st ON b.service_type_id = st.id
GROUP BY u.company, st.name;
```
