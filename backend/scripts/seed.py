"""
Наполняет БД тестовыми данными из normalized.json.
Запуск (из контейнера api):
    python scripts/seed.py
    python scripts/seed.py --file /data/normalized.json
"""
import os
import re
import sys
import json
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import (
    Artifact,
    Author,
    Favorite,
    Internship,
    Partner,
    Subscription,
    Tag,
    Teacher,
    User,
)
from app.security import hash_password


# ============================================================
# РЕАЛЬНЫЕ НАПРАВЛЕНИЯ ТюмГУ
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
# ТЕМЫ ПОДПИСОК (9 шт.) — построены вокруг реальных тематических кластеров
# в данных ТюмГУ (экономика, гуманитарные науки, физкультура, экология,
# химия, ИТ). id тегов не задаём — теги создаются get-or-create по имени.
# ============================================================
TOPICS = [
    {
        "id": 1,
        "name": "Экономика и финансы",
        "description": "Финансы, банковское дело, менеджмент и конкурентоспособность",
        "tags": [
            {"name": "экономика"},
            {"name": "финансы"},
            {"name": "менеджмент"},
            {"name": "конкурентоспособность"},
            {"name": "источники финансирования"},
        ],
    },
    {
        "id": 2,
        "name": "Право и государственное управление",
        "description": "Юриспруденция, публичное и муниципальное управление",
        "tags": [
            {"name": "право"},
            {"name": "государственное управление"},
        ],
    },
    {
        "id": 3,
        "name": "Филология и лингвистика",
        "description": "Русский язык, языкознание, литература и перевод",
        "tags": [
            {"name": "филология"},
            {"name": "лингвистика"},
            {"name": "русский язык"},
            {"name": "лексика"},
        ],
    },
    {
        "id": 4,
        "name": "Журналистика и медиакоммуникации",
        "description": "Журналистика, медиа и массовые коммуникации",
        "tags": [
            {"name": "журналистика"},
            {"name": "медиа"},
        ],
    },
    {
        "id": 5,
        "name": "Педагогика и образование",
        "description": "Педагогика, методики обучения и функциональная грамотность",
        "tags": [
            {"name": "педагогика"},
            {"name": "образование"},
            {"name": "функциональная грамотность"},
            {"name": "психология"},
        ],
    },
    {
        "id": 6,
        "name": "Физическая культура и спорт",
        "description": "Физическое воспитание, спортивная подготовка и методики тренировок",
        "tags": [
            {"name": "физическая культура"},
            {"name": "спорт"},
            {"name": "тренировочный процесс"},
        ],
    },
    {
        "id": 7,
        "name": "Экология и науки о Земле",
        "description": "Экология, лесное хозяйство, география и геология",
        "tags": [
            {"name": "экология"},
            {"name": "география"},
            {"name": "геология"},
            {"name": "гидрология"},
            {"name": "лесные пожары"},
        ],
    },
    {
        "id": 8,
        "name": "Химия и новые материалы",
        "description": "Химия, наноматериалы и функциональные материалы",
        "tags": [
            {"name": "химия"},
            {"name": "наноматериалы"},
        ],
    },
    {
        "id": 9,
        "name": "Математика, ИТ и искусственный интеллект",
        "description": "Математика, моделирование, информационные системы и машинное обучение",
        "tags": [
            {"name": "математика"},
            {"name": "моделирование"},
            {"name": "информационные системы"},
            {"name": "машинное обучение"},
            {"name": "Python"},
            {"name": "Big Data"},
        ],
    },
]

# ============================================================
# ПАРТНЁРЫ
# ============================================================
PARTNERS = [
    {
        "name": "Газпромнефть",
        "contact_email": "rnd@gpn-demo.ru",
        "login_email": "gpn@demo.ru",
        "subscriptions": [
            {"topic_id": 1},  # Экономика и финансы
            {"topic_id": 8},  # Химия и новые материалы
            {"topic_id": 9},  # Математика, ИТ и ИИ
        ],
    },
    {
        "name": "Яндекс",
        "contact_email": "it@yandex-demo.ru",
        "login_email": "yandex@demo.ru",
        "subscriptions": [
            {"topic_id": 3},  # Филология и лингвистика
            {"topic_id": 4},  # Журналистика и медиакоммуникации
            {"topic_id": 5},  # Педагогика и образование
        ],
    },
    {
        "name": "ЗапСибЭкоЦентр",
        "contact_email": "eco@eco-demo.ru",
        "login_email": "eco@demo.ru",
        "subscriptions": [
            {"topic_id": 7},  # Экология и науки о Земле
            {"topic_id": 6},  # Физическая культура и спорт
            {"topic_id": 2},  # Право и государственное управление
        ],
    },
]


def generate_teachers(count: int = 20) -> List[Dict]:
    teachers = [
        {
            "full_name": "Шевляков Артём Николаевич",
            "email": "a.n.shevlyakov@utmn.ru",
            "department": "Школа компьютерных наук",
            "position": "Заместитель директора по развитию, д.ф.-м.н., профессор",
        },
        {
            "full_name": "Вдовин Евгений Петрович",
            "email": "e.p.vdovin@utmn.ru",
            "department": "Школа компьютерных наук",
            "position": "Директор ШКН, д.ф.-.м.н., профессор",
        },
        {
            "full_name": "Яркова Елена Леонидовна",
            "email": "e.l.yarkova@utmn.ru",
            "department": "Центр иностранных языков и коммуникативных технологий",
            "position": "Старший преподаватель",
        },
        {
            "full_name": "Борисова Ирина Оттовна",
            "email": "i.o.borisova@utmn.ru",
            "department": "Центр иностранных языков и коммуникативных технологий",
            "position": "Старший преподаватель",
        },
        {
            "full_name": "Кыров Дмитрий Николаевич",
            "email": "d.n.kyrov@utmn.ru",
            "department": "Кафедра анатомии и физиологии человека и животных",
            "position": "Доцент (к.н.)",
        },
        {
            "full_name": "Павлова Елена Александровна",
            "email": "e.a.pavlova@utmn.ru",
            "department": "Академический департамент (ШКН)",
            "position": "Старший преподаватель",
        },
        {
            "full_name": "Перевалова Мария Николаевна",
            "email": "m.n.perevalova@utmn.ru",
            "department": "Академический департамент (ШКН)",
            "position": "Доцент",
        },
        {
            "full_name": "Воробьева Марина Сергеевна",
            "email": "m.s.vorobeva@utmn.ru",
            "department": "Академический департамент (ШКН)",
            "position": "Профессор (к.н.)",
        },
        {
            "full_name": "Аврискин Михаил Владимирович",
            "email": "m.v.avriskin@utmn.ru",
            "department": "Академический департамент (ШКН)",
            "position": "Старший преподаватель",
        },
        {
            "full_name": "Шилов Сергей Павлович",
            "email": "s.p.shilov@utmn.ru",
            "department": "Заведующий кафедрой (д.н.)",
            "position": "Кафедра истории",
        },
        {
            "full_name": "Медведев Александр Александрович",
            "email": "a.a.medvedev@utmn.ru",
            "department": "Заведующий кафедрой (к.н.)",
            "position": "Кафедра языкознания и литературоведения",
        },
        {
            "full_name": "Остапенко Анна Сергеевна",
            "email": "a.s.ostapenko@utmn.ru",
            "department": "Заведующий кафедрой (к.н.)",
            "position": "Кафедра прикладной и теоретической лингвистики",
        },
    ]
    return teachers


def load_normalized_data(file_path: str) -> List[Dict]:
    """Загружает данные из normalized.json."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ Файл {path} не найден")
        return []
    
    print(f"📂 Загружаем данные из {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        print(f"   Загружено {len(data)} записей")
        return data
    else:
        print(f"⚠️ Неверный формат данных в {path}")
        return []


def map_program_to_tags(program: Optional[str]) -> List[str]:
    """Маппинг направления подготовки на теги."""
    if not program:
        return ["информационные системы", "машинное обучение"]
    
    program_to_tags = {
        "нефтегаз": ["нефть", "газ", "бурение"],
        "информационные": ["информационные системы", "Python", "кибербезопасность"],
        "математическое": ["машинное обучение", "Big Data", "Python"],
        "картография": ["3D-модель", "геология", "моделирование"],
        "экология": ["экология", "очистка воды", "возобновляемая энергетика"],
        "химия": ["наноматериалы", "экология", "очистка воды"],
        "физика": ["энергетика", "наноматериалы", "моделирование"],
        "журналистика": ["NLP", "AI", "информационные системы"],
        "психология": ["AI", "Big Data", "информационные системы"],
        "юриспруденция": ["информационные системы", "кибербезопасность"],
        "менеджмент": ["Big Data", "информационные системы", "цифровой двойник"],
        "экономика": ["Big Data", "информационные системы"],
        "педагогика": ["информационные системы", "AI"],
        "робототехника": ["AI", "машинное обучение", "моделирование"],
        "безопасность": ["кибербезопасность", "информационные системы"],
    }
    
    program_lower = program.lower()
    for key, tags in program_to_tags.items():
        if key in program_lower:
            return tags[:3]

    return ["информационные системы", "машинное обучение"]


# ============================================================
# ТЕМАТИЧЕСКИЕ ТЕГИ ПО НАПРАВЛЕНИЮ / ИНСТИТУТУ / НАЗВАНИЮ
# 100 ВКР библиотеки приходят без ключевых слов — выводим тег темы из текста
# работы, чтобы она попала в релевантную подписку (из 9 тем выше). Правила
# двуязычные: данные содержат и русские, и английские тексты.
# ============================================================
NOISE_TAGS = {
    "магистерская диссертация",
    "выпускная квалификационная работа",
    "бакалаврская работа",
    "master thesis",
    "master's thesis",
    "bachelor thesis",
}

THEME_RULES = [
    (r"эконом|финанс|кредит|бюджет|менеджмент|тариф|бухгалт|инвестиц|econom|financ|\bbank|market|business", ["экономика", "финансы"]),
    (r"юриспруд|\bправо|правов|государствен\w*\s+управлен|муниципал|\blaw\b|legal|jurisprud|\bcourt", ["право", "государственное управление"]),
    (r"журналист|\bмедиа|масс\w*\s+коммуникац|journalis|\bmedia\b|mass communicat", ["журналистика", "медиа"]),
    (r"филолог|лингвист|языкознан|русский язык|литератур|лексик|семиот|перевод|дискурс|фразеолог|philolog|linguist|language|literatur|semiot|discourse|translation", ["филология", "лингвистика"]),
    (r"педагог|образован|грамотност|обучени|воспитани|дидакт|\bшкол|pedagog|education|teaching|didactic|literacy", ["педагогика", "образование"]),
    (r"психолог|благополуч|psycholog|cognitive|mental health|emotion", ["психология"]),
    (r"физическ\w*\s+культур|\bспорт|тренировоч|гимнаст|дзюдо|футбол|волейбол|физическое воспитан|атлет|\bsport|physical (culture|education|training)|athlet", ["физическая культура", "спорт"]),
    (r"эколог|\bлес|биомасс|растительн|гидролог|\bпочв|географ|геолог|зондирован|субаркт|углерод|\bпожар|картограф|геоинформат|природопользован|\bнефт|\bгаз\b|ecolog|environment|forest|climate|carbon|geolog|geograph|hydrolog|\bsoil|remote sensing|petroleum|\boil\b", ["экология", "география"]),
    (r"хими|наномат|полимер|синтез|катализ|\bматериал|chemis|nanomat|polymer|synthesis|catalys|\bmaterial", ["химия", "наноматериалы"]),
    (r"математ|механик|робот|мехатрон|моделирован|статист|числен|\bmath|mechanic|robot|\bmodel|numerical|statistic|equation|physic", ["математика", "моделирование"]),
    (r"информацион\w*\s+систем|программн|компьютерн|машинн\w*\s+обучен|нейросет|искусствен\w*\s+интеллект|инфокоммуник|информационная безопасн|кибербез|machine learning|neural|computer|software|algorithm|\bdata\b|information system|artificial intelligence|cyber", ["информационные системы", "машинное обучение"]),
]


def derive_theme_tags(work: Dict) -> List[str]:
    """Тематические теги по тексту работы (название + направление + институт +
    имеющиеся ключевые слова) — чтобы работа без внятных ключевых слов всё
    равно попадала в тематическую подписку."""
    text = " ".join([
        work.get("title", "") or "",
        work.get("major", "") or "",
        work.get("institute", "") or "",
        " ".join(t.get("name", "") for t in work.get("tags", [])),
    ]).lower()
    result: List[str] = []
    for pattern, tags in THEME_RULES:
        if re.search(pattern, text):
            for t in tags:
                if t not in result:
                    result.append(t)
    return result


def prioritize_tags(tags: List[str], limit: int = 8) -> List[str]:
    """Русские теги в приоритете (по ним матчатся подписки), дубли убраны,
    не больше limit штук."""
    seen, ru, other = set(), [], []
    for t in tags:
        if not t or t in seen:
            continue
        seen.add(t)
        (ru if re.search(r"[а-яё]", t, re.I) else other).append(t)
    return (ru + other)[:limit]


def seed(normalized_path: Optional[str] = None) -> None:
    """Основная функция наполнения БД."""
    init_db()

    with Session(engine) as session:
        # 1. Очистка
        print("🗑️ Очистка базы данных...")
        session.execute(text("""
            TRUNCATE TABLE digestitem, request, artifacttag, subscriptiontag, 
            artifact, subscription, partner, "user", author, teacher, 
            favorite, internship CASCADE;
        """))
        session.commit()
        print("✅ База данных очищена")

        # 2. Создаём теги — get-or-create по имени, а не merge по жёстким id:
        # таблица tag не входит в TRUNCATE выше, и после импорта/прошлых
        # прогонов теги могут существовать с другими id — merge по id=1..33
        # в этом случае падает на UNIQUE(name).
        print("🏷️ Создаём теги...")
        tags_by_name = {tag.name: tag for tag in session.exec(select(Tag)).all()}
        for topic in TOPICS:
            for tag_data in topic["tags"]:
                if tag_data["name"] not in tags_by_name:
                    tag = Tag(name=tag_data["name"])
                    session.add(tag)
                    session.flush()
                    tags_by_name[tag.name] = tag
        session.commit()
        print(f"   Тегов в базе: {len(tags_by_name)}")

        # 3. Загружаем данные из normalized.json
        normalized_data = []
        
        if normalized_path:
            normalized_data = load_normalized_data(normalized_path)
        
        # Если путь не указан или файл не найден, пробуем стандартные пути
        if not normalized_data:
            default_paths = [
                "data/normalized.json",
                "../data/normalized.json",
                "/data/normalized.json",
            ]
            for path in default_paths:
                normalized_data = load_normalized_data(path)
                if normalized_data:
                    break
        
        # Если данных нет, используем демо-данные
        if not normalized_data:
            print("⚠️ Нет данных для импорта!")
            return

        print(f"📚 Загружено {len(normalized_data)} артефактов")

        # Считаем статистику по источникам
        source_counts = {}
        for work in normalized_data:
            source = work.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print(f"   Источники: {source_counts}")

        # 4. Генерируем преподавателей
        teachers_data = generate_teachers(20)
        teachers_cache = {}
        
        print("👨‍🏫 Создаём преподавателей...")
        for t_data in teachers_data:
            teacher = Teacher(**t_data)
            session.add(teacher)
            session.flush()
            teachers_cache[t_data["full_name"]] = teacher
        session.commit()
        print(f"   Создано {len(teachers_cache)} преподавателей")

        # 5. Создаём авторов и артефакты
        print("📚 Создаём авторов и артефакты...")
        authors_cache = {}
        created_artifacts = []
        skipped = 0

        author_emails, stud_emails = {}, {}
        
        for i, work in enumerate(normalized_data):
            title = work.get("title", f"Артефакт {i+1}")
            # Формат v2 (scripts/normalize.py): author — объект с реальным
            # автором ТюмГУ и направлением, подобранным по тематике работы.
            # Legacy-фолбэк — свободная строка author_name.
            author_obj = work.get("author") or {}
            author_name = author_obj.get("full_name") or work.get("author_name")
            author_program = author_obj.get("program")
            year = work.get("year")
            annotation = work.get("annotation", "")
            source = work.get("source", "unknown")
            
            # Теги: производные тематические (по направлению/институту/названию)
            # + реальные ключевые слова из normalized.json (без служебного мусора
            # библиотеки). Русские в приоритете — по ним матчатся подписки — не
            # больше 8 штук.
            real_tags = [
                t.get("name") for t in work.get("tags", [])
                if t.get("name") and t["name"].lower() not in NOISE_TAGS
            ]
            tag_names = prioritize_tags(derive_theme_tags(work) + real_tags)
            if not tag_names:
                tag_names = ["информационные системы"]
            
            # Направление: приоритет — подобранное normalize.py по тематике
            # (author.program), затем сырой major источника, затем случайное.
            institute = work.get("institute")
            major = author_program or work.get("major")
            if not major:
                major = random.choice(REAL_PROGRAMS)
                print(f"   ⚠️ Для '{title[:30]}...' сгенерировано направление: {major}")
            
            source_url = work.get("source_url", "")
            artifact_type = work.get("type", "article")
            
            # Для OpenAlex статей может не быть автора
            if not author_name:
                author_name = f"Автор {i+1}"

            email_prefix = 'author' if source == "openalex" else 'stud'
            email_postfix = 'utmn.ru' if source == "openalex" else 'study.utmn.ru'
            
            # Создаём автора
            if author_name not in authors_cache:
                # Генерируем email
                counter = 1
                email = f"{email_prefix}{str(i + 1).zfill(10)}@{email_postfix}"
                while session.exec(select(Author).where(Author.email == email)).first():
                    email = f"{email_prefix}{str(i + 1 + counter).zfill(10)}@{email_postfix}"
                    counter += 1
                
                if source == "openalex":
                    author_emails[author_name] = email
                else:
                    stud_emails[author_name] = email
                
                job_status = random.choices(
                    ["searching", "employed", "not_searching"],
                    weights=[0.5, 0.3, 0.2]
                )[0]
                
                author = Author(
                    email=email,
                    full_name=author_name,
                    program=major,
                    job_status=job_status,
                )
                session.add(author)
                session.flush()
                authors_cache[author_name] = author
                print(f"   Создан автор: {author_name} ({email})")
            
            author = authors_cache[author_name]

            # Научный руководитель: у ВКР normalize.py извлекает реального из
            # библиографического описания — создаём его; иначе случайный.
            supervisor = None
            supervisor_obj = work.get("supervisor") or {}
            supervisor_name = supervisor_obj.get("full_name")
            if supervisor_name:
                if supervisor_name not in teachers_cache:
                    teacher = Teacher(
                        full_name=supervisor_name,
                        email=f"teacher{len(teachers_cache) + 1:04d}@utmn.ru",
                        department="Тюменский государственный университет",
                        position="Научный руководитель",
                    )
                    session.add(teacher)
                    session.flush()
                    teachers_cache[supervisor_name] = teacher
                supervisor = teachers_cache[supervisor_name]
            elif teachers_cache and artifact_type == "vkr":
                supervisor = random.choice(list(teachers_cache.values()))

            # Политика чтения: из normalized.json (открытые OA-источники ->
            # open), фолбэк для legacy-записей — случайная.
            read_policy = work.get("read_policy")
            if read_policy not in ("open", "requires_approval"):
                read_policy = random.choices(["open", "requires_approval"], weights=[0.3, 0.7])[0]

            # Статус модерации: normalized.json приходит целиком в draft — это
            # бесполезно для демо (партнёр не увидел бы ни одной работы, дайджест
            # показывает только approved). Поэтому большинство одобряем, ~15%
            # оставляем в очереди куратора. Явный approved/rejected из файла
            # уважаем, если он там появится.
            curator_status = work.get("curator_status")
            if curator_status not in ("approved", "rejected"):
                curator_status = random.choices(
                    ["approved", "draft"], weights=[0.85, 0.15]
                )[0]

            # У модели Artifact нет колонки year — реальный год публикации
            # кодируем в created_at, иначе все карточки показывают год сида.
            created_at = (
                datetime(int(year), 6, 1)
                if year and 1990 <= int(year) <= 2100
                else datetime.utcnow()
            )

            artifact = Artifact(
                title=title,
                type=artifact_type,
                annotation=annotation or "Нет аннотации",
                file_path=source_url or None,
                created_at=created_at,
                curator_status=curator_status,
                read_policy=read_policy,
                author_id=author.id,
                supervisor_id=supervisor.id if supervisor else None,
            )
            session.add(artifact)
            session.flush()
            
            # Привязываем теги: недостающие (не входящие в темы) создаём на лету,
            # чтобы на карточке были видны и реальные ключевые слова, а не только
            # тематические.
            for tag_name in tag_names:
                tag = tags_by_name.get(tag_name)
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    session.flush()
                    tags_by_name[tag_name] = tag
                session.execute(
                    text("INSERT INTO artifacttag (artifact_id, tag_id) VALUES (:a, :t) ON CONFLICT DO NOTHING"),
                    {"a": artifact.id, "t": tag.id}
                )
            
            created_artifacts.append(artifact)
            if (i + 1) % 50 == 0:
                print(f"   Создано {i + 1} артефактов...")
        
        session.commit()
        print(f"   Создано {len(authors_cache)} авторов и {len(created_artifacts)} артефактов")
        if skipped:
            print(f"   Пропущено: {skipped}")

        # 6. Партнёры и подписки
        print("🏢 Создаём партнёров и подписки...")
        partners = {}
        subscriptions_list = []

        for p_data in PARTNERS:
            partner = Partner(name=p_data["name"], contact_email=p_data["contact_email"])
            session.add(partner)
            session.commit()
            session.refresh(partner)
            partners[p_data["login_email"]] = partner

            for sub_data in p_data["subscriptions"]:
                topic = next((t for t in TOPICS if t["id"] == sub_data["topic_id"]), None)
                if not topic:
                    continue
                sub = Subscription(
                    partner_id=partner.id,
                    name=topic["name"],
                    description=topic["description"],
                )
                session.add(sub)
                session.commit()
                session.refresh(sub)
                subscriptions_list.append((sub, topic["tags"]))

        for sub, topic_tags in subscriptions_list:
            for tag_data in topic_tags:
                tag = tags_by_name.get(tag_data["name"])
                if tag:
                    session.execute(
                        text("INSERT INTO subscriptiontag (subscription_id, tag_id) VALUES (:s, :t) ON CONFLICT DO NOTHING"),
                        {"s": sub.id, "t": tag.id}
                    )
            session.commit()

        print(f"   Создано {len(partners)} партнёров и {len(subscriptions_list)} подписок")

        # 7. Пользователи
        print("👤 Создаём пользователей...")
        users = []
        
        for login_email, partner in partners.items():
            users.append(
                User(
                    email=login_email,
                    password_hash=hash_password("pass123"),
                    role="partner",
                    partner_id=partner.id,
                )
            )
        
        users.append(
            User(email="curator@demo.ru", password_hash=hash_password("pass123"), role="curator")
        )
        users.append(
            User(email="admin@demo.ru", password_hash=hash_password("pass123"), role="admin")
        )
        
        for author in authors_cache.values():
            users.append(
                User(
                    email=author.email,
                    password_hash=hash_password("pass123"),
                    role="author",
                    author_id=author.id,
                )
            )
        
        session.add_all(users)
        session.commit()
        print(f"   Создано {len(users)} пользователей")

        # 8. Избранное
        print("⭐ Создаём избранное...")
        if created_artifacts:
            gpn = partners.get("gpn@demo.ru")
            yandex = partners.get("yandex@demo.ru")
            eco = partners.get("eco@demo.ru")
            
            if gpn and len(created_artifacts) >= 1:
                session.add(Favorite(artifact_id=created_artifacts[0].id, partner_id=gpn.id))
            if yandex and len(created_artifacts) >= 2:
                session.add(Favorite(artifact_id=created_artifacts[1].id, partner_id=yandex.id))
            if eco and len(created_artifacts) >= 3:
                session.add(Favorite(artifact_id=created_artifacts[2].id, partner_id=eco.id))
            session.commit()

        # 9. Статистика
        artifact_count = session.query(Artifact).count()
        author_count = session.query(Author).count()
        teacher_count = session.query(Teacher).count()
        subscription_count = session.query(Subscription).count()
        user_count = session.query(User).count()
        tag_count = session.query(Tag).count()

        print("\n" + "=" * 60)
        print("База данных успешно наполнена.")
        print("=" * 60)
        print(f"Статистика:")
        print(f"   • {artifact_count} артефактов")
        print(f"   • {author_count} авторов")
        print(f"   • {teacher_count} преподавателей")
        print(f"   • {tag_count} тегов")
        print(f"   • {len(partners)} партнёров")
        print(f"   • {subscription_count} подписок")
        print(f"   • {user_count} пользователей")
        print()
        print("Логины для входа:")
        print("   Партнёры:")
        for login_email in partners:
            print(f"     {login_email} / pass123")
        print("   Куратор:")
        print("     curator@demo.ru / pass123")
        print("   Админ:")
        print("     admin@demo.ru / pass123")
        print("   Преподователи:")
        for data in teachers_data:
            print(f"     {data['full_name']}: {data['email']} / pass123")
        print("   Авторы статей:")
        for name in author_emails:
            print(f"     {name}: {author_emails[name]} / pass123")
        print("   Студенты:")
        for name in stud_emails:
            print(f"     {name}: {stud_emails[name]} / pass123")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Наполнение БД данными из normalized.json")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Путь к файлу normalized.json"
    )
    args = parser.parse_args()
    
    seed(args.file)


if __name__ == "__main__":
    main()
