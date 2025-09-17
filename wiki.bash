#!/usr/bin/env bash
set -euo pipefail

# Config
IMAGE="mediawiki:1.39"
CONTAINER="steccom-mediawiki"
PORT="8080"
ROOT="$(pwd)"
LS_HOST="${ROOT}/mediawiki/LocalSettings.php"        # эталонный LocalSettings из репо
IMAGES_HOST="${ROOT}/mediawiki_data"                  # папка для загрузок
API_URL="http://localhost:8000"                       # FastAPI (для publish)

usage() {
  cat <<EOF
Usage: $0 <command> [options]

Commands:
  start             Запустить MediaWiki контейнер (корневые пути, без /w)
  stop              Остановить и удалить контейнер
  restart           Перезапустить контейнер (stop -> start)
  status            Показать статус и проверить CSS/картинки
  purge             Очистить кэш Wiki и purge главной
  publish           Опубликовать KB в MediaWiki через FastAPI (нужен $TOKEN)
                    Options: --user admin --pass Admin123456789 --glob "docs/kb/*.json"

Examples:
  $0 start
  $0 status
  TOKEN="..." $0 publish --user admin --pass Admin123456789 --glob "docs/kb/*.json"
EOF
}

ensure_requirements() {
  command -v docker >/dev/null 2>&1 || { echo "docker not found"; exit 1; }
  mkdir -p "${IMAGES_HOST}"
  if [[ ! -f "${LS_HOST}" ]]; then
    echo "LocalSettings не найден: ${LS_HOST}"
    exit 1
  fi
}

start() {
  ensure_requirements
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
  docker run -d \
    --name "${CONTAINER}" \
    -p "${PORT}:80" \
    -v "${IMAGES_HOST}:/var/www/html/images" \
    -v "${LS_HOST}:/var/www/html/LocalSettings.php:ro" \
    --restart unless-stopped \
    "${IMAGE}"

  echo "⏳ Жду поднятие сервера..."
  sleep 5
  # Purge главной
  curl -s "http://localhost:${PORT}/index.php?title=Заглавная_страница&action=purge" >/dev/null || true
  status
}

stop() {
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
  echo "🛑 ${CONTAINER} остановлен"
}

restart() {
  stop
  start
}

purge() {
  # Очистка кэша и purge главной
  docker exec "${CONTAINER}" rm -rf /var/www/html/cache/* >/dev/null 2>&1 || true
  curl -s "http://localhost:${PORT}/index.php?title=Заглавная_страница&action=purge" >/dev/null || true
  echo "✅ Кэш очищен, главная обновлена"
}

status() {
  echo "🐳 Контейнеры:"
  docker ps --filter "name=${CONTAINER}"
  echo
  echo "🔎 Проверка CSS (ожидается Content-Type: text/css)"
  curl -I "http://localhost:${PORT}/load.php?lang=ru&modules=skins.vector.styles.legacy&only=styles&skin=vector" | sed -n '1,10p' || true
  echo
  echo "🖼  Проверка картинки (ожидается image/png)"
  curl -I "http://localhost:${PORT}/resources/assets/poweredby_mediawiki_88x31.png" | sed -n '1,10p' || true
  echo
  echo "🌐 Откройте в браузере: http://localhost:${PORT}/"
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
    -d "{\"wiki_url\":\"http://localhost:${PORT}/w/api.php\",\"username\":\"${USER}\",\"password\":\"${PASS}\",\"kb_glob\":\"${GLOB}\"}" | jq . || true
}

cmd="${1:-}"
shift || true

case "${cmd}" in
  start)   start ;;
  stop)    stop ;;
  restart) restart ;;
  status)  status ;;
  purge)   purge ;;
  publish) publish "$@" ;;
  ""|help|-h|--help) usage ;;
  *) echo "Unknown command: ${cmd}"; usage; exit 1 ;;
esac

#!/usr/bin/env bash
set -euo pipefail

# Config
IMAGE="mediawiki:1.39"
CONTAINER="steccom-mediawiki"
PORT="8080"
ROOT="$(pwd)"
LS_HOST="${ROOT}/mediawiki/LocalSettings.php"        # эталонный LocalSettings из репо
IMAGES_HOST="${ROOT}/mediawiki_data"                  # папка для загрузок
API_URL="http://localhost:8000"                       # FastAPI (для publish)

usage() {
  cat <<EOF
Usage: $0 <command> [options]

Commands:
  start             Запустить MediaWiki контейнер (корневые пути, без /w)
  stop              Остановить и удалить контейнер
  restart           Перезапустить контейнер (stop -> start)
  status            Показать статус и проверить CSS/картинки
  purge             Очистить кэш Wiki и purge главной
  publish           Опубликовать KB в MediaWiki через FastAPI (нужен \$TOKEN)
                    Options: --user admin --pass Admin123456789 --glob "docs/kb/*.json"

Examples:
  $0 start
  $0 status
  TOKEN="..." $0 publish --user admin --pass Admin123456789 --glob "docs/kb/*.json"
EOF
}

ensure_requirements() {
  command -v docker >/dev/null 2>&1 || { echo "docker not found"; exit 1; }
  mkdir -p "${IMAGES_HOST}"
  if [[ ! -f "${LS_HOST}" ]]; then
    echo "LocalSettings не найден: ${LS_HOST}"
    exit 1
  fi
}

start() {
  ensure_requirements
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
  docker run -d \
    --name "${CONTAINER}" \
    -p "${PORT}:80" \
    -v "${IMAGES_HOST}:/var/www/html/images" \
    -v "${LS_HOST}:/var/www/html/LocalSettings.php:ro" \
    --restart unless-stopped \
    "${IMAGE}"

  echo "⏳ Жду поднятие сервера..."
  sleep 5
  # Purge главной
  curl -s "http://localhost:${PORT}/index.php?title=Заглавная_страница&action=purge" >/dev/null || true
  status
}

stop() {
  docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true
  echo "🛑 ${CONTAINER} остановлен"
}

restart() {
  stop
  start
}

purge() {
  # Очистка кэша и purge главной
  docker exec "${CONTAINER}" rm -rf /var/www/html/cache/* >/dev/null 2>&1 || true
  curl -s "http://localhost:${PORT}/index.php?title=Заглавная_страница&action=purge" >/dev/null || true
  echo "✅ Кэш очищен, главная обновлена"
}

status() {
  echo "🐳 Контейнеры:"
  docker ps --filter "name=${CONTAINER}"
  echo
  echo "🔎 Проверка CSS (ожидается Content-Type: text/css)"
  curl -I "http://localhost:${PORT}/load.php?lang=ru&modules=skins.vector.styles.legacy&only=styles&skin=vector" | sed -n '1,10p' || true
  echo
  echo "🖼  Проверка картинки (ожидается image/png)"
  curl -I "http://localhost:${PORT}/resources/assets/poweredby_mediawiki_88x31.png" | sed -n '1,10p' || true
  echo
  echo "🌐 Откройте в браузере: http://localhost:${PORT}/"
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
    echo '  TOKEN="..." '"$0"' publish --user admin --pass Admin123456789 --glob "docs/kb/*.json"'
    exit 1
  fi

  echo "📤 Публикация KB → MediaWiki через FastAPI..."
  curl -s -X POST "${API_URL}/wiki/publish" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"wiki_url\":\"http://localhost:${PORT}/w/api.php\",\"username\":\"${USER}\",\"password\":\"${PASS}\",\"kb_glob\":\"${GLOB}\"}" | jq . || true
}

cmd="${1:-}"
shift || true

case "${cmd}" in
  start)   start ;;
  stop)    stop ;;
  restart) restart ;;
  status)  status ;;
  purge)   purge ;;
  publish) publish "$@" ;;
  ""|help|-h|--help) usage ;;
  *) echo "Unknown command: ${cmd}"; usage; exit 1 ;;
esac
