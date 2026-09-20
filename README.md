# Arena Play

Статический сайт любительской хоккейной команды Arena Play.

## Локальная проверка

```sh
docker build -t arenaplayteam:check .
bash scripts/smoke-test.sh arenaplayteam:check
```

Для простого локального просмотра можно запустить `python3 -m http.server 8080`, но браузер должен поддерживать ES modules.

## Данные

Состав, матчи и статистика находятся в `data/team.js`. После изменения файла сайт собирается обычным push в `main`.

## GitHub Actions

Создать Environment `production` и добавить секреты `DOCKER_USERNAME`, `DOCKER_TOKEN`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PORT`, `DEPLOY_SSH_KEY`, `DEPLOY_KNOWN_HOSTS`, `DEPLOY_HOST_PROJECT_PATH`. Затем создать repository variable `DEPLOY_ENABLED=true`.

Docker Hub token не хранить в репозитории. Токен, опубликованный в переписке, необходимо отозвать и заменить.

## Сервер

Проект разворачивается в `/home/mr17dom1/projects/arenaplayru` и подключается к существующей сети Traefik `housekpr-network`. После первого успешного деплоя включить маршрут в `routing.env`:

```sh
TRAEFIK_ENABLED=true
```

До включения маршрута проверить, что DNS-записи `@` и `www` домена указывают на сервер.

