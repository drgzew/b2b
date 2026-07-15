
# Парсинг файлов ВКР и научных публикаций ТюмГУ

Файлы:

- `parsing/docs/sources.md` - Перечень источников файлов;
- `parsing/parsers/openalex.ipynb` - Jypiter-блокнот OpenAlex-парсера;
- `parsing/parsers/openalex.py` - Код OpenAlex-парсера.

**ВНИМАНИЕ!** *Не коммитьте в публичный репозиторий файлы ВКР.*

## Парсинг публикаций из OpenAlex

```cmd
cd parsing
python -m parsers.openalex
```

Созадутся файлы:

- `parsing/data/raw/openalex.json` - Описание найденных статей в формате JSON;
- `parsing/data/pdfs/` - Папка со скачанными статьями в формате PDF;
- `parsing/docs/taxonomy.md` - Описание таксономии OpenAlex в формате Markdown;
- `parsing/docs/taxonomy.json` - Описание таксономии OpenAlex в формате JSON.

## Парсинг ВКР из библиотеки ТюмГУ

```cmd
cd parsing
python -m parsers.libtheses
```

Ничего не создастся, так как сайт библиотеки приказал долго жить.

## Нормализация публикаций и ВКР к формату артефакта

```cmd
cd parsing
python -m scripts.normalize
```

Создастся файл:

`parsing/data/normalized.json` - Артефакты в формате JSON.

## Импорт данных в базу данных

Два способа — выбрать любой, оба используют одну и ту же логику импорта
(`backend/app/importer.py`), результат идентичен.

### Способ 1 — без консоли, через админку

1. Войти в интерфейс под ролью `admin`.
2. На странице администрирования выбрать `parsing/data/normalized.json` и
   нажать «Импортировать» (дёргает `POST /admin/import`, файл передаётся
   через форму — `multipart/form-data`).
3. В ответ придёт статистика импорта (сколько добавлено, сколько тегов
   создано, тексты первых ошибок, если были) — то же самое, что раньше было
   видно только в консоли.

Опция `wipe` (чекбокс «очистить базу перед импортом») необратима — использовать
только на действительно пустой/тестовой базе.

### Способ 2 — через консоль (как раньше)

Удалить ранее созданные контейнеры:
```cmd
docker-compose down --volumes --rmi all
```

Поднять контейнеры:

```cmd
docker-compose up
```

Выполнить в другом терминале:

```cmd
docker-compose exec db pg_isready -U app -d app
docker exec b2b-backend-1 mkdir -p /data
docker cp parsing b2b-backend-1:/data
docker cp backend b2b-backend-1:/data
docker exec -it b2b-backend-1 bash
cd /data
python -m parsing.scripts.import --wipe --file parsing/data/normalized.json
exit
docker cp b2b-backend-1:/data/data-report.md parsing/
docker compose exec backend python scripts/seed.py
```

**Порядок важен, но теперь не критичен**: раньше `scripts/seed.py`, запущенный
после импорта, тихо стирал только что импортированные реальные артефакты
(TRUNCATE затрагивал `artifact`/`author`/`tag`) — это исправлено: `seed.py`
больше не трогает данные парсера, только свои демо-сущности (партнёров,
подписки, демо-пользователей). Можно запускать `seed.py` многократно —
повторный запуск не плодит дубли ни демо-данных, ни тегов.

Проверка функционала:

```cmd
curl http://localhost:8000/artifacts
curl http://localhost:8000/artifacts/1
curl http://localhost:8000/tags
```

Создастся файл:

`parsing/data-report.md` - Отчёт о наполнении базы данных.
