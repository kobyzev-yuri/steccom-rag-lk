# KB Admin - Система управления базами знаний

## Быстрый старт

### 1. Запуск
```bash
# Основной скрипт запуска
./start_kb_admin.sh

# Или с очисткой логов
./start_kb_admin.sh --clean-logs

# Запуск в режиме переднего плана (для отладки)
./start_kb_admin.sh --foreground
```

### 2. Управление
```bash
# Проверить статус
./kb_admin_control.sh status

# Остановить
./kb_admin_control.sh stop

# Перезапустить
./kb_admin_control.sh restart

# Показать логи
./kb_admin_control.sh logs

# Запустить в режиме переднего плана
./kb_admin_control.sh foreground
```

## Доступ к приложению

- **URL**: http://localhost:8502
- **Health check**: http://localhost:8502/_stcore/health

## Файлы и логи

- **Логи**: `logs/kb_admin.log`
- **PID файл**: `.kb_admin.pid`
- **Виртуальное окружение**: `.venv/`

## Полезные команды

```bash
# Отслеживание логов в реальном времени
tail -f logs/kb_admin.log

# Проверка порта
ss -ltnp | grep :8502

# Остановка по PID
kill $(cat .kb_admin.pid)

# Принудительная остановка
pkill -f "streamlit.*kb_admin/app.py"
```

## Требования

- Python 3.10+
- Виртуальное окружение `.venv`
- Зависимости из `requirements.txt`

## Устранение проблем

### Порт 8502 занят
```bash
./kb_admin_control.sh stop
# или
sudo lsof -ti:8502 | xargs kill -9
```

### Проблемы с зависимостями
```bash
rm .venv/.deps_installed
./start_kb_admin.sh
```

### Проблемы с импортами
```bash
# Проверить импорты
python kb_admin/test_imports.py
```




