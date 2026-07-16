"""
Наполняет БД тестовыми данными из normalized.json.
Запуск (из контейнера api):
    python scripts/seed.py
    python scripts/seed.py --file /data/normalized.json
"""
import os
import sys
import json
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import random

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
# ТЕМЫ С ТЭГАМИ
# ============================================================
TOPICS = [
    {
        "id": 1,
        "name": "Искусственный интеллект и машинное обучение",
        "description": "AI, машинное обучение, нейросети и интеллектуальные системы",
        "tags": [
            {"id": 1, "name": "AI"},
            {"id": 2, "name": "машинное обучение"},
            {"id": 3, "name": "нейросети"},
            {"id": 4, "name": "NLP"},
            {"id": 5, "name": "Big Data"},
            {"id": 6, "name": "computer vision"},
            # Удален дублирующийся тег "информационные системы" (был id=7)
        ],
    },
    {
        "id": 2,
        "name": "Нефтегазовые технологии",
        "description": "Добыча, переработка и моделирование в нефтегазовой отрасли",
        "tags": [
            {"id": 8, "name": "нефть"},
            {"id": 9, "name": "газ"},
            {"id": 10, "name": "бурение"},
            {"id": 11, "name": "цифровой двойник"},
            {"id": 12, "name": "моделирование"},
            {"id": 13, "name": "геология"},
            {"id": 14, "name": "газовая промышленность"},
            {"id": 15, "name": "нефтепродукты"},
            {"id": 16, "name": "нефтешлам"},
        ],
    },
    {
        "id": 3,
        "name": "Информационные технологии и разработка",
        "description": "Разработка ПО, веб-технологии, информационная безопасность",
        "tags": [
            {"id": 17, "name": "Python"},
            {"id": 18, "name": "React"},
            {"id": 19, "name": "Backend"},  # Оставляем один Backend
            # Удален дублирующийся Backend (был id=24)
            {"id": 20, "name": "API"},
            {"id": 21, "name": "сети"},
            {"id": 22, "name": "информационные системы"},  # Теперь один тег с этим именем
            {"id": 23, "name": "кибербезопасность"},
        ],
    },
    {
        "id": 4,
        "name": "Экология и природопользование",
        "description": "Экологические исследования, охрана природы и устойчивое развитие",
        "tags": [
            {"id": 25, "name": "экология"},
            {"id": 26, "name": "очистка воды"},
            {"id": 27, "name": "возобновляемая энергетика"},
            {"id": 28, "name": "гидрология"},
            {"id": 29, "name": "растительность"},
            {"id": 30, "name": "биомасса"},
            {"id": 31, "name": "органическое вещество"},
            {"id": 32, "name": "тяжёлые металлы"},
            {"id": 33, "name": "радиоактивность"},
        ],
    },
    {
        "id": 5,
        "name": "Лингвистика и филология",
        "description": "Изучение языка, текста, дискурса и коммуникации",
        "tags": [
            {"id": 34, "name": "русский язык"},
            {"id": 35, "name": "языкознание"},
            {"id": 36, "name": "лексика"},
            {"id": 37, "name": "фразеологизмы"},
            {"id": 38, "name": "семантика"},
            {"id": 39, "name": "лингвистика"},
            {"id": 40, "name": "гастрономический дискурс"},
            {"id": 41, "name": "лексические единицы"},
        ],
    },
    {
        "id": 6,
        "name": "Педагогика и образование",
        "description": "Методика преподавания, педагогические технологии и образование",
        "tags": [
            {"id": 42, "name": "образование"},
            {"id": 43, "name": "педагогика"},
            {"id": 44, "name": "методика"},
            {"id": 45, "name": "функциональная грамотность"},
            {"id": 46, "name": "универсальные учебные действия"},
            {"id": 47, "name": "педагогические технологии"},
            {"id": 48, "name": "школьная программа"},
            {"id": 49, "name": "уроки литературы"},
        ],
    },
    {
        "id": 7,
        "name": "Экономика и финансы",
        "description": "Экономические исследования, финансы, управление и инвестиции",
        "tags": [
            {"id": 50, "name": "экономика"},
            {"id": 51, "name": "финансы"},
            {"id": 52, "name": "инвестиции"},
            {"id": 53, "name": "управление"},
            {"id": 54, "name": "бюджет"},
            {"id": 55, "name": "финансовые результаты"},
            {"id": 56, "name": "финансовая устойчивость"},
        ],
    },
    {
        "id": 8,
        "name": "Физическая культура и спорт",
        "description": "Спортивные игры, физическая подготовка и здоровый образ жизни",
        "tags": [
            {"id": 57, "name": "физическая культура"},
            {"id": 58, "name": "спорт"},
            {"id": 59, "name": "волейбол"},
            {"id": 60, "name": "баскетбол"},
            {"id": 61, "name": "тренировка"},
            {"id": 62, "name": "физическая подготовка"},
            {"id": 63, "name": "лыжный спорт"},
        ],
    },
    {
        "id": 9,
        "name": "Юриспруденция и право",
        "description": "Правовые исследования, гражданское право и правовое регулирование",
        "tags": [
            {"id": 64, "name": "юриспруденция"},
            {"id": 65, "name": "правовое регулирование"},
            {"id": 66, "name": "право"},
            {"id": 67, "name": "гражданское право"},
            {"id": 68, "name": "законодательство"},
        ],
    },
    {
        "id": 10,
        "name": "Общая наука и исследования",
        "description": "Междисциплинарные и общенаучные исследования",
        "tags": [
            {"id": 69, "name": "исследование"},
            {"id": 70, "name": "анализ"},
            {"id": 71, "name": "психология"},
            {"id": 72, "name": "история"},
            {"id": 73, "name": "культурология"},
            {"id": 74, "name": "социология"},
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
            {"topic_id": 2, "name": "Нефтегазовые технологии"},
            {"topic_id": 1, "name": "Искусственный интеллект и машинное обучение"},
        ],
    },
    {
        "name": "Яндекс",
        "contact_email": "it@yandex-demo.ru",
        "login_email": "yandex@demo.ru",
        "subscriptions": [
            {"topic_id": 1, "name": "Искусственный интеллект и машинное обучение"},
            {"topic_id": 3, "name": "Информационные технологии и разработка"},
        ],
    },
    {
        "name": "ЗапСибЭкоЦентр",
        "contact_email": "eco@eco-demo.ru",
        "login_email": "eco@demo.ru",
        "subscriptions": [
            {"topic_id": 4, "name": "Экология и природопользование"},
            {"topic_id": 2, "name": "Нефтегазовые технологии"},
        ],
    },
    {
        "name": "Центр педагогических инноваций",
        "contact_email": "edu@edu-demo.ru",
        "login_email": "edu@demo.ru",
        "subscriptions": [
            {"topic_id": 6, "name": "Педагогика и образование"},
            {"topic_id": 1, "name": "Искусственный интеллект и машинное обучение"},
        ],
    },
    {
        "name": "ЛингвоПроект",
        "contact_email": "lingua@lingua-demo.ru",
        "login_email": "lingua@demo.ru",
        "subscriptions": [
            {"topic_id": 5, "name": "Лингвистика и филология"},
            {"topic_id": 1, "name": "Искусственный интеллект и машинное обучение"},
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
        print(f"Файл {path} не найден")
        return []
    
    print(f"Загружаем данные из {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        print(f"Загружено {len(data)} записей")
        return data
    else:
        print(f"⚠️ Неверный формат данных в {path}")
        return []


def map_tags_to_topic(tag_name: str) -> List[int]:
    """Определяет, к каким темам относится тег."""
    tag_to_topic = {
        # Искусственный интеллект и машинное обучение
        "AI": [1],
        "машинное обучение": [1],
        "нейросети": [1],
        "NLP": [1],
        "Big Data": [1],
        "computer vision": [1],
        "информационные системы": [1, 3],
        
        # Нефтегазовые технологии
        "нефть": [2],
        "газ": [2],
        "бурение": [2],
        "цифровой двойник": [2],
        "моделирование": [2],
        "геология": [2],
        "газовая промышленность": [2],
        "нефтепродукты": [2],
        "нефтешлам": [2],
        "сейсмика": [2],
        "3D-модель": [2],
        
        # Информационные технологии и разработка
        "Python": [3],
        "React": [3],
        "Backend": [3],
        "API": [3],
        "сети": [3],
        "кибербезопасность": [3],
        
        # Экология и природопользование
        "экология": [4],
        "очистка воды": [4],
        "возобновляемая энергетика": [4],
        "гидрология": [4],
        "растительность": [4],
        "биомасса": [4],
        "органическое вещество": [4],
        "тяжёлые металлы": [4],
        "радиоактивность": [4],
        "энергетика": [4],
        "наноматериалы": [4],
        
        # Лингвистика и филология
        "русский язык": [5],
        "языкознание": [5],
        "лексика": [5],
        "фразеологизмы": [5],
        "семантика": [5],
        "лингвистика": [5],
        "гастрономический дискурс": [5],
        "лексические единицы": [5],
        "филология": [5],
        
        # Педагогика и образование
        "образование": [6],
        "педагогика": [6],
        "методика": [6],
        "функциональная грамотность": [6],
        "универсальные учебные действия": [6],
        "педагогические технологии": [6],
        "школьная программа": [6],
        "уроки литературы": [6],
        "уроки русского языка": [6],
        
        # Экономика и финансы
        "экономика": [7],
        "финансы": [7],
        "инвестиции": [7],
        "управление": [7],
        "бюджет": [7],
        "финансовые результаты": [7],
        "финансовая устойчивость": [7],
        "финансирование": [7],
        
        # Физическая культура и спорт
        "физическая культура": [8],
        "спорт": [8],
        "волейбол": [8],
        "баскетбол": [8],
        "тренировка": [8],
        "физическая подготовка": [8],
        "лыжный спорт": [8],
        "спортивные игры": [8],
        "спортсмены": [8],
        
        # Юриспруденция и право
        "юриспруденция": [9],
        "правовое регулирование": [9],
        "право": [9],
        "гражданское право": [9],
        "законодательство": [9],
        
        # Общая наука и исследования
        "исследование": [10],
        "анализ": [10],
        "психология": [10],
        "история": [10],
        "культурология": [10],
        "социология": [10],
        "литературоведение": [10],
        "литературная критика": [10],
    }
    
    return tag_to_topic.get(tag_name, [])


def seed(normalized_path: Optional[str] = None) -> None:
    """Основная функция наполнения БД."""
    init_db()

    with Session(engine) as session:
        # 1. Очистка
        print("Очистка базы данных...")
        session.execute(text("""
            TRUNCATE TABLE digestitem, request, artifacttag, subscriptiontag, 
            artifact, subscription, partner, "user", author, teacher, 
            favorite, internship CASCADE;
        """))
        session.commit()
        print("База данных очищена")

        # 2. Создаём теги и маппинг тегов по темам
        print("Создаём теги...")
        tag_names = set()
        for topic in TOPICS:
            for tag_data in topic["tags"]:
                tag_names.add(tag_data["name"])
                tag = Tag(id=tag_data["id"], name=tag_data["name"])
                session.merge(tag)
        session.commit()
        tags_by_name = {tag.name: tag for tag in session.exec(select(Tag)).all()}
        print(f"Создано {len(tags_by_name)} тегов")

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

        if not normalized_data:
            print("Нет данных для импорта!")
            return

        print(f"Загружено {len(normalized_data)} артефактов")

        source_counts = {}
        for work in normalized_data:
            source = work.get("source", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

        print(f"Источники: {source_counts}")

        # 4. Генерируем преподавателей
        teachers_data = generate_teachers(20)
        teachers_cache = {}

        print("Создаём преподавателей...")
        for t_data in teachers_data:
            teacher = Teacher(**t_data)
            session.add(teacher)
            session.flush()
            teachers_cache[t_data["full_name"]] = teacher
        session.commit()
        print(f"Создано {len(teachers_cache)} преподавателей")

        # 5. Создаём авторов и артефакты
        print("Создаём авторов и артефакты...")
        authors_cache = {}
        created_artifacts = []
        skipped = 0

        author_emails, stud_emails = {}, {}

        # Создаём маппинг тегов для быстрого доступа
        tag_id_to_topic_ids = {}
        for tag_name, tag in tags_by_name.items():
            topic_ids = map_tags_to_topic(tag_name)
            if topic_ids:
                tag_id_to_topic_ids[tag.id] = topic_ids

        for i, work in enumerate(normalized_data):
            title = work.get("title", f"Артефакт {i+1}")
            author_name = work.get("author_name")
            year = work.get("year")
            annotation = work.get("annotation", "")
            source = work.get("source", "unknown")

            # Извлекаем теги
            tags_data = work.get("tags", [])
            tag_names = [t.get("name") for t in tags_data if t.get("name")]

            # Дополнительные теги из ключевых слов (для статей OpenAlex)
            if source == "openalex" and not tag_names:
                tag_names = ["информационные системы", "машинное обучение"]
            
            # Ограничиваем количество тегов до 5
            tag_names = list(set(tag_names))[:5]

            institute = work.get("institute")
            major = work.get("major")
            
            if not major and source == "utmnlib":
                # Для ВКР из библиотеки пытаемся извлечь из institute
                if "компьютерных" in str(institute).lower():
                    major = "09.03.02 Информационные системы и технологии"
                elif "нефти" in str(institute).lower() or "геологии" in str(institute).lower():
                    major = "05.03.06 Экология и природопользование"
                elif "физической культуры" in str(institute).lower():
                    major = "49.03.01 Физическая культура"
                else:
                    major = random.choice(REAL_PROGRAMS)
            elif not major:
                major = random.choice(REAL_PROGRAMS)

            source_url = work.get("source_url", "")
            artifact_type = work.get("type", "article")

            # Для OpenAlex статей может не быть автора
            if not author_name:
                author_name = f"Автор {i+1}"

            email_prefix = 'author' if source == "openalex" else 'stud'
            email_postfix = 'utmn.ru' if source == "openalex" else 'study.utmn.ru'

            if author_name not in authors_cache:
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

            author = authors_cache[author_name]

            supervisor = random.choice(list(teachers_cache.values())) if teachers_cache else None
            read_policy = random.choices(["open", "requires_approval"], weights=[0.3, 0.7])[0]

            # Определяем curator_status: для OpenAlex статей сразу approved
            # curator_status = "approved" if source == "openalex" else "draft"
            curator_status = "draft" if random.randint(1, 10) == 5 else "approved"

            artifact = Artifact(
                title=title,
                type=artifact_type,
                annotation=annotation or "Нет аннотации",
                file_path=source_url or None,
                year=year,
                curator_status=curator_status,
                read_policy=read_policy,
                author_id=author.id,
                supervisor_id=supervisor.id if supervisor else None,
            )
            session.add(artifact)
            session.flush()

            # Привязываем теги
            for tag_name in tag_names:
                tag = tags_by_name.get(tag_name)
                if tag:
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
        print("Создаём партнёров и подписки...")
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

        print(f"Создано {len(partners)} партнёров и {len(subscriptions_list)} подписок")

        # 7. Пользователи
        print("Создаём пользователей...")
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
        print(f"Создано {len(users)} пользователей")

        # 8. Избранное
        print("Создаём избранное...")
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
        print("База данных успешно заполнена.")
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
        print("   Преподаватели:")
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
