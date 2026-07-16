"""
Наполняет БД тестовыми данными для пилота.
Запуск (из контейнера api):
    python scripts/seed.py
    python scripts/seed.py --file /data/raw/libtheses.json
"""
import os
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
# ТЕГИ
# ============================================================
TOPICS = [
    {
        "id": 1,
        "name": "Нефтегазовые технологии",
        "description": "Исследования в области добычи и моделирования месторождений",
        "tags": [
            {"id": 1, "name": "нефть"},
            {"id": 2, "name": "газ"},
            {"id": 3, "name": "моделирование"},
            {"id": 4, "name": "геология"},
            {"id": 5, "name": "3D-модель"},
            {"id": 21, "name": "газовая промышленность"},
            {"id": 22, "name": "цифровой двойник"},
            {"id": 23, "name": "сейсмика"},
            {"id": 24, "name": "бурение"},
        ],
    },
    {
        "id": 2,
        "name": "Искусственный интеллект",
        "description": "AI, машинное обучение и интеллектуальные системы",
        "tags": [
            {"id": 6, "name": "AI"},
            {"id": 7, "name": "машинное обучение"},
            {"id": 8, "name": "нейросети"},
            {"id": 9, "name": "NLP"},
            {"id": 10, "name": "Big Data"},
            {"id": 25, "name": "computer vision"},
        ],
    },
    {
        "id": 3,
        "name": "Информационные технологии",
        "description": "Разработка программных и информационных систем",
        "tags": [
            {"id": 11, "name": "React"},
            {"id": 12, "name": "Backend"},
            {"id": 13, "name": "Python"},
            {"id": 28, "name": "API"},
            {"id": 31, "name": "информационные системы"},
            {"id": 32, "name": "кибербезопасность"},
            {"id": 33, "name": "сети"},
        ],
    },
    {
        "id": 4,
        "name": "Экология и энергетика",
        "description": "Экологические исследования и новые источники энергии",
        "tags": [
            {"id": 14, "name": "экология"},
            {"id": 15, "name": "очистка воды"},
            {"id": 16, "name": "энергетика"},
            {"id": 17, "name": "наноматериалы"},
            {"id": 29, "name": "возобновляемая энергетика"},
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
            {"topic_id": 1, "name": "Нефтегазовые технологии"},
            {"topic_id": 2, "name": "Искусственный интеллект"},
        ],
    },
    {
        "name": "Яндекс",
        "contact_email": "it@yandex-demo.ru",
        "login_email": "yandex@demo.ru",
        "subscriptions": [
            {"topic_id": 2, "name": "Искусственный интеллект"},
            {"topic_id": 3, "name": "Информационные технологии"},
        ],
    },
    {
        "name": "ЗапСибЭкоЦентр",
        "contact_email": "eco@eco-demo.ru",
        "login_email": "eco@demo.ru",
        "subscriptions": [
            {"topic_id": 4, "name": "Экология и энергетика"},
            {"topic_id": 1, "name": "Нефтегазовые технологии"},
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


def load_libtheses_data(file_path: str) -> List[Dict]:
    """Загружает данные из libtheses.json."""
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


def seed(libtheses_path: Optional[str] = None) -> None:
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

        # 2. Создаём теги
        print("🏷️ Создаём теги...")
        for topic in TOPICS:
            for tag_data in topic["tags"]:
                tag = Tag(id=tag_data["id"], name=tag_data["name"])
                session.merge(tag)
        session.commit()
        tags_by_name = {tag.name: tag for tag in session.exec(select(Tag)).all()}
        print(f"   Создано {len(tags_by_name)} тегов")

        # 3. Загружаем данные из libtheses.json
        libtheses_data = []
        
        if libtheses_path:
            libtheses_data = load_libtheses_data(libtheses_path)
        
        # Если путь не указан или файл не найден, пробуем стандартные пути
        if not libtheses_data:
            default_paths = [
                "data/raw/libtheses.json",
                "../data/raw/libtheses.json",
                "/data/raw/libtheses.json",
            ]
            for path in default_paths:
                libtheses_data = load_libtheses_data(path)
                if libtheses_data:
                    break
        
        # Если данных нет, используем демо-данные
        if not libtheses_data:
            print("⚠️ Используются демо-данные (3 записи)")
            libtheses_data = [
                {
                    "title": "Оптимизация буровых растворов",
                    "authors": ["Орлова Анна Сергеевна"],
                    "year": 2024,
                    "abstract": "ВКР о снижении затрат на буровые растворы",
                    "institute": "Школа естественных наук",
                    "major": "05.03.02 География",
                },
                {
                    "title": "Цифровой двойник насосной станции",
                    "authors": ["Соколов Дмитрий Алексеевич"],
                    "year": 2024,
                    "abstract": "Модель цифрового двойника для мониторинга",
                    "institute": "Институт математики и компьютерных наук",
                    "major": "09.03.02 Информационные системы и технологии",
                },
                {
                    "title": "Прогноз спроса в логистике методами ML",
                    "authors": ["Зайцева Екатерина Владимировна"],
                    "year": 2024,
                    "abstract": "Применение ML для прогноза спроса",
                    "institute": "Институт математики и компьютерных наук",
                    "major": "02.03.03 Математическое обеспечение",
                },
            ]

        print(f"📚 Загружено {len(libtheses_data)} ВКР")

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
        
        for i, work in enumerate(libtheses_data):
            title = work.get("title", f"ВКР {i+1}")
            authors = work.get("authors", [])
            author_full_name = authors[0] if authors else f"Студент {i+1}"
            year = work.get("year")
            abstract = work.get("abstract", "")
            institute = work.get("institute", "")
            major = work.get("major")
            
            # Если major отсутствует, выбираем случайное направление
            if not major:
                major = random.choice(REAL_PROGRAMS)
                print(f"   ⚠️ Для '{title[:30]}...' сгенерировано направление: {major}")
            
            source_url = work.get("source_url", "")
            
            # Создаём автора
            if author_full_name not in authors_cache:
                # Генерируем email

                counter = 1
                
                email = f"stud{str(i + 1).zfill(10)}@study.utmn.ru"
                while session.exec(select(Author).where(Author.email == email)).first():
                    email = f"stud{str(i + 1 + counter).zfill(10)}@study.utmn.ru"
                    counter += 1
                
                job_status = random.choices(
                    ["searching", "employed", "not_searching"],
                    weights=[0.5, 0.3, 0.2]
                )[0]
                
                author = Author(
                    email=email,
                    full_name=author_full_name,
                    program=major,
                    job_status=job_status,
                )
                session.add(author)
                session.flush()
                authors_cache[author_full_name] = author
                print(f"   Создан автор: {author_full_name} ({email})")
            
            author = authors_cache[author_full_name]
            
            # Теги
            tag_names = map_program_to_tags(major)
            all_tags = list(tags_by_name.keys())
            additional = random.sample(
                [t for t in all_tags if t not in tag_names],
                min(random.randint(0, 2), len(all_tags) - len(tag_names))
            )
            tag_names.extend(additional)
            tag_names = list(set(tag_names))[:4]
            
            supervisor = random.choice(list(teachers_cache.values())) if teachers_cache else None
            read_policy = random.choices(["open", "requires_approval"], weights=[0.3, 0.7])[0]
            
            artifact = Artifact(
                title=title,
                type="vkr",
                annotation=abstract or "Нет аннотации",
                file_path=source_url or f"https://library.utmn.ru/dl/vkr_{i+1}.pdf",
                year=year,
                curator_status="approved",
                read_policy=read_policy,
                author_id=author.id,
                supervisor_id=supervisor.id if supervisor else None,
            )
            session.add(artifact)
            session.flush()
            
            for tag_name in tag_names:
                tag = tags_by_name.get(tag_name)
                if tag:
                    session.execute(
                        text("INSERT INTO artifacttag (artifact_id, tag_id) VALUES (:a, :t) ON CONFLICT DO NOTHING"),
                        {"a": artifact.id, "t": tag.id}
                    )
            
            created_artifacts.append(artifact)
            if (i + 1) % 10 == 0:
                print(f"   Создано {i + 1} артефактов...")
        
        session.commit()
        print(f"   Создано {len(authors_cache)} авторов и {len(created_artifacts)} артефактов")

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
        print("✅ БАЗА ДАННЫХ УСПЕШНО НАПОЛНЕНА!")
        print("=" * 60)
        print(f"📊 Статистика:")
        print(f"   • {artifact_count} артефактов (ВКР)")
        print(f"   • {author_count} авторов (студентов)")
        print(f"   • {teacher_count} преподавателей")
        print(f"   • {tag_count} тегов")
        print(f"   • {len(partners)} партнёров")
        print(f"   • {subscription_count} подписок")
        print(f"   • {user_count} пользователей")
        
        print("\n🔐 Логины для входа:")
        print("   Партнёры:")
        for login_email in partners:
            print(f"     {login_email} / pass123")
        print("   Куратор:")
        print("     curator@demo.ru / pass123")
        print("   Админ:")
        print("     admin@demo.ru / pass123")
        print("   Авторы (вход по университетской почте):")
        for author in list(authors_cache.values())[:5]:
            print(f"     {author.email} / pass123")
        if len(authors_cache) > 5:
            print(f"     ... и ещё {len(authors_cache) - 5} авторов")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Наполнение БД тестовыми данными")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Путь к файлу libtheses.json"
    )
    args = parser.parse_args()
    
    seed(args.file)


if __name__ == "__main__":
    main()
