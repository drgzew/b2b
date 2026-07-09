"""
Наполняет БД тестовыми данными для пилота:
- 8 фейковых артефактов (ВКР, статьи, доклад) с тегами
- 3 партнёра (Газпромнефть, Яндекс, ЗапСибЭкоЦентр) с подписками из нескольких тегов
  (несколько тегов на подписку — чтобы индекс Жаккара имел смысл)
- 4 пользователя для входа: 3 партнёрских и 1 куратор

Запуск (из контейнера api или локально с настроенным DATABASE_URL):
    python scripts/seed.py

Логины после сидирования:
    gpn@demo.ru       / pass123  (роль: partner, партнёр: Газпромнефть)
    yandex@demo.ru    / pass123  (роль: partner, партнёр: Яндекс)
    eco@demo.ru       / pass123  (роль: partner, партнёр: ЗапСибЭкоЦентр)
    curator@demo.ru   / pass123  (роль: curator)
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
    # Существующие артефакты
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
    # Новые артефакты для расширения тематик
    {
        "title": "Применение нейросетей для интерпретации геофизических данных",
        "type": "article",
        "annotation": "Исследование использования свёрточных нейросетей для анализа сейсмических разрезов",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "А. Козлов",
        "tag_names": ["нефтегаз", "цифровизация", "машинное обучение"],
    },
    {
        "title": "Биоремедиация нефтезагрязнённых почв",
        "type": "vkr",
        "annotation": "ВКР по очистке почв с использованием микроорганизмов-деструкторов",
        "curator_status": "approved",
        "access_level": "annotation_only",
        "author_name": "Е. Зайцева",
        "tag_names": ["экология", "биотехнологии", "нефтегаз"],
    },
    {
        "title": "Разработка биопрепаратов для очистки сточных вод",
        "type": "article",
        "annotation": "Статья о создании консорциумов бактерий для очистки промышленных стоков",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "П. Соколов",
        "tag_names": ["биотехнологии", "экология"],
    },
    {
        "title": "Прогнозирование отказов оборудования с помощью ML",
        "type": "talk",
        "annotation": "Доклад о применении градиентного бустинга для предиктивного обслуживания",
        "curator_status": "approved",
        "access_level": "full",
        "author_name": "М. Иванова",
        "tag_names": ["цифровизация", "машинное обучение"],
    },
]


def seed() -> None:
    init_db()

    with Session(engine) as session:
        # Собираем все имена тегов из артефактов
        all_tag_names = {name for a in ARTIFACTS for name in a["tag_names"]}
        tags = {name: get_or_create_tag(session, name) for name in all_tag_names}

        # Создаём артефакты
        for data in ARTIFACTS:
            tag_names = data.pop("tag_names")
            artifact = Artifact(**data)
            artifact.tags = [tags[name] for name in tag_names]
            session.add(artifact)
        session.commit()

        # Создаём трёх партнёров
        gpn = Partner(name="Газпромнефть — R&D", contact_email="rnd@gpn-demo.ru")
        yandex = Partner(name="Яндекс — ИТ", contact_email="it@yandex-demo.ru")
        eco = Partner(name="ЗапСибЭкоЦентр", contact_email="eco@zsec-demo.ru")
        session.add(gpn)
        session.add(yandex)
        session.add(eco)
        session.commit()
        session.refresh(gpn)
        session.refresh(yandex)
        session.refresh(eco)

        # Подписки: у каждого партнёра своя подписка с несколькими тегами
        gpn_sub = Subscription(partner_id=gpn.id, name="Нефтегаз и цифровизация")
        gpn_sub.tags = [tags["нефтегаз"], tags["цифровизация"]]
        session.add(gpn_sub)

        yandex_sub = Subscription(partner_id=yandex.id, name="Цифровизация и ML")
        yandex_sub.tags = [tags["цифровизация"], tags["машинное обучение"]]
        session.add(yandex_sub)

        eco_sub = Subscription(partner_id=eco.id, name="Экология и биотехнологии")
        eco_sub.tags = [tags["экология"], tags["биотехнологии"]]
        session.add(eco_sub)
        session.commit()

        # Пользователи: по одному на каждого партнёра + куратор
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
            f"Готово: {len(ARTIFACTS)} артефактов, 3 партнёра, 3 подписки, 4 пользователя.\n"
            "Логины: gpn@demo.ru / yandex@demo.ru / eco@demo.ru / curator@demo.ru, пароль везде pass123"
        )


if __name__ == "__main__":
    seed()
