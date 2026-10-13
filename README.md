# Arena Play

Статический сайт любительской хоккейной команды Arena Play.

## Локальная проверка

```sh
docker build -t arenaplayteam:check .
bash scripts/smoke-test.sh arenaplayteam:check
```

Для простого локального просмотра можно запустить `python3 -m http.server 8080`, но браузер должен поддерживать ES modules.

## Данные

Состав и статистика находятся в `data/team.js`; расписание хранится в `data/schedule.json`. Workflow `Update schedule` ежедневно в 07:00, 13:00 и 19:00 по Москве читает страницу клуба Arena Play на ЛХЛ-77 и обновляет расписание и результаты. При изменении данных он делает коммит и запускает сборку и деплой сайта. Workflow можно запустить вручную в GitHub Actions.

Ссылки на трансляции ищутся в публичном каталоге VK Видео ЛХЛ-77 по названиям обеих команд и дате публикации (от трёх дней до матча до следующего дня). Старые встречи и хайлайты исключаются. Если подходящей записи нет или VK недоступен, показывается ссылка на все видео. Уже сохранённые ссылки на конкретные записи сохраняются.

Парсер можно проверить локально командами `python3 -m unittest discover -s scripts -p 'test_*.py'` и `python3 scripts/sync_schedule.py`. Для локального просмотра используйте HTTP-сервер из корня репозитория, чтобы браузер мог загрузить JSON-файл расписания.

## GitHub Actions

Создать Environment `production` и добавить секреты `DOCKER_USERNAME`, `DOCKER_TOKEN`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PORT`, `DEPLOY_SSH_KEY`, `DEPLOY_HOST_PROJECT_PATH`. Публичный ключ сервера закреплён в `deploy/known_hosts`. Push в `master` запускает сборку и деплой.

Docker Hub token не хранить в репозитории. Токен, опубликованный в переписке, необходимо отозвать и заменить.

## Сервер

Проект разворачивается в `/home/mr17dom1/projects/arenaplayru` и подключается к существующей сети Traefik `housekpr-network`. CI/CD публикует образ `lobanovsky/arenaplayru:<короткий SHA>` и записывает этот SHA как `TAG` в серверный `.env`. Маршрут Traefik всегда включён в `compose.yaml`.

На сервере достаточно обычных команд:

```sh
cd /home/mr17dom1/projects/arenaplayru
docker compose pull
docker compose up -d
docker compose ps
```

`docker compose down` останавливает сайт; повторный `docker compose up -d` запускает его с тем же образом и настройками.
