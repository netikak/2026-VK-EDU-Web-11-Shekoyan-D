# 2026-VK-EDU-Web-11-Shekoyan-D
# AskPupkin 

Версия сайта вопросов и ответов для чтения. Главная страница показывает новые вопросы,
`/hot/` — лучшие по сумме оценок, `/tag/<tag>/` — вопросы по тегу,
`/question/<id>/` — вопрос и страницы его ответов.

## Запуск через Docker

Из этой папки:

```sh
docker compose --env-file .env.docker up --build -d
docker compose --env-file .env.docker exec web python manage.py createsuperuser
docker compose --env-file .env.docker exec web python manage.py fill_db 10001
```

Сайт доступен на http://localhost:8000/, админка — на http://localhost:8000/admin/.
Миграции применяются при запуске. PostgreSQL хранит данные в именованном томе Compose.
Команда наполнения необязательна. Пустая база поддерживается.

## Локальный запуск

Нужны Python 3.12 и запущенный PostgreSQL. Создайте роль и базу под учётной записью
администратора PostgreSQL. Для имени роли и базы используйте значения `DB_USER` и
`DB_NAME` из `.env.local`. Для пароля роли используйте значение `DB_PASSWORD`.

```sh
createuser --createdb --pwprompt askpupkin_hw3
createdb --owner=askpupkin_hw3 askpupkin_hw3

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Если локальные файлы окружения отсутствуют, скопируйте `.env.example` в
`.env.local` и `.env.docker`. Задайте секретный ключ и пароль БД.
Для Docker установите `DB_HOST=db`. Django Debug Toolbar подключается только
при `DEBUG=True`.

## Наполнение и проверки

```sh
python manage.py fill_db 2
python manage.py test
```

Команда `fill_db <ratio>` добавляет `ratio` пользователей и профилей,
`10 × ratio` вопросов, `100 × ratio` ответов, `ratio` тегов и
`200 × ratio` оценок. Повторный запуск добавляет новую порцию.
Минимум — `2`. При `ratio=1` единственный пользователь и 110 объектов допускают
только 110 уникальных оценок. Для объёма из задания используйте `10001`.
Тестовые пользователи создаются без паролей. Для работы в админке создайте суперпользователя.
Рейтинг вычисляется из оценок, поэтому добавление, редактирование и удаление
оценки в админке отражаются на сайте сразу.
