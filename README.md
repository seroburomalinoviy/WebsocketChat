# WebsocketChat

Стек:  FastAPI, PostgreSQL, SQLalchemy, Alembic, WebSocket 

## Запуск проекта

1) Собрать docker

`docker compose up -d --build`

2) Применить миграции

`docker compose exec web alembic upgrade head`

Чат будет доступен по адресу `0.0.0.0:8000/`

Для получения истории сообщений чата:

`curl 0.0.0.0:8000/history/{chat_id}`
