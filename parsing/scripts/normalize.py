"""
Нормализация распарсенных данных (OpenAlex + библиотека ТюмГУ + репозиторий)
в формат normalized.json для импорта в БД (app/importer.py, POST /admin/import).

v2: формат записи расширен под текущую модель бэкенда:
  - author: {full_name, program} — реальный автор ТюмГУ (utmn_authors у статей,
    ФИО из заголовка у ВКР) и направление обучения. Для ВКР направление берётся
    из данных библиотеки (major), для статей подбирается по тематике работы
    из списка реальных направлений ТюмГУ (тот же список, что в seed.py).
  - supervisor: {full_name} | None — научный руководитель ВКР (из описания).
  - read_policy: open | requires_approval — открытые OA-статьи и работы
    из открытого репозитория читаются сразу; ВКР библиотеки ("доступ по
    паролю") — только по одобренному запросу.
  - tags: русские теги, сматченные по ключевым словам/названию/аннотации,
    чтобы работы попадали в дайджесты партнёров (подписки используют русские
    теги из seed.py). Непокрытые словарём английские keywords сохраняются
    дополнительными тегами.
Старые поля (access_level, author_name) сохранены для обратной совместимости.
"""
from datetime import datetime
import json
import random
import re
from pathlib import Path
from typing import Dict, List, Optional

# ============================================================
# РЕАЛЬНЫЕ НАПРАВЛЕНИЯ ТюмГУ (тот же список, что в backend/scripts/seed.py)
# ============================================================
REAL_PROGRAMS = [
    "01.03.01 Математика",
    "01.03.03 Механика и математическое моделирование",
    "02.03.03 Математическое обеспечение и администрирование информационных систем",
    "03.03.02 Физика",
    "04.03.01 Химия",
    "05.03.02 География",
    "05.03.03 Картография и геоинформатика",
    "05.03.06 Экология и природопользование",
    "06.03.01 Биология",
    "06.05.01 Биоинженерия и биоинформатика",
    "09.03.02 Информационные системы и технологии",
    "09.03.03 Прикладная информатика",
    "10.05.01 Компьютерная безопасность",
    "10.05.03 Информационная безопасность автоматизированных систем",
    "16.03.01 Техническая физика",
    "37.03.01 Психология",
    "38.03.01 Экономика",
    "38.03.02 Менеджмент",
    "38.03.04 Государственное и муниципальное управление",
    "39.03.01 Социология",
    "40.03.01 Юриспруденция",
    "41.03.01 Зарубежное регионоведение",
    "42.03.02 Журналистика",
    "43.03.02 Туризм",
    "44.03.05 Педагогическое образование (с двумя профилями)",
    "44.03.03 Специальное (дефектологическое) образование",
    "45.03.01 Филология",
    "45.03.02 Лингвистика",
    "46.03.01 История",
    "47.03.01 Философия",
    "51.03.01 Культурология",
    "35.03.10 Ландшафтная архитектура",
    "08.04.01 Строительство",
    "15.03.06 Механика и робототехника",
    "27.03.05 Инноватика",
]

# ============================================================
# ПОДБОР НАПРАВЛЕНИЯ ПО ТЕМАТИКЕ РАБОТЫ
# Правила проверяются по порядку на склейке keywords+title (в нижнем регистре);
# первое совпадение выигрывает. Ключи — подстроки/регэкспы.
# ============================================================
PROGRAM_RULES = [
    (r"machine learning|neural|deep learning|artificial intelligence|nlp|natural language|computer vision|classification model",
     "09.03.02 Информационные системы и технологии"),
    (r"cyber|information security|информационная безопасност",
     "10.05.01 Компьютерная безопасность"),
    (r"software|information system|database|algorithm|программирован|информатик",
     "09.03.03 Прикладная информатика"),
    (r"bioinformatic|genom|dna|rna|gene ",
     "06.05.01 Биоинженерия и биоинформатика"),
    (r"biolog|microb|bacteri|parasit|cell|organism|ecosystem|species|plant|soil biology",
     "06.03.01 Биология"),
    (r"ecolog|environment|pollution|water treatment|wastewater|climate|carbon|biochar|remediation",
     "05.03.06 Экология и природопользование"),
    (r"chemistr|chemical|catalys|polymer|nanoparticle|nanomaterial|synthesis|solution",
     "04.03.01 Химия"),
    (r"physic|quantum|optic|thermodynamic|magnet|plasma|laser",
     "03.03.02 Физика"),
    (r"mathemat|equation|numerical|theorem|тополог|алгебр",
     "01.03.01 Математика"),
    (r"geolog|geophysic|seismic|drilling|oil|gas |petroleum|reservoir|well |borehole",
     "05.03.02 География"),
    (r"gis|cartograph|geoinformat|remote sensing|spatial",
     "05.03.03 Картография и геоинформатика"),
    (r"psycholog|cognitive|behavior|mental health|emotion",
     "37.03.01 Психология"),
    (r"econom|financ|bank|market|invest|business|管理|management|entrepreneur",
     "38.03.01 Экономика"),
    (r"sociolog|social survey|society|inequality|migration",
     "39.03.01 Социология"),
    (r"law|legal|jurisprudence|court|legislation",
     "40.03.01 Юриспруденция"),
    (r"education|pedagog|teaching|student learning|school|didactic|учебн",
     "44.03.05 Педагогическое образование (с двумя профилями)"),
    (r"linguist|language teaching|translation|discourse|semantic",
     "45.03.02 Лингвистика"),
    (r"philolog|literature|poetry|novel|текстолог",
     "45.03.01 Филология"),
    (r"histor|archaeolog|archival|medieval|ancient",
     "46.03.01 История"),
    (r"philosoph|ontolog|epistemolog|ethic",
     "47.03.01 Философия"),
    (r"tourism|hospitality|туризм",
     "43.03.02 Туризм"),
    (r"journalis|media|mass communication",
     "42.03.02 Журналистика"),
    (r"cultur|heritage|museum",
     "51.03.01 Культурология"),
    (r"construction|building|civil engineer|architectur",
     "08.04.01 Строительство"),
    (r"robot|mechatron|mechanic",
     "15.03.06 Механика и робототехника"),
    (r"energy|power|electric|renewable|turbine|heat",
     "16.03.01 Техническая физика"),
    (r"medicin|clinical|patient|therapy|disease|cancer|oncolog|surgery|osteopath|somatic",
     "06.03.01 Биология"),
    (r"public administration|municipal|government",
     "38.03.04 Государственное и муниципальное управление"),
]

# ============================================================
# РУСИФИКАЦИЯ ТЕГОВ
# Маппинг тематик на русские теги проекта (см. TOPICS в seed.py) + общенаучные
# русские теги. Первый уровень — теги, участвующие в подписках партнёров.
# ============================================================
RU_TAG_RULES = [
    # Нефтегазовые технологии
    (r"\boil\b|petroleum|нефт", ["нефть"]),
    # 'gas' только в нефтегазовом контексте — иначе ловит gas chromatography и т.п.
    (r"natural gas|gas (field|pipeline|industry|production|well|condensate)|газов[аоы]|\bгаз\b", ["газ"]),
    (r"drilling|borehole|well construction|бурен", ["бурение"]),
    (r"seismic|сейсм", ["сейсмика"]),
    (r"geolog|geophysic|геолог", ["геология"]),
    (r"reservoir|digital twin|цифровой двойник", ["цифровой двойник", "моделирование"]),
    (r"simulation|modeling|modelling|numerical model|математическ.*модел|моделирован", ["моделирование"]),
    # Искусственный интеллект
    (r"machine learning|машинное обучение", ["машинное обучение", "AI"]),
    (r"neural network|deep learning|нейросет|нейронн", ["нейросети", "AI"]),
    (r"artificial intelligence|\bai\b|искусственн.*интеллект", ["AI"]),
    (r"natural language|nlp|text classification|language model", ["NLP", "AI"]),
    (r"computer vision|image recognition|распознавание изображ", ["computer vision", "AI"]),
    (r"big data|data mining|large-scale data|большие данные", ["Big Data"]),
    # Информационные технологии
    (r"information system|информационн.*систем", ["информационные системы"]),
    (r"cybersecurity|information security|кибербезопасност", ["кибербезопасность"]),
    (r"\bapi\b|web service|microservice", ["API"]),
    (r"\bpython\b", ["Python"]),
    (r"network protocol|computer network|компьютерн.*сет", ["сети"]),
    # Экология и энергетика
    (r"ecolog|environment|climate|carbon|biochar|эколог", ["экология"]),
    (r"water treatment|wastewater|water purification|очистк.*вод|сточн.*вод", ["очистка воды"]),
    (r"energy|power engineering|электроэнерг|энергетик|энергоэффективн", ["энергетика"]),
    (r"nanomaterial|nanoparticle|наноматериал|наночастиц", ["наноматериалы"]),
    # 'solar' только в энергетическом контексте — иначе ловит solar system
    (r"renewable|solar (power|energy|panel|cell)|wind (power|energy|turbine)|возобновляем", ["возобновляемая энергетика"]),
    # Общенаучные русские теги (вне подписок, для каталога и поиска)
    (r"psycholog|психолог", ["психология"]),
    (r"education|pedagog|педагог|образован", ["образование"]),
    (r"econom|financ|bank|эконом|финанс|банк", ["экономика"]),
    (r"sociolog|социолог", ["социология"]),
    (r"\blaw\b|legal|юридическ|юриспруденц|правов", ["право"]),
    (r"medicin|clinical|disease|cancer|мед[ии]цин|клиническ", ["медицина"]),
    (r"chemistr|chemical|хими", ["химия"]),
    (r"physic|физик", ["физика"]),
    (r"biolog|биолог", ["биология"]),
    (r"linguist|лингвист|языкознан", ["лингвистика"]),
    (r"histor|истори", ["история"]),
    (r"tourism|туризм", ["туризм"]),
]

# Максимум английских keywords, добавляемых к русским тегам
MAX_EN_KEYWORDS = 3
# Доля работ, оставляемых в статусе draft — очередь модерации куратора на демо
DRAFT_SHARE = 0.12

# Детерминированный генератор: одинаковый normalized.json при каждом запуске
_rng = random.Random(20260716)


def _text_for_matching(work: Dict) -> str:
    """Склейка всех текстовых полей работы для матчинга правил."""
    parts = [
        work.get("title", "") or "",
        work.get("title_en", "") or "",
        " ".join(work.get("keywords", []) or []),
        (work.get("abstract", "") or "")[:1500],
        work.get("major", "") or "",
    ]
    return " ".join(parts).lower()


def match_program(work: Dict) -> Optional[str]:
    """Направление обучения по тематике работы (первое сработавшее правило)."""
    text = _text_for_matching(work)
    for pattern, program in PROGRAM_RULES:
        if re.search(pattern, text):
            return program
    return None


def match_ru_tags(work: Dict) -> List[str]:
    """Русские теги по тематике работы (все сработавшие правила)."""
    text = _text_for_matching(work)
    tags: List[str] = []
    for pattern, rule_tags in RU_TAG_RULES:
        if re.search(pattern, text):
            for tag in rule_tags:
                if tag not in tags:
                    tags.append(tag)
    return tags


def build_tags(work: Dict, include_raw_ru: bool = True) -> List[Dict]:
    """Итоговые теги: русские по правилам + немного исходных keywords.

    Русские keywords работ репозитория берём как есть (это осмысленные
    библиотечные рубрики); у OpenAlex-статей сырые русские keywords —
    мусор из автоизвлечения, их не включаем (include_raw_ru=False).
    Английские — только в дополнение и не больше MAX_EN_KEYWORDS.
    """
    tags = match_ru_tags(work)
    ru_kw = [k for k in (work.get("keywords") or []) if re.search(r"[а-яё]", k, re.I)]
    en_kw = [k for k in (work.get("keywords") or []) if not re.search(r"[а-яё]", k, re.I)]
    if include_raw_ru:
        for kw in ru_kw:
            kw = kw.strip().lower()
            # служебные пометки репозитория тегами не делаем
            if kw and kw not in tags and kw not in ("магистерская диссертация", "выпускная квалификационная работа"):
                tags.append(kw)
    for kw in en_kw[:MAX_EN_KEYWORDS]:
        kw = kw.strip()
        if kw and kw not in tags:
            tags.append(kw)
    return [{"name": t} for t in tags]


def clean_major(major: Optional[str]) -> Optional[str]:
    """Чистит направление из библиографической строки: обрезает хвост после
    ' / ' (там идут инициалы автора) и балансирует кавычки-ёлочки."""
    if not major:
        return None
    major = re.split(r"\s+/\s+", major)[0].strip().rstrip(".,;:")
    if major.count("«") > major.count("»"):
        major += "»"
    return major or None


def created_at_from_year(year: Optional[int]) -> str:
    """created_at из реального года публикации — иначе все карточки показывают
    год импорта. Точная дата в источниках не указана, берём середину года."""
    if year and 1990 <= int(year) <= 2100:
        return datetime(int(year), 6, 1).isoformat()
    return datetime.utcnow().isoformat()


def pick_curator_status() -> str:
    """Большинство работ сразу approved (иначе дайджесты партнёров пусты),
    небольшая доля — draft, чтобы у куратора была живая очередь модерации."""
    return "draft" if _rng.random() < DRAFT_SHARE else "approved"


def extract_vkr_author(work: Dict) -> Optional[str]:
    """ФИО автора ВКР. В библиотечной записи title начинается с 'Фамилия, Имя
    Отчество. Название...' — берём часть до первой точки. Иначе — поле authors."""
    title = work.get("title", "") or ""
    m = re.match(r"^([А-ЯЁ][а-яё]+,\s*[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)\.", title)
    if m:
        # 'Иванов, Андрей Сергеевич' -> 'Иванов Андрей Сергеевич'
        return m.group(1).replace(",", "")
    authors = work.get("authors") or []
    if authors:
        return authors[0].replace(",", "").strip()
    return None


def strip_vkr_author_from_title(title: str) -> str:
    """Убирает 'Фамилия, Имя Отчество.' из начала названия ВКР."""
    return re.sub(r"^[А-ЯЁ][а-яё]+,\s*[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\.\s*", "", title).strip()


def extract_supervisor(work: Dict) -> Optional[str]:
    """Научный руководитель из библиографического описания ВКР
    ('... / А. С. Иванов; научный руководитель Д. С. Речапов; ...')."""
    text = f"{work.get('title_en', '') or ''} {work.get('abstract_en', '') or ''}"
    m = re.search(r"научн\w*\s+руководител\w*\s+([^;/—]+)", text, re.I)
    if m:
        return m.group(1).strip().rstrip(".,")
    return None


def normalize_openalex_work(work: Dict, index: int) -> Dict:
    """Одна OA-статья OpenAlex -> запись normalized.json (формат v2)."""
    # Автор артефакта — первый автор, аффилированный с ТюмГУ (реальное имя);
    # если разметки нет, берём первого автора статьи.
    utmn_authors = work.get("utmn_authors") or []
    all_authors = work.get("authors") or []
    author_name = (utmn_authors[0] if utmn_authors else (all_authors[0] if all_authors else None))

    return {
        "id": None,
        "title": work.get("title", f"Статья без названия {index}"),
        "type": "article",
        "annotation": work.get("abstract", "") or "",
        "file_path": work.get("source_url"),
        "curator_status": pick_curator_status(),
        # Все выгруженные статьи — из открытых источников (OA): читаются сразу
        "read_policy": "open" if work.get("source_url") else "requires_approval",
        "access_level": "full" if work.get("source_url") else "annotation_only",  # legacy
        "author": {
            "full_name": author_name,
            "program": match_program(work),
        } if author_name else None,
        "author_name": ", ".join(all_authors) if all_authors else None,  # legacy
        "co_authors": all_authors,
        "supervisor": None,  # у статей научрука нет
        "created_at": created_at_from_year(work.get("year")),
        "embedding": None,
        "tags": build_tags(work, include_raw_ru=False),
        "doi": work.get("doi"),
        "source_url": work.get("source_url"),
        "year": work.get("year"),
        "openalex_id": work.get("openalex_id"),
        "institute": None,
        "major": None,
        "source": "openalex",
    }


def normalize_thesis_work(work: Dict, index: int, source: str) -> Dict:
    """Одна ВКР/диссертация (библиотека или репозиторий) -> запись v2."""
    author_name = extract_vkr_author(work)
    title = strip_vkr_author_from_title(work.get("title", f"ВКР без названия {index}"))
    # Направление: у библиотеки/репозитория указано реальное (major, чистим от
    # библиографических хвостов); если нет — подбираем по тематике.
    program = clean_major(work.get("major")) or match_program(work)
    # Библиотечные ВКР закрыты ("доступ по паролю") — читаются только по
    # одобренному запросу; репозиторий (elib) — открытый архив.
    is_open = source == "repotheses"

    return {
        "id": None,
        "title": title,
        "type": "vkr",
        "annotation": work.get("abstract", "") or "",
        "file_path": work.get("source_url"),
        "curator_status": pick_curator_status(),
        "read_policy": "open" if (is_open and work.get("source_url")) else "requires_approval",
        "access_level": "full" if is_open else "annotation_only",  # legacy
        "author": {
            "full_name": author_name,
            "program": program,
        } if author_name else None,
        "author_name": author_name,  # legacy
        "co_authors": work.get("authors") or [],
        "supervisor": ({"full_name": extract_supervisor(work)} if extract_supervisor(work) else None),
        "created_at": created_at_from_year(work.get("year")),
        "embedding": None,
        "tags": build_tags(work),
        "doi": None,
        "source_url": work.get("source_url"),
        "year": work.get("year"),
        "openalex_id": None,
        "institute": work.get("institute"),
        "major": work.get("major"),
        "source": "utmnlib" if source == "libtheses" else "repotheses",
    }


def load_json_list(file_path: str, key: Optional[str] = None) -> List[Dict]:
    """Загрузка JSON-списка (или dict с ключом key) из файла."""
    path = Path(file_path)
    if not path.exists():
        print(f"Файл {path} не найден — пропускаем")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and key and key in data:
        return data[key]
    print(f"Неверный формат данных в {file_path}")
    return []


def save_normalized_data(artifacts: List[Dict], output_path: str):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(artifacts, f, ensure_ascii=False, indent=2)
    print(f"Всего артефактов: {len(artifacts)}")


def main():
    artifacts = []

    print("Загрузка данных OpenAlex")
    openalex_works = load_json_list("data/raw/openalex.json", key="works")
    for n, work in enumerate(openalex_works):
        try:
            artifacts.append(normalize_openalex_work(work, n + 1))
        except Exception as e:
            print(f"Ошибка при нормализации статьи OpenAlex {n + 1}: {e}")

    print("Загрузка ВКР библиотеки ТюмГУ")
    libtheses_works = load_json_list("data/raw/libtheses.json")
    for n, work in enumerate(libtheses_works):
        try:
            artifacts.append(normalize_thesis_work(work, n + 1, "libtheses"))
        except Exception as e:
            print(f"Ошибка при нормализации ВКР библиотеки {n + 1}: {e}")

    print("Загрузка работ репозитория ТюмГУ")
    repo_works = load_json_list("data/raw/repotheses.json")
    for n, work in enumerate(repo_works):
        try:
            artifacts.append(normalize_thesis_work(work, n + 1, "repotheses"))
        except Exception as e:
            print(f"Ошибка при нормализации работы репозитория {n + 1}: {e}")

    save_normalized_data(artifacts, "data/normalized.json")

    # Короткая сводка по качеству нормализации
    with_author = sum(1 for a in artifacts if a.get("author"))
    with_program = sum(1 for a in artifacts if a.get("author") and a["author"].get("program"))
    with_ru_tags = sum(1 for a in artifacts if any(re.search(r"[а-яё]", t["name"], re.I) for t in a["tags"]))
    open_count = sum(1 for a in artifacts if a.get("read_policy") == "open")
    print(f"Нормализовано артефактов: {len(artifacts)}")
    print(f" - Из OpenAlex: {len(openalex_works)}")
    print(f" - ВКР библиотеки: {len(libtheses_works)}")
    print(f" - Работ репозитория: {len(repo_works)}")
    print(f" - С автором: {with_author}, с направлением: {with_program}")
    print(f" - С русскими тегами: {with_ru_tags}")
    print(f" - Открытых для чтения: {open_count}")


if __name__ == "__main__":
    main()
