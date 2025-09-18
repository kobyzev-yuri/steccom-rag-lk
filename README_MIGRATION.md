## Миграция проекта на другую Ubuntu-машину (Wiki + API)

Ниже — минимальные шаги, чтобы развернуть MediaWiki «as is» и (опционально) опубликовать KB из проекта на новой машине.

### 1. Подготовка окружения
```bash
sudo apt update && sudo apt install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER && newgrp docker
docker ps
```

### 2. Клонирование проекта
```bash
git clone <ВАШ_REPO_URL>
cd steccom
```

### 3. Запуск MediaWiki «as is»
```bash
chmod +x wiki.bash
./wiki.bash start
./wiki.bash status
```
Откройте `http://localhost:8080/`. Если главная открывается (200 OK), стили — `text/css`, картинки — `image/png`, значит всё готово.

Если вид «ломается»: выполните `./wiki.bash purge` и перезагрузите страницу с очисткой кэша (Ctrl+Shift+R).

### 4. Перенос контента (опционально)
- Если нужно перенести загруженные файлы (картинки), перенесите папку `mediawiki_data` в корень проекта (она монтируется как `/var/www/html/images`).
- Если у вас есть SQLite БД из старой машины, положите каталог `mediawiki_db` (с файлом `mediawiki.sqlite`) в корень проекта и пере‑запустите контейнер:
```bash
docker rm -f steccom-mediawiki
docker run -d \
  --name steccom-mediawiki \
  -p 8080:80 \
  -v "$(pwd)/mediawiki_db:/var/www/html/data" \
  -v "$(pwd)/mediawiki_data:/var/www/html/images" \
  -v "$(pwd)/mediawiki/LocalSettings.php:/var/www/html/LocalSettings.php:ro" \
  --restart unless-stopped \
  mediawiki:1.39
./wiki.bash status
```

Если SQLite БД не переносите — вики поднимется «чистой» и вы можете заново опубликовать KB (см. ниже).

### 5. Публикация KB в Wiki через FastAPI
1) Поднимите FastAPI (см. `README_API.md`), получите JWT токен.
2) Выполните:
```bash
TOKEN="<ваш токен>" ./wiki.bash publish \
  --user admin --pass Admin123456789 \
  --glob "docs/kb/*.json"
```

### 6. Типовые проблемы
- Docker недоступен: `sudo systemctl enable --now docker` и проверьте `docker ps`.
- Порт 8080 занят: освободите порт (`sudo ss -lntp | grep :8080`) или измените переменную `PORT` в `wiki.bash`.
- 500 на `/`: пересоздайте БД по инструкции в `README_MEDIAWIKI.md` (раздел «Полная переустановка»).
- Стили/картинки не грузятся: проверьте блок путей в `mediawiki/LocalSettings.php` и сделайте `./wiki.bash purge`.

### 7. Полезные команды
```bash
./wiki.bash start
./wiki.bash status
./wiki.bash purge
./wiki.bash publish --user admin --pass Admin123456789 --glob "docs/kb/*.json"
./wiki.bash restart
./wiki.bash stop
```



