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

Требует `parsing/data/normalized.json` (генерируется парсером, см.
[`parsing/README.md`](./parsing/README.md) — «Импорт данных в базу данных»).
Файл не версионируется в git; `docker-compose.yml` монтирует `parsing/data`
в контейнер `backend`, так что скрипт находит его сам:

```bash
docker compose exec backend python scripts/seed.py
```

Если файла нет вообще — скрипт откажется наполнять базу и явно скажет,
что делать, **не тронув** существующие данные (раньше в этом случае база
тихо очищалась, оставляя проект без единого логина).

Создаст теги, авторов и артефакты из `normalized.json`, ~20 преподавателей,
3 партнёров с тематическими подписками и пользователей для входа:

| Email | Пароль | Роль |
|---|---|---|
| gpn@demo.ru | pass123 | partner (Газпромнефть) |
| yandex@demo.ru | pass123 | partner (Яндекс) |
| eco@demo.ru | pass123 | partner (ЗапСибЭкоЦентр) |
| curator@demo.ru | pass123 | curator |
| admin@demo.ru | pass123 | admin |

Логины авторов/студентов и преподавателей — печатаются в конце вывода
скрипта (сгенерированы из реальных ФИО в `normalized.json`, поэтому список
меняется от запуска к запуску вместе с исходными данными).

## Эндпоинты

Полный контракт с примерами запросов/ответов — в [`docs/api-contract.md`](./docs/api-contract.md). Там же ⚠️ **breaking change**: поле артефакта `access_level` переименовано в `read_policy` (`open | requires_approval`, дефолт `requires_approval`).

Коротко:
- `GET /health` — healthcheck
- `POST /auth/login` — логин, возвращает JWT
- `GET /artifacts`, `POST /artifacts`, `GET /artifacts/{id}` — базовый CRUD без авторизации
- `GET /partner/me`, `.../subscriptions`, `.../subscriptions/{id}/digest` (с `can_read` на каждый артефакт), `.../requests`, `.../artifacts/{id}/read` (открыть полный текст — редирект для ВКР, PDF для статьи/доклада), `.../internships`, `.../favorites` — партнёрские (`partner`)
- `GET /curator/artifacts`, `.../approve|reject`, `.../tags`, `GET /curator/requests`, `POST /curator/requests/{id}/decision` (разрешить/нет на full_text-запрос) — кураторские (`curator`/`admin`)
- `GET /author/me`, `.../artifacts`, `PATCH .../artifacts/{id}/read-policy`, `GET .../requests` (входящие запросы на чтение — с именем компании и работы), `POST .../requests/{id}/decision` — кабинет автора (`author`)
- `GET /authors/{id}`, `GET /teachers/{id}` — кликабельные профили автора/руководителя ВКР (доступны `partner`/`curator`/`admin`; партнёру — урезанный профиль без email/даты рождения)
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
- `POST /authors/sso/tumgu` — мок, а не реальный SSO/LDAP ТюмГУ. Тело функции `parse_tumgu_profile()` в `app/sso.py` — единственное место, которое надо будет заменить
- Профиль преподавателя (`Teacher`) — тоже демо-данные, без входа/кабинета; наполняется только через `seed.py`
- Доступ к полному тексту выдаётся per-partner (`PartnerArtifactAccess`) — один одобренный запрос открывает текст только тому партнёру, который его запросил, не всем сразу
