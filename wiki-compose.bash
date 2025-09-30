#!/usr/bin/env bash
set -euo pipefail

# Config
COMPOSE_FILE="docker-compose.yml"
CONTAINER="steccom-mediawiki"
PORT="8080"
ROOT="$(pwd)"
API_URL="http://localhost:8000"                       # FastAPI (для publish)

# Detect compose binary (docker compose vs docker-compose), else fallback to bare docker
COMPOSE=""
MODE=""
detect_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
    MODE="compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    # Validate docker-compose actually runs (old Debian package may be broken)
    if docker-compose version >/dev/null 2>&1; then
      COMPOSE="docker-compose"
      MODE="compose"
    else
      MODE="bare"
    fi
  else
    MODE="bare"
  fi
}

ensure_requirements() {
  detect_compose
  if [[ "${MODE}" == "compose" ]]; then
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
      echo "docker-compose.yml не найден: ${COMPOSE_FILE}"
      exit 1
    fi
  fi
}

# Ensure volumes exist and ownership is correct for www-data (uid:33,gid:33)
ensure_volumes() {
  mkdir -p ./mediawiki_db_persistent ./mediawiki_data ./mediawiki
  # Попробуем выставить права, если доступно
  if chown -R 33:33 ./mediawiki_db_persistent ./mediawiki_data 2>/dev/null; then
    :
  else
    echo "⚠️ Не удалось chown 33:33 для mediawiki_* (возможно, нет прав). Продолжаю..."
  fi
}

usage() {
  cat <<EOF
Usage: $0 <command> [options]

Commands:
  start             Запустить MediaWiki (compose или bare docker)
  stop              Остановить MediaWiki
  restart           Перезапустить MediaWiki
  status            Показать статус и проверить CSS/картинки
  purge             Очистить кэша Wiki и purge главной
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

# ---------------- Compose mode commands ----------------
start_compose() {
  echo "🚀 Запуск MediaWiki через ${COMPOSE}..."
  ${COMPOSE} -f "${COMPOSE_FILE}" up -d
}

stop_compose() {
  echo "🛑 Остановка MediaWiki..."
  ${COMPOSE} -f "${COMPOSE_FILE}" down
}

status_compose() {
  echo "🐳 Статус контейнеров (compose):"
  ${COMPOSE} -f "${COMPOSE_FILE}" ps || true
}

logs_compose() {
  echo "📋 Логи MediaWiki:"
  ${COMPOSE} -f "${COMPOSE_FILE}" logs -f mediawiki
}

purge_compose() {
  ${COMPOSE} -f "${COMPOSE_FILE}" exec -T mediawiki rm -rf /var/www/html/cache/* >/dev/null 2>&1 || true
}

# ---------------- Bare docker fallback ----------------
start_bare() {
  echo "🚀 Запуск MediaWiki через bare docker..."
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
  docker run -d --name "${CONTAINER}" \
    -p "${PORT}:80" \
    -e MEDIAWIKI_DB_TYPE=sqlite \
    -e MEDIAWIKI_DB_NAME=mediawiki \
    -e MEDIAWIKI_SITE_NAME="СТЭККОМ Wiki" \
    -e MEDIAWIKI_SITE_LANG=ru \
    -e MEDIAWIKI_ADMIN_USER=admin \
    -e MEDIAWIKI_ADMIN_PASS=Admin123456789 \
    -e MEDIAWIKI_ENABLE_UPLOADS=true \
    -v "${ROOT}/mediawiki_db_persistent:/var/www/html/data" \
    -v "${ROOT}/mediawiki_data:/var/www/html/images" \
    -v "${ROOT}/mediawiki/LocalSettings.php:/var/www/html/LocalSettings.php:ro" \
    --restart unless-stopped \
    mediawiki:1.39
}

stop_bare() {
  echo "🛑 Остановка MediaWiki (bare)..."
  docker stop "${CONTAINER}" >/dev/null 2>&1 || true
  docker rm "${CONTAINER}" >/dev/null 2>&1 || true
}

status_bare() {
  echo "🐳 Статус контейнера (bare):"
  docker ps --filter "name=${CONTAINER}" --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' || true
}

logs_bare() {
  echo "📋 Логи MediaWiki (bare):"
  docker logs -f "${CONTAINER}"
}

purge_bare() {
  docker exec -T "${CONTAINER}" rm -rf /var/www/html/cache/* >/dev/null 2>&1 || true
}

# ---------------- Common flows ----------------
start() {
  ensure_requirements
  ensure_volumes
  if [[ "${MODE}" == "compose" ]]; then
    start_compose
  else
    start_bare
  fi
  
  echo "⏳ Жду поднятие сервера..."
  sleep 10
  
  # Purge главной
  curl -s "http://localhost:${PORT}/index.php?title=Заглавная_страница&action=purge" >/dev/null || true
  status
}

stop() {
  ensure_requirements
  if [[ "${MODE}" == "compose" ]]; then
    stop_compose
  else
    stop_bare
  fi
  echo "✅ MediaWiki остановлен"
}

restart() {
  stop
  start
}

purge() {
  ensure_requirements
  if [[ "${MODE}" == "compose" ]]; then
    purge_compose
  else
    purge_bare
  fi
  curl -s "http://localhost:${PORT}/index.php?title=Заглавная_страница&action=purge" >/dev/null || true
  echo "✅ Кэш очищен, главная обновлена"
}

status() {
  ensure_requirements
  if [[ "${MODE}" == "compose" ]]; then
    status_compose
  else
    status_bare
  fi
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
  ensure_requirements
  if [[ "${MODE}" == "compose" ]]; then
    logs_compose
  else
    logs_bare
  fi
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
  ensure_requirements
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
  if [[ "${MODE}" == "compose" ]]; then
    stop_compose
  else
    stop_bare
  fi
  
  # Восстанавливаем данные
  rm -rf mediawiki_db_persistent mediawiki_data
  cp -r "$BACKUP_PATH/mediawiki_db_persistent" ./
  cp -r "$BACKUP_PATH/mediawiki_data" ./
  
  # Запускаем MediaWiki
  if [[ "${MODE}" == "compose" ]]; then
    start_compose
  else
    start_bare
  fi
  
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
