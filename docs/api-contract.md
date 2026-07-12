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
`role` — `"partner"`, `"curator"` или `"admin"`. Роль `admin` имеет доступ ко всем эндпоинтам `/curator/*` и `/authors/*` в дополнение к своим собственным `/admin/*` — отдельных дублирующих ручек для админа нет.

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
      "created_at": "2026-...", "tags": ["цифровизация", "нефтегаз"],
      "author_id": 2, "author_name": "Волкова Ольга"
    },
    "relevance": 0.667
  }
]
```
`relevance` — индекс Жаккара (пересечение / объединение тегов подписки и артефакта), 0.0–1.0.

`author_id` — кликабельная ссылка на профиль: фронт делает `GET /authors/{author_id}`, чтобы открыть карточку (см. раздел «Профили авторов» ниже).

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

## Профили авторов

Реализует пункты «карточка пользователя» и «доступ к профилям должен быть кликабельным».
Объём данных в ответе зависит от роли того, кто спрашивает.

### `GET /authors/{id}`
Доступен `partner`, `curator`, `admin`. Именно этот эндпоинт открывается по клику на `author_name`/`author_id` из карточки артефакта или дайджеста.

**Response 200 (для curator/admin — полный профиль)**
```json
{
  "id": 2, "email": "smirnova.a@study.utmn.ru", "full_name": "Волкова Ольга",
  "photo_url": "https://avatars.example.tyumsu.ru/....jpg",
  "birth_date": "2000-04-01", "program": "Нефтегазовое дело",
  "job_status": "employed"
}
```

**Response 200 (для partner — урезанный профиль)**
```json
{
  "id": 2, "email": null, "full_name": "Волкова Ольга",
  "photo_url": "https://avatars.example.tyumsu.ru/....jpg",
  "birth_date": null, "program": "Нефтегазовое дело",
  "job_status": "employed"
}
```
`email` и `birth_date` намеренно обнулены для партнёра — принцип минимизации персональных данных: партнёру для решения о стажировке/НИОКР email и дата рождения не нужны. Форма ответа одна и та же (не два разных эндпоинта), фронту не нужно ветвиться по роли самому.

`job_status`: `"searching" | "not_searching" | "employed"` — актуальный статус по трудоустройству.

### `GET /authors` — только `curator`/`admin`
Список всех авторов, полный профиль у каждого.

### `PATCH /authors/{id}/job-status` — только `curator`/`admin`
**Request**
```json
{ "job_status": "employed" }
```

### `POST /authors/sso/tumgu` — только `curator`/`admin`
«Вход через почту ТюмГУ» — сейчас мок (см. `app/sso.py`), детерминированно генерирует ФИО/фото/дату рождения/направление по email и создаёт или обновляет профиль автора. Реальная интеграция с SSO/LDAP подключится заменой тела одной функции, форма запроса/ответа не изменится.

**Request**
```json
{ "email": "newstudent@study.utmn.ru" }
```
**Response 200** — тот же формат, что у `GET /authors/{id}` для curator/admin.

⚠️ Сейчас у авторов нет собственного логина в систему — этот эндпоинт вызывает куратор/админ в момент занесения работы, а не сам студент. Самостоятельный вход автора и self-service изменение своего `job_status` — вне скоупа пилота, см. открытые вопросы ниже.

---

## Администратор

Роль `admin` — расширение роли `curator`: имеет доступ ко всем эндпоинтам `/curator/*` и `/authors/*` (роль просто добавлена в список разрешённых), плюс собственные эндпоинты управления учётками и партнёрами.

### `GET /admin/users`
Список всех пользователей (без password_hash).

### `POST /admin/users`
**Request**
```json
{ "email": "new@demo.ru", "password": "...", "role": "curator", "partner_id": null }
```
`partner_id` обязателен, если `role == "partner"`.

### `GET /admin/partners`
Список всех партнёров-компаний.

### `POST /admin/partners`
**Request**
```json
{ "name": "Лукойл — Инновации", "contact_email": "i@lukoil-demo.ru" }
```

---

## ⚠️ Breaking change: `access_level` → `read_policy`

Поле артефакта `access_level` (`full | annotation_only | none`) заменено на
`read_policy` (`open | requires_approval`, дефолт `requires_approval` — "запрет
по умолчанию" из новых требований). Аннотация видна всегда независимо от
`read_policy` — это поле только про доступ к полному тексту/файлу.

---

## Профили — преподаватель

### `GET /teachers/{id}`
Публичный внутри системы (любая из ролей `curator|admin|partner`). Кликабельный
профиль руководителя ВКР — так же, как `GET /authors/{id}`.

**Response 200**
```json
{ "id": 1, "full_name": "Королёва Наталья Викторовна", "email": "koroleva.nv@utmn.ru", "department": "ШКН ТюмГУ", "position": "доцент" }
```

Артефакт теперь может ссылаться на руководителя: поля `supervisor_id` /
`supervisor_name` в `ArtifactRead`, аналогично `author_id`/`author_name`.

---

## Кабинет автора

Требует токен с `role: author`. Учётка привязана к профилю через
`User.author_id` (в пилоте — тот же email, что и университетская почта).

### `GET /author/me` — свой профиль (полный, включая email/дату рождения)

### `PATCH /author/me/job-status`
```json
{ "job_status": "searching" }
```
`searching | not_searching | employed`. Это самостоятельная версия того же
поля, что куратор меняет через `PATCH /authors/{id}/job-status`.

### `GET /author/artifacts` — свои работы

### `PATCH /author/artifacts/{id}/read-policy`
```json
{ "read_policy": "open" }
```
`open | requires_approval`. Меняет политику только для своих артефактов (404
на чужие).

### `GET /author/requests?status=sent|approved|rejected`
Входящие запросы на полный текст по своим работам — с именем компании и
названием работы, а не голыми id.

**Response 200**
```json
[{ "id": 1, "artifact_id": 1, "artifact_title": "Оптимизация буровых растворов",
   "partner_id": 1, "partner_name": "Газпромнефть — R&D", "status": "sent", "created_at": "..." }]
```

### `POST /author/requests/{id}/decision`
Кнопка «разрешить/нет».
```json
{ "approve": true }
```
При `approve: true` партнёру сразу выдаётся доступ именно к этому артефакту
(без изменения `read_policy` на будущее). Повторное решение по уже решённому
запросу — `400`.

---

## Флоу «Запросить полный текст» у партнёра

### `GET /partner/artifacts/{id}/read`
Проверяет, можно ли прямо сейчас читать текст (открыто автором ИЛИ уже выдан
доступ по одобренному запросу).

**Response 200** (доступ есть)
```json
{ "mode": "redirect", "url": "https://vkr.utmn-demo.ru/works/1" }
```
`mode: "redirect"` для ВКР (переход по ссылке), `mode: "pdf"` для статьи/доклада
(открыть PDF).

**Response 403** (доступа нет) — фронт должен предложить `POST /partner/requests`.

### `POST /partner/requests` (уже было, уточнение для `type: "full_text"`)
Если текст уже доступен — `400`, запрос создавать не нужно, сразу `GET /read`.
Если нет — создаётся запрос со статусом `sent`, уходит **одновременно** в
`GET /author/requests` и `GET /curator/requests` — решает тот, кто ответит
первым (`POST /author/requests/{id}/decision` или
`POST /curator/requests/{id}/decision`).

`DigestEntry` в ответе дайджеста теперь содержит `can_read: bool` — фронт
может сразу решить, показывать кнопку «Открыть» или «Запросить», не делая
отдельный запрос на каждый артефакт.

### `POST /curator/requests/{id}/decision`
Та же кнопка «разрешить/нет», что и у автора — равноправна с ней. Старый
`PATCH /curator/requests/{id}` для `type == "full_text"` теперь возвращает
`400` — решение обязано идти через `/decision`, иначе можно было бы выставить
статус `approved`, не выдав реальный доступ.

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
4. **"Вход через ТюмГУ почту" сейчас мок** (`app/sso.py`), и решение "мок или реальный SSO" отложено. Пока `POST /authors/sso/tumgu` вызывается куратором/админом вручную, а не самим студентом — если продукту нужен самостоятельный вход автора (личный кабинет, self-service `job_status`), это отдельная задача на бэкенд, надо явно поставить в план.
5. `PUT /curator/artifacts/{id}/tags` **добавляет** автора в артефакт? Нет — привязка автора сейчас задаётся только при создании (`POST /artifacts` с `author_id`) или напрямую в БД/seed. Если нужен эндпоинт "перепривязать автора у существующего артефакта" — не реализован, стоит уточнить, нужен ли он кураторам.
