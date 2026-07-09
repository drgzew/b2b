"""
Наполняет БД тестовыми данными для пилота:
- 5 фейковых артефактов (ВКР, статьи, доклад) с тегами
- 2 партнёра (ГПН, СИБУР) с подписками из нескольких тегов
  (несколько тегов на подписку — чтобы индекс Жаккара имел смысл)
- 3 пользователя для входа: 2 партнёрских и 1 куратор

Запуск (из контейнера api или локально с настроенным DATABASE_URL):
    python scripts/seed.py

Логины после сидирования:
    gpn@demo.ru     / pass123  (роль: partner, партнёр: Газпромнефть)
    sibur@demo.ru   / pass123  (роль: partner, партнёр: СИБУР)
    curator@demo.ru / pass123  (роль: curator)
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, select  # noqa: E402

from backend.app.db import engine, init_db  # noqa: E402
from backend.app.models import Artifact, Partner, Subscription, Tag, User  # noqa: E402
from backend.app.security import hash_password  # noqa: E402


def get_or_create_tag(session: Session, name: str) -> Tag:
    tag = session.exec(select(Tag).where(Tag.name == name)).first()
    if not tag:
        tag = Tag(name=name)
        session.add(tag)
        session.commit()
        session.refresh(tag)
    return tag


ARTIFACTS = [
    {
        "title": "Оптимизация буровых растворов",
        "type": "vkr",
        "annotation": "ВКР о снижении затрат на буровые растворы за счёт подбора состава",
        "curator_status": "approved",
        "access_level": "annotation_only",
        "author_name": "И. Петров",
        "tag_names": ["нефтегаз"],
    },
    {
        "title": "Цифровой двойник насосной станции",
        "type": "vkr",
        "annotation": "Модель цифрового двойника для мониторинга состояния насосного оборудования",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "А. Смирнова",
        "tag_names": ["цифровизация", "нефтегаз"],
    },
    {
        "title": "Прогноз спроса в логистике методами ML",
        "type": "article",
        "annotation": "Статья о применении моделей машинного обучения для прогноза спроса",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "Д. Ким",
        "tag_names": ["логистика", "цифровизация"],
    },
    {
        "title": "Энергоэффективность буровых установок",
        "type": "talk",
        "annotation": "Доклад с конференции о путях повышения энергоэффективности",
        "curator_status": "approved",
        "access_level": "annotation_only",
        "author_name": "Е. Волков",
        "tag_names": ["энергетика", "нефтегаз"],
    },
    {
        "title": "Автоматизация учёта НИОКР",
        "type": "article",
        "annotation": "Статья про автоматизацию процессов учёта научно-исследовательских работ",
        "curator_status": "draft",  # ещё не прошла модерацию — не должна попадать в дайджест
        "access_level": "none",
        "author_name": "М. Орлова",
        "tag_names": ["цифровизация"],
    },
]


def seed() -> None:
    init_db()

    with Session(engine) as session:
        all_tag_names = {name for a in ARTIFACTS for name in a["tag_names"]}
        tags = {name: get_or_create_tag(session, name) for name in all_tag_names}

        for data in ARTIFACTS:
            tag_names = data.pop("tag_names")
            artifact = Artifact(**data)
            artifact.tags = [tags[name] for name in tag_names]
            session.add(artifact)
        session.commit()

        gpn = Partner(name="Газпромнефть — R&D", contact_email="rnd@gpn-demo.ru")
        sibur = Partner(name="СИБУР — Инновации", contact_email="innovations@sibur-demo.ru")
        session.add(gpn)
        session.add(sibur)
        session.commit()
        session.refresh(gpn)
        session.refresh(sibur)

        gpn_sub = Subscription(partner_id=gpn.id, name="Нефтегаз и цифровизация")
        gpn_sub.tags = [tags["нефтегаз"], tags["цифровизация"], tags["энергетика"]]
        session.add(gpn_sub)

        sibur_sub = Subscription(partner_id=sibur.id, name="Цифровизация и логистика")
        sibur_sub.tags = [tags["цифровизация"], tags["логистика"]]
        session.add(sibur_sub)
        session.commit()

        users = [
            User(
                email="gpn@demo.ru",
                password_hash=hash_password("pass123"),
                role="partner",
                partner_id=gpn.id,
            ),
            User(
                email="sibur@demo.ru",
                password_hash=hash_password("pass123"),
                role="partner",
                partner_id=sibur.id,
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
            f"Готово: {len(ARTIFACTS)} артефактов, 2 партнёра, 2 подписки, 3 пользователя.\n"
            "Логины: gpn@demo.ru / sibur@demo.ru / curator@demo.ru, пароль везде pass123"
        )


if __name__ == "__main__":
    seed()
