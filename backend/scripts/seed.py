"""
Наполняет БД тестовыми данными для пилота.
Гарантированное сохранение тегов через прямые SQL-вставки.
Запуск (из контейнера api): python scripts/seed.py
"""
import os
import sys

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
from app.sso import parse_tumgu_profile

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
# ТЕГИ ИЗ topics.ts
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
# АРТЕФАКТЫ (с тегами в виде имён)
# ============================================================
ARTIFACTS = [
    {
        "title": "Оптимизация буровых растворов",
        "type": "vkr",
        "annotation": "ВКР о снижении затрат на буровые растворы за счёт подбора состава",
        "curator_status": "approved",
        "read_policy": "requires_approval",
        "file_path": "https://vkr.utmn-demo.ru/works/1",
        "author_full_name": "Орлова Анна Сергеевна",
        "program": "05.03.02 География",
        "job_status": "searching",
        "tag_names": ["нефть", "бурение"],
    },
    {
        "title": "Цифровой двойник насосной станции",
        "type": "vkr",
        "annotation": "Модель цифрового двойника для мониторинга состояния насосного оборудования",
        "curator_status": "approved",
        "read_policy": "open",
        "file_path": "https://vkr.utmn-demo.ru/works/2",
        "author_full_name": "Соколов Дмитрий Алексеевич",
        "program": "05.03.03 Картография и геоинформатика",
        "job_status": "employed",
        "tag_names": ["цифровой двойник", "нефть"],
    },
    {
        "title": "Прогноз спроса в логистике методами ML",
        "type": "article",
        "annotation": "Статья о применении моделей машинного обучения для прогноза спроса",
        "curator_status": "approved",
        "read_policy": "open",
        "file_path": "https://articles.utmn-demo.ru/logistics-ml.pdf",
        "author_full_name": "Зайцева Екатерина Владимировна",
        "program": "02.03.03 Математическое обеспечение и администрирование информационных систем",
        "job_status": "not_searching",
        "tag_names": ["машинное обучение", "Big Data"],
    },
    {
        "title": "Энергоэффективность буровых установок",
        "type": "talk",
        "annotation": "Доклад с конференции о путях повышения энергоэффективности",
        "curator_status": "approved",
        "read_policy": "requires_approval",
        "file_path": "https://talks.utmn-demo.ru/energy-efficiency.pdf",
        "author_full_name": "Петров Максим Иванович",
        "program": "05.03.03 Картография и геоинформатика",
        "job_status": "searching",
        "tag_names": ["энергетика", "нефть"],
    },
    {
        "title": "Автоматизация учёта НИОКР",
        "type": "article",
        "annotation": "Статья про автоматизацию процессов учёта научно-исследовательских работ",
        "curator_status": "draft",
        "read_policy": "requires_approval",
        "file_path": "https://articles.utmn-demo.ru/niokr-automation.pdf",
        "author_full_name": "Волкова Ольга Павловна",
        "program": "09.03.02 Информационные системы и технологии",
        "job_status": "employed",
        "tag_names": ["информационные системы"],
    },
    {
        "title": "Применение нейросетей для интерпретации геофизических данных",
        "type": "article",
        "annotation": "Исследование использования свёрточных нейросетей для анализа сейсмических разрезов",
        "curator_status": "approved",
        "read_policy": "open",
        "file_path": "https://articles.utmn-demo.ru/neural-geophysics.pdf",
        "author_full_name": "Смирнов Сергей Николаевич",
        "program": "02.03.03 Математическое обеспечение и администрирование информационных систем",
        "job_status": "searching",
        "tag_names": ["нейросети", "сейсмика"],
    },
    {
        "title": "Биоремедиация нефтезагрязнённых почв",
        "type": "vkr",
        "annotation": "ВКР по очистке почв с использованием микроорганизмов-деструкторов",
        "curator_status": "approved",
        "read_policy": "requires_approval",
        "file_path": "https://vkr.utmn-demo.ru/works/4",
        "author_full_name": "Козлова Анастасия Игоревна",
        "program": "05.03.06 Экология и природопользование",
        "job_status": "not_searching",
        "tag_names": ["экология", "очистка воды"],
    },
    {
        "title": "Разработка биопрепаратов для очистки сточных вод",
        "type": "article",
        "annotation": "Статья о создании консорциумов бактерий для очистки промышленных стоков",
        "curator_status": "approved",
        "read_policy": "open",
        "file_path": "https://articles.utmn-demo.ru/biopreparations.pdf",
        "author_full_name": "Иванов Павел Андреевич",
        "program": "09.03.03 Прикладная информатика",
        "job_status": "searching",
        "tag_names": ["экология", "очистка воды"],
    },
    {
        "title": "Прогнозирование отказов оборудования с помощью ML",
        "type": "talk",
        "annotation": "Доклад о применении градиентного бустинга для предиктивного обслуживания",
        "curator_status": "approved",
        "read_policy": "open",
        "file_path": "https://talks.utmn-demo.ru/predictive-maintenance.pdf",
        "author_full_name": "Иванова Мария Дмитриевна",
        "program": "09.03.02 Информационные системы и технологии",
        "job_status": "employed",
        "tag_names": ["машинное обучение", "нейросети"],
    },
    # Добавьте в ARTIFACTS:
    {
        "title": "Новая ВКР на модерации",
        "type": "vkr",
        "annotation": "Работа ожидает проверки куратора",
        "curator_status": "draft",
        "read_policy": "requires_approval",
        "file_path": "https://vkr.utmn-demo.ru/works/draft1",
        "author_full_name": "Иванов Дмитрий Сергеевич",
        "program": "09.03.02 Информационные системы и технологии",
        "job_status": "searching",
        "tag_names": ["информационные системы", "цифровизация"],
    },
    {
        "title": "Статья на проверке",
        "type": "article",
        "annotation": "Статья ожидает одобрения куратора",
        "curator_status": "draft",
        "read_policy": "requires_approval",
        "file_path": "https://articles.utmn-demo.ru/draft-article.pdf",
        "author_full_name": "Петров Иван Сергеевич",
        "program": "02.03.03 Математическое обеспечение и администрирование информационных систем",
        "job_status": "searching",
        "tag_names": ["машинное обучение", "AI"],
    },
]

# ============================================================
# ПАРТНЁРЫ И ПОДПИСКИ
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

TEACHER = {
    "full_name": "Шевляков Артём Николаевич",
    "email": "a.n.shevlyakov@utmn.ru",
    "department": "Школа компьютерных наук",
    "position": "Заместитель директора по развитию, д.ф.-м.н., профессор",
}


def get_or_create_author(session: Session, full_name: str, program: str, job_status: str, author_counter: int) -> Author:
    email = f"stud0000{author_counter:06d}@study.utmn.ru"
    author = session.exec(select(Author).where(Author.email == email)).first()
    if author:
        return author
    profile = parse_tumgu_profile(email)
    author = Author(
        email=email,
        full_name=full_name,
        photo_url=profile.get("photo_url"),
        birth_date=profile.get("birth_date"),
        program=program,
        job_status=job_status,
    )
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


def seed() -> None:
    init_db()

    with Session(engine) as session:
        # 1. Полная очистка
        session.execute(text("TRUNCATE TABLE digestitem, request, artifacttag, subscriptiontag, artifact, subscription, partner, \"user\", author, teacher, favorite, internship CASCADE;"))
        session.commit()

        # 2. Создаём теги с фиксированными ID
        print("Создаём теги из topics.ts...")
        for topic in TOPICS:
            for tag_data in topic["tags"]:
                tag = Tag(id=tag_data["id"], name=tag_data["name"])
                session.merge(tag)
        session.commit()

        tags_by_name = {tag.name: tag for tag in session.exec(select(Tag)).all()}
        print(f"Создано {len(tags_by_name)} тегов")

        # 3. Преподаватель
        teacher = session.exec(select(Teacher).where(Teacher.email == TEACHER["email"])).first()
        if not teacher:
            teacher = Teacher(**TEACHER)
            session.add(teacher)
            session.commit()
            session.refresh(teacher)

        # 4. Создаём авторов и артефакты (без привязки тегов, сделаем позже)
        print("Создаём артефакты...")
        authors_by_email = {}
        author_counter = 0
        artifacts_list = []

        for data in ARTIFACTS:
            author_counter += 1
            author = get_or_create_author(
                session,
                data["author_full_name"],
                data["program"],
                data["job_status"],
                author_counter,
            )
            authors_by_email[author.email] = author

            tag_names = data.pop("tag_names")
            artifact = Artifact(
                title=data["title"],
                type=data["type"],
                annotation=data["annotation"],
                curator_status=data["curator_status"],
                read_policy=data["read_policy"],
                file_path=data["file_path"],
                author_id=author.id,
                supervisor_id=teacher.id,
            )
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            artifacts_list.append((artifact, tag_names))

        # 5. Привязываем теги к артефактам через прямой SQL
        print("Привязываем теги к артефактам...")
        for artifact, tag_names in artifacts_list:
            for tag_name in tag_names:
                tag = tags_by_name.get(tag_name)
                if tag:
                    session.execute(
                        text("INSERT INTO artifacttag (artifact_id, tag_id) VALUES (:a, :t) ON CONFLICT DO NOTHING"),
                        {"a": artifact.id, "t": tag.id}
                    )
            session.commit()

        # 6. Создаём партнёров и подписки (тоже без тегов, привяжем позже)
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

        # 7. Привязываем теги к подпискам через прямой SQL
        print("Привязываем теги к подпискам...")
        for sub, topic_tags in subscriptions_list:
            for tag_data in topic_tags:
                tag = tags_by_name.get(tag_data["name"])
                if tag:
                    session.execute(
                        text("INSERT INTO subscriptiontag (subscription_id, tag_id) VALUES (:s, :t) ON CONFLICT DO NOTHING"),
                        {"s": sub.id, "t": tag.id}
                    )
            session.commit()

        # 8. Создаём пользователей
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
        for email, author in authors_by_email.items():
            users.append(
                User(
                    email=email,
                    password_hash=hash_password("pass123"),
                    role="author",
                    author_id=author.id,
                )
            )
        session.add_all(users)
        session.commit()

        # 9. Избранное и стажировки (необязательно)
        artifacts = session.exec(select(Artifact)).all()
        if artifacts:
            gpn = partners["gpn@demo.ru"]
            yandex = partners["yandex@demo.ru"]
            eco = partners["eco@demo.ru"]
            if len(artifacts) >= 3:
                session.add(Favorite(artifact_id=artifacts[0].id, partner_id=gpn.id))
                session.add(Favorite(artifact_id=artifacts[2].id, partner_id=yandex.id))
                session.add(Favorite(artifact_id=artifacts[6].id, partner_id=eco.id))
            if len(artifacts) >= 2:
                session.add(
                    Internship(
                        artifact_id=artifacts[0].id,
                        partner_id=gpn.id,
                        student_name="Орлова Анна Сергеевна",
                        status="sent",
                    )
                )
                session.add(
                    Internship(
                        artifact_id=artifacts[4].id,
                        partner_id=yandex.id,
                        student_name="Волкова Ольга Павловна",
                        status="accepted",
                    )
                )
            session.commit()

        # 10. Диагностика
        artifact_tag_count = session.execute(text("SELECT COUNT(*) FROM artifacttag")).scalar()
        subscription_tag_count = session.execute(text("SELECT COUNT(*) FROM subscriptiontag")).scalar()
        print(f"Связей артефакт-тег: {artifact_tag_count}")
        print(f"Связей подписка-тег: {subscription_tag_count}")

        artifact_count = session.query(Artifact).count()
        subscription_count = session.query(Subscription).count()
        user_count = session.query(User).count()

        print(
            f"\n✅ Готово!\n"
            f"  • {artifact_count} артефактов\n"
            f"  • {len(authors_by_email)} авторов\n"
            f"  • 1 преподаватель\n"
            f"  • {len(partners)} партнёров с подписками\n"
            f"  • {subscription_count} подписок\n"
            f"  • {user_count} пользователей\n"
            f"\n🔐 Логины:\n"
            f"  Партнёры:\n"
            f"    gpn@demo.ru    / pass123  (Газпромнефть)\n"
            f"    yandex@demo.ru / pass123  (Яндекс)\n"
            f"    eco@demo.ru    / pass123  (ЗапСибЭкоЦентр)\n"
            f"  Куратор:\n"
            f"    curator@demo.ru / pass123\n"
            f"  Админ:\n"
            f"    admin@demo.ru / pass123\n"
            f"  Авторы (email как логин):\n"
        )
        for email in authors_by_email:
            print(f"    {email} / pass123")


if __name__ == "__main__":
    seed()