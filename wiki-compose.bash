#!/usr/bin/env bash
set -euo pipefail

# Config
COMPOSE_FILE="docker-compose.yml"
CONTAINER="steccom-mediawiki"
PORT="8080"
ROOT="$(pwd)"
API_URL="http://localhost:8000"                       # FastAPI (для publish)

usage() {
  cat <<EOF
Usage: $0 <command> [options]

Commands:
  start             Запустить MediaWiki через docker-compose
  stop              Остановить MediaWiki
  restart           Перезапустить MediaWiki
  status            Показать статус и проверить CSS/картинки
  purge             Очистить кэш Wiki и purge главной
  publish           Опубликовать KB в MediaWiki через FastAPI (нужен $TOKEN)
                    Options: --user admin --pass Admin123456789 --glob "docs/kb/*.json"
  logs              Показать логи MediaWiki
  backup            Создать бэкап базы данных
  restore           Восстановить базу данных из бэкапа

Examples:
  $0 start
  $0 status
  TOKEN="..." $0 publish --user admin --pass Admin123456789 --glob "docs/kb/*.json"
  $0 backup
EOF
}

ensure_requirements() {
  command -v docker-compose >/dev/null 2>&1 || { echo "docker-compose not found"; exit 1; }
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo "docker-compose.yml не найден: ${COMPOSE_FILE}"
    exit 1
  fi
}

start() {
  ensure_requirements
  echo "🚀 Запуск MediaWiki через docker-compose..."
  docker-compose up -d
  
  echo "⏳ Жду поднятие сервера..."
  sleep 10
  
  # Проверяем здоровье контейнера
  if docker-compose ps | grep -q "healthy"; then
    echo "✅ MediaWiki запущен и здоров"
  else
    echo "⚠️  MediaWiki запущен, но проверка здоровья не прошла"
  fi
  
  # Purge главной
  curl -s "http://localhost:${PORT}/index.php?title=Заглавная_страница&action=purge" >/dev/null || true
  status
}

stop() {
  echo "🛑 Остановка MediaWiki..."
  docker-compose down
  echo "✅ MediaWiki остановлен"
}

restart() {
  stop
  start
}

purge() {
  # Очистка кэша и purge главной
  docker-compose exec mediawiki rm -rf /var/www/html/cache/* >/dev/null 2>&1 || true
  curl -s "http://localhost:${PORT}/index.php?title=Заглавная_страница&action=purge" >/dev/null || true
  echo "✅ Кэш очищен, главная обновлена"
}

status() {
  echo "🐳 Статус контейнеров:"
  docker-compose ps
  echo
  echo "🔎 Проверка CSS (ожидается Content-Type: text/css)"
  curl -I "http://localhost:${PORT}/load.php?lang=ru&modules=skins.vector.styles.legacy&only=styles&skin=vector" | sed -n '1,10p' || true
  echo
  echo "🖼  Проверка картинки (ожидается image/png)"
  curl -I "http://localhost:${PORT}/resources/assets/poweredby_mediawiki_88x31.png" | sed -n '1,10p' || true
  echo
  echo "🌐 Откройте в браузере: http://localhost:${PORT}/"
  echo "📊 API: http://localhost:${PORT}/api.php"
}

logs() {
  echo "📋 Логи MediaWiki:"
  docker-compose logs -f mediawiki
}

backup() {
  echo "💾 Создание бэкапа базы данных..."
  BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$BACKUP_DIR"
  
  # Копируем базу данных
  cp -r mediawiki_db_persistent "$BACKUP_DIR/"
  cp -r mediawiki_data "$BACKUP_DIR/"
  
  echo "✅ Бэкап создан в: $BACKUP_DIR"
}

restore() {
  if [[ $# -eq 0 ]]; then
    echo "Использование: $0 restore <путь_к_бэкапу>"
    echo "Доступные бэкапы:"
    ls -la backups/ 2>/dev/null || echo "Бэкапы не найдены"
    exit 1
  fi
  
  BACKUP_PATH="$1"
  if [[ ! -d "$BACKUP_PATH" ]]; then
    echo "❌ Бэкап не найден: $BACKUP_PATH"
    exit 1
  fi
  
  echo "🔄 Восстановление из бэкапа: $BACKUP_PATH"
  
  # Останавливаем MediaWiki
  docker-compose down
  
  # Восстанавливаем данные
  rm -rf mediawiki_db_persistent mediawiki_data
  cp -r "$BACKUP_PATH/mediawiki_db_persistent" ./
  cp -r "$BACKUP_PATH/mediawiki_data" ./
  
  # Запускаем MediaWiki
  docker-compose up -d
  
  echo "✅ Восстановление завершено"
}

publish() {
  # Args
  local USER="admin"
  local PASS="Admin123456789"
  local GLOB="docs/kb/*.json"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --user) USER="$2"; shift 2 ;;
      --pass) PASS="$2"; shift 2 ;;
      --glob) GLOB="$2"; shift 2 ;;
      *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
  done

  if [[ -z "${TOKEN:-}" ]]; then
    echo "ERROR: TOKEN env is required. Example:"
    echo '  TOKEN="..." '$0' publish --user admin --pass Admin123456789 --glob "docs/kb/*.json"'
    exit 1
  fi

  echo "📤 Публикация KB → MediaWiki через FastAPI..."
  curl -s -X POST "${API_URL}/wiki/publish" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"wiki_url\":\"http://localhost:${PORT}/api.php\",\"username\":\"${USER}\",\"password\":\"${PASS}\",\"kb_glob\":\"${GLOB}\"}" | jq . || true
}

cmd="${1:-}"
shift || true

case "${cmd}" in
  start)   start ;;
  stop)    stop ;;
  restart) restart ;;
  status)  status ;;
  purge)   purge ;;
  logs)    logs ;;
  backup)  backup ;;
  restore) restore "$@" ;;
  publish) publish "$@" ;;
  ""|help|-h|--help) usage ;;
  *) echo "Unknown command: ${cmd}"; usage; exit 1 ;;
esac
