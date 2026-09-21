# Arena Play

Статический сайт любительской хоккейной команды Arena Play.

## Локальная проверка

```sh
docker build -t arenaplayteam:check .
bash scripts/smoke-test.sh arenaplayteam:check
```

Для простого локального просмотра можно запустить `python3 -m http.server 8080`, но браузер должен поддерживать ES modules.

## Данные

Состав, матчи и статистика находятся в `data/team.js`. После изменения файла сайт собирается обычным push в `master`.

## GitHub Actions

Создать Environment `production` и добавить секреты `DOCKER_USERNAME`, `DOCKER_TOKEN`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PORT`, `DEPLOY_SSH_KEY`, `DEPLOY_HOST_PROJECT_PATH`. Публичный ключ сервера закреплён в `deploy/known_hosts`. Push в `master` запускает сборку и деплой.

Docker Hub token не хранить в репозитории. Токен, опубликованный в переписке, необходимо отозвать и заменить.

## Сервер

Проект разворачивается в `/home/mr17dom1/projects/arenaplayru` и подключается к существующей сети Traefik `housekpr-network`. CI/CD записывает в корень настоящий `compose.yaml` и `.env` с текущим Docker-образом. Маршрут Traefik всегда включён в `compose.yaml`.

На сервере достаточно обычных команд:

```sh
cd /home/mr17dom1/projects/arenaplayru
docker compose pull
docker compose up -d
docker compose ps
```

`docker compose down` останавливает сайт; повторный `docker compose up -d` запускает его с тем же образом и настройками.
