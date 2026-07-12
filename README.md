# Подписка на университет — API (MVP-скелет)

## Настройка перед первым запуском

```bash
cp .env.example .env
```

```cmd
copy .env.example .env
```

Затем сгенерировать секрет и вписать его в `.env` (переменная `SECRET_KEY`):

```bash
openssl rand -hex 32
```

```cmd
docker compose build backend
docker compose run --rm backend python -c "import secrets; print(secrets.token_hex(32))"
```

Без этого шага сработает дев-заглушка из `docker-compose.yml` — этого достаточно для локальной разработки, но не для пилота с реальным доступом партнёров.

## Запуск

```bash
docker compose up --build
```

Поднимется:
- `db` — PostgreSQL с pgvector (`pgvector/pgvector:pg16`), порт `5432`
- `backend` — FastAPI, порт `8000`
- `frontend` — временный пустой контейнер-заглушка (чтобы `docker compose up` поднимал всё одной командой)

Таблицы создаются автоматически при старте API (`SQLModel.metadata.create_all`).

## Проверка

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## Наполнить тестовыми данными

```bash
docker compose exec backend python scripts/seed.py
```

Создаст 5 артефактов, 5 авторов (профили сгенерированы через мок "входа по почте ТюмГУ", см. `app/sso.py`), 2 партнёров (ГПН, СИБУР) с подписками и 4 пользователей для входа:

| Email | Пароль | Роль |
|---|---|---|
| gpn@demo.ru | pass123 | partner (Газпромнефть) |
| sibur@demo.ru | pass123 | partner (СИБУР) |
| curator@demo.ru | pass123 | curator |
| admin@demo.ru | pass123 | admin |

## Эндпоинты

Полный контракт с примерами запросов/ответов — в [`docs/api-contract.md`](./docs/api-contract.md).

Коротко:
- `GET /health` — healthcheck
- `POST /auth/login` — логин, возвращает JWT
- `GET /artifacts`, `POST /artifacts`, `GET /artifacts/{id}` — базовый CRUD без авторизации
- `GET /partner/me`, `GET /partner/subscriptions`, `GET /partner/subscriptions/{id}/digest`, `POST /partner/requests` — партнёрские (нужен токен с ролью `partner`)
- `GET /curator/artifacts`, `POST /curator/artifacts/{id}/approve|reject`, `PUT /curator/artifacts/{id}/tags`, `GET /curator/requests`, `PATCH /curator/requests/{id}` — кураторские (нужен токен с ролью `curator` или `admin`)
- `GET /authors`, `GET /authors/{id}`, `PATCH /authors/{id}/job-status`, `POST /authors/sso/tumgu` — профили авторов. `GET /authors/{id}` доступен и партнёру (урезанный профиль без email/даты рождения), остальное — только `curator`/`admin`
- `GET/POST /admin/users`, `GET/POST /admin/partners` — только `admin`. Роль `admin` также имеет полный доступ ко всем эндпоинтам `/curator/*` и `/authors/*`

Документация Swagger: http://localhost:8000/docs — там же можно авторизоваться (кнопка Authorize, вставить `Bearer <token>`) и дёргать защищённые эндпоинты прямо из интерфейса.

## Быстрая проверка через curl

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"gpn@demo.ru","password":"pass123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl http://localhost:8000/partner/subscriptions -H "Authorization: Bearer $TOKEN"
```

## Известные TODO

- `Artifact.embedding` — временно строка, заменить на `pgvector.sqlalchemy.Vector` при подключении семантического поиска
- Таблицы создаются через `create_all` — при усложнении схемы стоит перейти на Alembic-миграции
- `GET/POST /artifacts` пока без авторизации — открытый вопрос к фронту в `docs/api-contract.md`
- Нет эндпоинта `GET /tags` — фронту неоткуда взять список `tag_id` для `PUT /curator/artifacts/{id}/tags`, кроме как из тегов уже загруженных артефактов
- `POST /authors/sso/tumgu` — мок, а не реальный SSO/LDAP ТюмГУ (решение о реальной интеграции ещё не принято). Тело функции `parse_tumgu_profile()` в `app/sso.py` — единственное место, которое надо будет заменить
- У авторов нет собственного логина/личного кабинета — профиль заводит куратор/админ, self-service изменение `job_status` самим автором не реализовано
