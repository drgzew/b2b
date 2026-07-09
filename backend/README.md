# Подписка на университет — API (MVP-скелет)

## Запуск

```bash
docker compose up --build
```

Поднимется:
- `db` — PostgreSQL с pgvector (`pgvector/pgvector:pg16`), порт `5432`
- `api` — FastAPI, порт `8000`
- `frontend` — временный пустой контейнер-заглушка (чтобы `docker compose up` поднимал всё одной командой)

Таблицы создаются автоматически при старте API (`SQLModel.metadata.create_all`).

## Проверка

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Наполнить тестовыми данными

```bash
docker compose exec api python scripts/seed.py
```

Создаст 5 фейковых артефактов, 1 партнёра и 3 подписки.

## Эндпоинты

- `GET /health` — healthcheck
- `GET /artifacts` — список артефактов
- `POST /artifacts` — создать артефакт (см. `app/schemas.py: ArtifactCreate`)
- `GET /artifacts/{id}` — получить артефакт по id

Документация Swagger: http://localhost:8000/docs

## Известные TODO

- `Artifact.embedding` — временно строка, заменить на `pgvector.sqlalchemy.Vector` при подключении семантического поиска
- Таблицы создаются через `create_all` — при усложнении схемы стоит перейти на Alembic-миграции
