
# Парсинг файлов ВКР и научных публикаций ТюмГУ

Файлы:

- `parsing/docs/sources.md` - Перечень источников файлов;
- `parsing/parsers/openalex.ipynb` - Jypiter-блокнот OpenAlex-парсера;
- `parsing/parsers/openalex.py` - Код OpenAlex-парсера.

**ВНИМАНИЕ!** *Не коммитьте в публичный репозиторий файлы ВКР.*

## Парсинг публикаций из OpenAlex

```cmd
cd parsing
python -m parsers.openalex -n 1000 --ratio .67
```

Созадутся файлы:

- `parsing/data/raw/openalex.json` - Описание найденных статей в формате JSON;
- `parsing/data/raw/openalex-ru.json` - Описание найденных статей на русском языке в формате JSON;
- `parsing/data/pdfs/` - Папка со скачанными статьями в формате PDF;
- `parsing/docs/taxonomy.md` - Описание таксономии OpenAlex в формате Markdown;
- `parsing/docs/taxonomy.json` - Описание таксономии OpenAlex в формате JSON.

## Парсинг ВКР из библиотеки ТюмГУ

```cmd
cd parsing
python -m parsers.libtheses --number=50
```

Создастся файл:

`parsing/data/raw/libtheses.json` - Описание найденных ВКР в формате JSON.

## Парсинг магистерских диссертаций из библиотеки ТюмГУ

```cmd
cd parsing
python -m parsers.repotheses --number=50
```

Создастся файл:

`parsing/data/raw/repotheses.json` - Описание найденных магистерских диссертаций в формате JSON.

## Нормализация публикаций и ВКР к формату артефакта

```cmd
cd parsing
python -m scripts.normalize
```

Создастся файл:

`parsing/data/normalized.json` - Артефакты в формате JSON.

## Импорт данных в базу данных

`docker-compose.yml` монтирует `parsing/data` в контейнер `backend` по пути
`/data` (read-only) — `scripts/seed.py` сам находит `normalized.json` там
без дополнительных действий, ручной `docker cp` больше не нужен.

```cmd
docker-compose up
docker-compose exec db pg_isready -U app -d app
docker compose exec backend python scripts/seed.py
```

Если файл лежит не в `parsing/data/normalized.json`, а где-то ещё — передать
путь явно (путь указывается **внутри контейнера**, а не на хосте):

```cmd
docker compose exec backend python scripts/seed.py --file /data/normalized.json
```

Проверка функционала:

```cmd
curl http://localhost:8000/artifacts
curl http://localhost:8000/artifacts/1
curl http://localhost:8000/tags
```

Создастся файл:

`parsing/data-report.md` - Отчёт о наполнении базы данных.
