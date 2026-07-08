
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
- `parsing/docs/taxonomy.md` - Описание таксономии OpenAlex в формате Markdown.
