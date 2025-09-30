#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# СТЭККОМ - Универсальный скрипт управления сервисами
# STECCOM - Universal Service Management Script
# =============================================================================

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Конфигурация сервисов
declare -A SERVICES=(
    ["api"]="8000:FastAPI Billing API"
    ["wiki"]="8080:MediaWiki"
    ["kb_admin"]="8502:KB Admin (Knowledge Base Builder)"
    ["streamlit"]="8501:Streamlit Main App"
)

# Конфигурация Docker
DOCKER_CONTAINER="steccom-mediawiki"
DOCKER_IMAGE="mediawiki:1.39"

# Функции для вывода
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен"
        return 1
    fi
    
    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 не установлен"
        return 1
    fi
    
    # Проверка виртуального окружения
    if [ ! -d ".venv" ]; then
        log_error "Виртуальное окружение .venv не найдено"
        log_info "Создайте виртуальное окружение: python3 -m venv .venv"
        return 1
    fi
    
    log_success "Все зависимости найдены"
    return 0
}

# Проверка порта
check_port() {
    local port=$1
    local service_name=$2
    
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        log_success "$service_name работает на порту $port"
        return 0
    else
        log_warning "$service_name не работает на порту $port"
        return 1
    fi
}

# Проверка HTTP сервиса
check_http_service() {
    local url=$1
    local service_name=$2
    local timeout=${3:-5}
    
    if curl -s --max-time $timeout "$url" >/dev/null 2>&1; then
        log_success "$service_name доступен по адресу $url"
        return 0
    else
        log_warning "$service_name недоступен по адресу $url"
        return 1
    fi
}

# Проверка Docker контейнера
check_docker_container() {
    local container_name=$1
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        log_success "Docker контейнер $container_name запущен"
        return 0
    else
        log_warning "Docker контейнер $container_name не запущен"
        return 1
    fi
}

# Запуск API сервиса
start_api() {
    log_info "Запуск FastAPI сервиса..."
    
    if check_port 8000 "FastAPI"; then
        log_info "FastAPI уже запущен"
        return 0
    fi
    
    # Активируем виртуальное окружение
    source .venv/bin/activate
    
    # Устанавливаем зависимости если нужно
    if [ ! -f ".api_deps_installed" ]; then
        log_info "Установка зависимостей API..."
        pip install -r requirements-api.txt
        touch .api_deps_installed
    fi
    
    # Запускаем в фоне
    nohup python api/run_api.py > logs/api.log 2>&1 &
    local api_pid=$!
    echo $api_pid > .api.pid
    
    # Ждем запуска
    sleep 3
    
    if check_http_service "http://localhost:8000/health" "FastAPI"; then
        log_success "FastAPI запущен (PID: $api_pid)"
        return 0
    else
        log_error "Не удалось запустить FastAPI"
        return 1
    fi
}

# Запуск MediaWiki
start_wiki() {
    log_info "Запуск MediaWiki..."
    
    if check_docker_container "$DOCKER_CONTAINER"; then
        log_info "MediaWiki уже запущен"
        return 0
    fi
    
    # Проверяем наличие конфигурации
    if [ ! -f "mediawiki/LocalSettings.php" ]; then
        log_error "Файл конфигурации MediaWiki не найден: mediawiki/LocalSettings.php"
        return 1
    fi
    
    # Создаем директории
    mkdir -p mediawiki_data
    mkdir -p mediawiki_db_persistent
    
    # Запускаем контейнер
    docker run -d \
        --name "$DOCKER_CONTAINER" \
        -p 8080:80 \
        -v "$(pwd)/mediawiki_data:/var/www/html/images" \
        -v "$(pwd)/mediawiki_db_persistent:/var/www/html/data" \
        -v "$(pwd)/mediawiki/LocalSettings.php:/var/www/html/LocalSettings.php:ro" \
        --restart unless-stopped \
        "$DOCKER_IMAGE"
    
    # Ждем запуска
    log_info "Ожидание запуска MediaWiki..."
    sleep 10
    
    if check_http_service "http://localhost:8080" "MediaWiki"; then
        log_success "MediaWiki запущен"
        return 0
    else
        log_error "Не удалось запустить MediaWiki"
        return 1
    fi
}

# Запуск KB Admin
start_kb_admin() {
    log_info "Запуск KB Admin..."
    
    if check_port 8502 "KB Admin"; then
        log_info "KB Admin уже запущен"
        return 0
    fi
    
    # Активируем виртуальное окружение
    source .venv/bin/activate
    
    # Переходим в директорию KB Admin
    cd kb_admin
    
    # Устанавливаем зависимости если нужно
    if [ ! -f ".kb_deps_installed" ]; then
        log_info "Установка зависимостей KB Admin..."
        pip install -r requirements.txt
        touch .kb_deps_installed
    fi
    
    # Создаем необходимые директории
    mkdir -p logs
    mkdir -p temp
    
    # Запускаем в фоне
    nohup streamlit run app.py --server.port 8502 --server.address 0.0.0.0 > ../logs/kb_admin.log 2>&1 &
    local kb_pid=$!
    echo $kb_pid > ../.kb_admin.pid
    
    # Возвращаемся в корень
    cd ..
    
    # Ждем запуска
    sleep 5
    
    if check_http_service "http://localhost:8502" "KB Admin"; then
        log_success "KB Admin запущен (PID: $kb_pid)"
        return 0
    else
        log_error "Не удалось запустить KB Admin"
        return 1
    fi
}

# Запуск Streamlit Main App
start_streamlit() {
    log_info "Запуск Streamlit Main App..."
    
    if check_port 8501 "Streamlit"; then
        log_info "Streamlit уже запущен"
        return 0
    fi
    
    # Активируем виртуальное окружение
    source .venv/bin/activate
    
    # Устанавливаем зависимости если нужно
    if [ ! -f ".streamlit_deps_installed" ]; then
        log_info "Установка зависимостей Streamlit..."
        pip install -r requirements.txt
        touch .streamlit_deps_installed
    fi
    
    # Создаем директорию для логов
    mkdir -p logs
    
    # Запускаем в фоне
    nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit.log 2>&1 &
    local streamlit_pid=$!
    echo $streamlit_pid > .streamlit.pid
    
    # Ждем запуска
    sleep 5
    
    if check_http_service "http://localhost:8501" "Streamlit"; then
        log_success "Streamlit запущен (PID: $streamlit_pid)"
        return 0
    else
        log_error "Не удалось запустить Streamlit"
        return 1
    fi
}

# Проверка всех сервисов
check_all_services() {
    log_header "Проверка статуса всех сервисов"
    echo "=================================="
    
    local all_running=true
    
    # Проверяем API
    if ! check_http_service "http://localhost:8000/health" "FastAPI"; then
        all_running=false
    fi
    
    # Проверяем MediaWiki
    if ! check_http_service "http://localhost:8080" "MediaWiki"; then
        all_running=false
    fi
    
    # Проверяем KB Admin
    if ! check_http_service "http://localhost:8502" "KB Admin"; then
        all_running=false
    fi
    
    # Проверяем Streamlit
    if ! check_http_service "http://localhost:8501" "Streamlit"; then
        all_running=false
    fi
    
    echo ""
    if [ "$all_running" = true ]; then
        log_success "Все сервисы работают!"
        show_service_urls
    else
        log_warning "Некоторые сервисы не работают"
    fi
    
    return $([ "$all_running" = true ] && echo 0 || echo 1)
}

# Показать URL сервисов
show_service_urls() {
    echo ""
    log_header "Доступные сервисы:"
    echo "🌐 FastAPI Billing API: http://localhost:8000"
    echo "   📖 Документация: http://localhost:8000/docs"
    echo "   🔧 ReDoc: http://localhost:8000/redoc"
    echo "   💚 Health: http://localhost:8000/health"
    echo ""
    echo "📚 MediaWiki: http://localhost:8080"
    echo "   👤 Логин: admin / Admin123456789"
    echo ""
    echo "🧠 KB Admin (Knowledge Base Builder): http://localhost:8502"
    echo ""
    echo "🎯 Streamlit Main App: http://localhost:8501"
    echo ""
}

# Запуск всех сервисов
start_all_services() {
    log_header "Запуск всех сервисов СТЭККОМ"
    echo "================================="
    
    # Проверяем зависимости
    if ! check_dependencies; then
        log_error "Не все зависимости установлены"
        return 1
    fi
    
    # Создаем директорию для логов
    mkdir -p logs
    
    local failed_services=()
    
    # Запускаем сервисы по порядку
    log_info "Запуск сервисов..."
    
    if ! start_wiki; then
        failed_services+=("MediaWiki")
    fi
    
    if ! start_api; then
        failed_services+=("FastAPI")
    fi
    
    if ! start_kb_admin; then
        failed_services+=("KB Admin")
    fi
    
    if ! start_streamlit; then
        failed_services+=("Streamlit")
    fi
    
    echo ""
    if [ ${#failed_services[@]} -eq 0 ]; then
        log_success "Все сервисы успешно запущены!"
        show_service_urls
    else
        log_error "Не удалось запустить: ${failed_services[*]}"
        return 1
    fi
}

# Остановка всех сервисов
stop_all_services() {
    log_header "Остановка всех сервисов"
    echo "========================"
    
    # Останавливаем Python процессы
    for pid_file in .api.pid .kb_admin.pid .streamlit.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                log_info "Остановка процесса $pid ($pid_file)"
                kill "$pid"
                rm -f "$pid_file"
            fi
        fi
    done
    
    # Останавливаем Docker контейнер
    if docker ps --format "table {{.Names}}" | grep -q "^${DOCKER_CONTAINER}$"; then
        log_info "Остановка Docker контейнера $DOCKER_CONTAINER"
        docker stop "$DOCKER_CONTAINER"
        docker rm "$DOCKER_CONTAINER"
    fi
    
    log_success "Все сервисы остановлены"
}

# Перезапуск всех сервисов
restart_all_services() {
    log_header "Перезапуск всех сервисов"
    echo "=========================="
    
    stop_all_services
    sleep 2
    start_all_services
}

# Показать логи
show_logs() {
    local service=${1:-"all"}
    
    case "$service" in
        "api")
            if [ -f "logs/api.log" ]; then
                tail -f logs/api.log
            else
                log_error "Лог файл API не найден"
            fi
            ;;
        "kb_admin")
            if [ -f "logs/kb_admin.log" ]; then
                tail -f logs/kb_admin.log
            else
                log_error "Лог файл KB Admin не найден"
            fi
            ;;
        "streamlit")
            if [ -f "logs/streamlit.log" ]; then
                tail -f logs/streamlit.log
            else
                log_error "Лог файл Streamlit не найден"
            fi
            ;;
        "all")
            log_info "Показ логов всех сервисов (Ctrl+C для выхода)"
            if [ -f "logs/api.log" ]; then
                echo "=== API LOGS ==="
                tail -n 10 logs/api.log
            fi
            if [ -f "logs/kb_admin.log" ]; then
                echo "=== KB ADMIN LOGS ==="
                tail -n 10 logs/kb_admin.log
            fi
            if [ -f "logs/streamlit.log" ]; then
                echo "=== STREAMLIT LOGS ==="
                tail -n 10 logs/streamlit.log
            fi
            ;;
        *)
            log_error "Неизвестный сервис: $service"
            log_info "Доступные сервисы: api, kb_admin, streamlit, all"
            ;;
    esac
}

# Показать справку
show_help() {
    cat << EOF
СТЭККОМ - Универсальный скрипт управления сервисами

Использование: $0 <команда> [опции]

Команды:
  start           Запустить все сервисы
  stop            Остановить все сервисы
  restart         Перезапустить все сервисы
  status          Показать статус всех сервисов
  check           Проверить статус сервисов (то же что status)
  logs [сервис]   Показать логи сервиса (api, kb_admin, streamlit, all)
  help            Показать эту справку

Сервисы:
  🌐 FastAPI Billing API (порт 8000)
  📚 MediaWiki (порт 8080)
  🧠 KB Admin - Knowledge Base Builder (порт 8502)
  🎯 Streamlit Main App (порт 8501)

Примеры:
  $0 start                    # Запустить все сервисы
  $0 status                   # Проверить статус
  $0 logs api                 # Показать логи API
  $0 restart                  # Перезапустить все сервисы

EOF
}

# Главная функция
main() {
    local command=${1:-"help"}
    
    case "$command" in
        "start")
            start_all_services
            ;;
        "stop")
            stop_all_services
            ;;
        "restart")
            restart_all_services
            ;;
        "status"|"check")
            check_all_services
            ;;
        "logs")
            show_logs "$2"
            ;;
        "help"|"-h"|"--help"|"")
            show_help
            ;;
        *)
            log_error "Неизвестная команда: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Запуск скрипта
main "$@"

