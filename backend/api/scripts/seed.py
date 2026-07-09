"""
Наполняет БД тестовыми данными для пилота:
- 5 фейковых артефактов (ВКР, статьи, доклад) с тегами
- 1 партнёр
- 3 подписки этого партнёра на разные теги

Запуск (из контейнера api или локально с настроенным DATABASE_URL):
    python scripts/seed.py
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, select  # noqa: E402

from app.db import engine, init_db  # noqa: E402
from app.models import Artifact, Partner, Subscription, Tag  # noqa: E402


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
        "status": "published",
        "access_level": "annotation_only",
        "author_name": "И. Петров",
        "tag_names": ["нефтегаз"],
    },
    {
        "title": "Цифровой двойник насосной станции",
        "type": "vkr",
        "annotation": "Модель цифрового двойника для мониторинга состояния насосного оборудования",
        "status": "published",
        "access_level": "full",
        "author_name": "А. Смирнова",
        "tag_names": ["цифровизация", "нефтегаз"],
    },
    {
        "title": "Прогноз спроса в логистике методами ML",
        "type": "article",
        "annotation": "Статья о применении моделей машинного обучения для прогноза спроса",
        "status": "published",
        "access_level": "full",
        "author_name": "Д. Ким",
        "tag_names": ["логистика", "цифровизация"],
    },
    {
        "title": "Энергоэффективность буровых установок",
        "type": "talk",
        "annotation": "Доклад с конференции о путях повышения энергоэффективности",
        "status": "published",
        "access_level": "annotation_only",
        "author_name": "Е. Волков",
        "tag_names": ["энергетика", "нефтегаз"],
    },
    {
        "title": "Автоматизация учёта НИОКР",
        "type": "article",
        "annotation": "Статья про автоматизацию процессов учёта научно-исследовательских работ",
        "status": "moderation",
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

        partner = Partner(name="Газпромнефть — R&D", contact_email="rnd@example.com")
        session.add(partner)
        session.commit()
        session.refresh(partner)

        subscribed_tags = ["нефтегаз", "цифровизация", "энергетика"]
        for tag_name in subscribed_tags:
            session.add(Subscription(partner_id=partner.id, tag_id=tags[tag_name].id))
        session.commit()

        print(
            f"Готово: {len(ARTIFACTS)} артефактов, 1 партнёр, "
            f"{len(subscribed_tags)} подписки на теги {subscribed_tags}"
        )


if __name__ == "__main__":
    seed()
