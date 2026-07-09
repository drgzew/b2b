# API-контракт — Подписка на университет

Черновик для согласования с фронтом. Базовый URL (локально): `http://localhost:8000`

Все защищённые эндпоинты требуют заголовок:
```
Authorization: Bearer <access_token>
```

---

## Аутентификация

### `POST /auth/login`
Публичный. Логин по email/паролю, единый для партнёров и кураторов.

**Request**
```json
{ "email": "gpn@demo.ru", "password": "pass123" }
```

**Response 200**
```json
{ "access_token": "eyJ...", "role": "partner" }
```
`role` — `"partner"` или `"curator"`.

**Response 401** — неверный email или пароль (намеренно одинаковая ошибка для обоих случаев).

Токен живёт 24 часа (пилотная настройка, см. `ACCESS_TOKEN_EXPIRE_MINUTES` в `security.py`).

---

## Партнёрские эндпоинты

Все требуют токен с `role: partner`. При обращении к чужим данным (не своей подписке) — `404`, не `403`, чтобы не подтверждать сам факт существования чужого id.

### `GET /partner/me`
Данные текущего партнёра.

**Response 200**
```json
{ "id": 1, "name": "Газпромнефть — R&D", "contact_email": "rnd@gpn-demo.ru" }
```

### `GET /partner/subscriptions`
Список подписок партнёра.

**Response 200**
```json
[
  { "id": 1, "name": "Нефтегаз и цифровизация", "tags": ["нефтегаз", "цифровизация", "энергетика"] }
]
```

### `GET /partner/subscriptions/{id}/digest`
Дайджест по конкретной подписке. Только `curator_status == "approved"`, только `relevance > 0`, сортировка по убыванию релевантности.

**Response 200**
```json
[
  {
    "artifact": {
      "id": 2, "title": "Цифровой двойник насосной станции", "type": "vkr",
      "annotation": "...", "file_path": null,
      "curator_status": "approved", "access_level": "full",
      "author_name": "А. Смирнова", "created_at": "2026-...",
      "tags": ["цифровизация", "нефтегаз"]
    },
    "relevance": 0.667
  }
]
```
`relevance` — индекс Жаккара (пересечение / объединение тегов подписки и артефакта), 0.0–1.0.

**Response 404** — подписка не найдена или принадлежит другому партнёру.

### `POST /partner/requests`
Создать запрос по артефакту.

**Request**
```json
{ "artifact_id": 2, "type": "full_text" }
```
`type`: `"full_text" | "internship" | "rnd"`

**Response 200**
```json
{ "id": 1, "artifact_id": 2, "partner_id": 1, "type": "full_text", "status": "sent", "created_at": "2026-..." }
```

---

## Кураторские эндпоинты

Все требуют токен с `role: curator`.

### `GET /curator/artifacts?status=draft|approved|rejected`
Очередь модерации. Параметр `status` опционален — без него возвращаются все артефакты.

### `POST /curator/artifacts/{id}/approve`
Переводит `curator_status` в `approved`. С этого момента артефакт может попасть в дайджест партнёров.

### `POST /curator/artifacts/{id}/reject`
Переводит `curator_status` в `rejected`.

### `PUT /curator/artifacts/{id}/tags`
Полностью заменяет теги артефакта (не добавляет, а перезаписывает список).

**Request**
```json
{ "tag_ids": [1, 3, 5] }
```
**Response 400** — если среди `tag_ids` есть несуществующие id.

### `GET /curator/requests`
Очередь всех запросов от партнёров (по всем артефактам и партнёрам).

### `PATCH /curator/requests/{id}`
Меняет статус запроса.

**Request**
```json
{ "status": "in_progress" }
```
`status`: `"in_progress" | "done"`

---

## Прочее (без авторизации)

- `GET /health` → `{"status": "ok"}`
- `GET /artifacts`, `POST /artifacts`, `GET /artifacts/{id}` — базовые CRUD-эндпоинты без ролевой модели, оставлены для внутренней загрузки контента. Не путать с `/curator/artifacts` — тот с фильтром по статусу и предназначен для интерфейса куратора.

---

## Коды ошибок (сквозные для всех защищённых эндпоинтов)

| Код | Когда |
|---|---|
| 401 | нет токена, невалидный/просроченный токен, неверный логин/пароль |
| 403 | токен валиден, но роль не подходит под эндпоинт |
| 404 | сущность не найдена или принадлежит не тому партнёру, который спрашивает |

## Открытые вопросы к фронту

1. `GET /artifacts` и `POST /artifacts` сейчас без авторизации — оставляем так для пилота (загрузка контента через отдельный внутренний процесс) или тоже закрываем ролью?
2. Нужен ли на фронте отдельный экран "все теги" (`GET /tags`)? Сейчас такого эндпоинта нет — для `PUT /curator/artifacts/{id}/tags` фронту нужно знать список `tag_id` заранее.
3. Нужна ли пагинация на `GET /curator/artifacts` и `GET /curator/requests`? Сейчас отдают всё целиком — ок для 50 артефактов пилота, но стоит зафиксировать до роста объёма.
