
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

## Нормализация публикаций к формату артефакта

```cmd
cd parsing
python -m scripts.normalize
```

Создастся файл:

`parsing/data/normalized.json` - Артефакты в формате JSON.

## Импорт данных в базу данных

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

Проверка функционала:

```cmd
curl http://localhost:8000/artifacts
curl http://localhost:8000/artifacts/1
curl http://localhost:8000/tags
```

Создастся файл:

`parsing/data-report.md` - Отчёт о наполнении базы данных.
