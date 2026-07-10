"""
Наполняет БД тестовыми данными для пилота:
- 9 фейковых артефактов (ВКР, статьи, доклад) с тегами
- 3 партнёра (Газпромнефть, Яндекс, ЗапСибЭкоЦентр)
- Подписки партнёров соответствуют темам из topics.ts (с теми же ID)
- 4 пользователя для входа

Запуск (из контейнера api или локально с настроенным DATABASE_URL):
    python scripts/seed.py
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import Artifact, Partner, Subscription, Tag, User
from app.security import hash_password


# ============================================================
# ТЕГИ ИЗ topics.ts (скопированы полностью)
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
# АРТЕФАКТЫ (теги заменены на существующие из TOPICS)
# ============================================================
ARTIFACTS = [
    {
        "title": "Оптимизация буровых растворов",
        "type": "vkr",
        "annotation": "ВКР о снижении затрат на буровые растворы за счёт подбора состава",
        "curator_status": "approved",
        "access_level": "annotation_only",
        "author_name": "И. Петров",
        "tag_names": ["нефть", "бурение"],
    },
    {
        "title": "Цифровой двойник насосной станции",
        "type": "vkr",
        "annotation": "Модель цифрового двойника для мониторинга состояния насосного оборудования",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "А. Смирнова",
        "tag_names": ["цифровой двойник", "нефть"],
    },
    {
        "title": "Прогноз спроса в логистике методами ML",
        "type": "article",
        "annotation": "Статья о применении моделей машинного обучения для прогноза спроса",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "Д. Ким",
        "tag_names": ["машинное обучение", "Big Data"],
    },
    {
        "title": "Энергоэффективность буровых установок",
        "type": "talk",
        "annotation": "Доклад с конференции о путях повышения энергоэффективности",
        "curator_status": "approved",
        "access_level": "annotation_only",
        "author_name": "Е. Волков",
        "tag_names": ["энергетика", "нефть"],
    },
    {
        "title": "Автоматизация учёта НИОКР",
        "type": "article",
        "annotation": "Статья про автоматизацию процессов учёта научно-исследовательских работ",
        "curator_status": "draft",
        "access_level": "none",
        "author_name": "М. Орлова",
        "tag_names": ["информационные системы"],
    },
    {
        "title": "Применение нейросетей для интерпретации геофизических данных",
        "type": "article",
        "annotation": "Исследование использования свёрточных нейросетей для анализа сейсмических разрезов",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "А. Козлов",
        "tag_names": ["нейросети", "сейсмика"],
    },
    {
        "title": "Биоремедиация нефтезагрязнённых почв",
        "type": "vkr",
        "annotation": "ВКР по очистке почв с использованием микроорганизмов-деструкторов",
        "curator_status": "approved",
        "access_level": "annotation_only",
        "author_name": "Е. Зайцева",
        "tag_names": ["экология", "очистка воды"],
    },
    {
        "title": "Разработка биопрепаратов для очистки сточных вод",
        "type": "article",
        "annotation": "Статья о создании консорциумов бактерий для очистки промышленных стоков",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "П. Соколов",
        "tag_names": ["экология", "очистка воды"],
    },
    {
        "title": "Прогнозирование отказов оборудования с помощью ML",
        "type": "talk",
        "annotation": "Доклад о применении градиентного бустинга для предиктивного обслуживания",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "М. Иванова",
        "tag_names": ["машинное обучение", "нейросети"],
    },
]


def seed() -> None:
    init_db()

    with Session(engine) as session:
        # 1. Создаём все теги из TOPICS с фиксированными ID
        print("Создаём теги из topics.ts...")
        for topic in TOPICS:
            for tag_data in topic["tags"]:
                tag = Tag(id=tag_data["id"], name=tag_data["name"])
                session.merge(tag)  # merge — создаст или обновит по id
        session.commit()

        # Загружаем созданные теги в словарь для быстрого доступа по имени
        tags = {tag.name: tag for tag in session.exec(select(Tag)).all()}
        print(f"Создано {len(tags)} тегов")

        # 2. Создаём артефакты
        print("Создаём артефакты...")
        for data in ARTIFACTS:
            tag_names = data.pop("tag_names")
            artifact = Artifact(**data)
            artifact.tags = [tags[name] for name in tag_names if name in tags]
            session.add(artifact)
        session.commit()

        # 3. Создаём трёх партнёров
        print("Создаём партнёров...")
        gpn = Partner(name="Газпромнефть", contact_email="rnd@gpn-demo.ru")
        yandex = Partner(name="Яндекс", contact_email="it@yandex-demo.ru")
        eco = Partner(name="ЗапСибЭкоЦентр", contact_email="eco@zsec-demo.ru")
        session.add(gpn)
        session.add(yandex)
        session.add(eco)
        session.commit()
        session.refresh(gpn)
        session.refresh(yandex)
        session.refresh(eco)

        # 4. Создаём подписки на основе тем из TOPICS с фиксированными ID
        print("Создаём подписки партнёров...")

        # Газпромнефть → Нефтегазовые технологии (id=1)
        topic_gpn = TOPICS[0]  # id=1
        gpn_tag_names = [t["name"] for t in topic_gpn["tags"]]
        gpn_tags = [tags[name] for name in gpn_tag_names if name in tags]
        gpn_sub = Subscription(
            id=topic_gpn["id"],  # явно задаём id=1
            partner_id=gpn.id,
            name=topic_gpn["name"],
            description=topic_gpn["description"],
        )
        gpn_sub.tags = gpn_tags
        session.add(gpn_sub)

        # Яндекс → Искусственный интеллект (id=2)
        topic_yandex = TOPICS[1]  # id=2
        yandex_tag_names = [t["name"] for t in topic_yandex["tags"]]
        yandex_tags = [tags[name] for name in yandex_tag_names if name in tags]
        yandex_sub = Subscription(
            id=topic_yandex["id"],
            partner_id=yandex.id,
            name=topic_yandex["name"],
            description=topic_yandex["description"],
        )
        yandex_sub.tags = yandex_tags
        session.add(yandex_sub)

        # ЗапСибЭкоЦентр → Экология и энергетика (id=4)
        topic_eco = TOPICS[3]  # id=4
        eco_tag_names = [t["name"] for t in topic_eco["tags"]]
        eco_tags = [tags[name] for name in eco_tag_names if name in tags]
        eco_sub = Subscription(
            id=topic_eco["id"],
            partner_id=eco.id,
            name=topic_eco["name"],
            description=topic_eco["description"],
        )
        eco_sub.tags = eco_tags
        session.add(eco_sub)

        session.commit()

        # 5. Создаём пользователей
        print("Создаём пользователей...")
        users = [
            User(
                email="gpn@demo.ru",
                password_hash=hash_password("pass123"),
                role="partner",
                partner_id=gpn.id,
            ),
            User(
                email="yandex@demo.ru",
                password_hash=hash_password("pass123"),
                role="partner",
                partner_id=yandex.id,
            ),
            User(
                email="eco@demo.ru",
                password_hash=hash_password("pass123"),
                role="partner",
                partner_id=eco.id,
            ),
            User(
                email="curator@demo.ru",
                password_hash=hash_password("pass123"),
                role="curator",
            ),
        ]
        session.add_all(users)
        session.commit()

        print(
            f"\n✅ Готово!\n"
            f"   Артефактов: {len(ARTIFACTS)}\n"
            f"   Партнёров: 3\n"
            f"   Подписок: 3\n"
            f"   Пользователей: 4\n"
            f"\n🔐 Логины:\n"
            f"   gpn@demo.ru     / pass123  (Газпромнефть)\n"
            f"   yandex@demo.ru  / pass123  (Яндекс)\n"
            f"   eco@demo.ru     / pass123  (ЗапСибЭкоЦентр)\n"
            f"   curator@demo.ru / pass123  (Куратор)\n"
        )


if __name__ == "__main__":
    seed()