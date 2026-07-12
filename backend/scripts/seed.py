"""
Наполняет БД тестовыми данными для пилота:
- 5 авторов, "залогиненных" через мок app/sso.py (см. TODO там про реальный SSO),
  с разными job_status
- 5 фейковых артефактов (ВКР, статьи, доклад) с тегами, привязанных к авторам
- 2 партнёра (ГПН, СИБУР) с подписками из нескольких тегов
  (несколько тегов на подписку — чтобы индекс Жаккара имел смысл)
- 4 пользователя для входа: 2 партнёрских, 1 куратор, 1 админ

Запуск (из контейнера api или локально с настроенным DATABASE_URL):
    python scripts/seed.py

Логины после сидирования:
    gpn@demo.ru     / pass123  (роль: partner, партнёр: Газпромнефть)
    sibur@demo.ru   / pass123  (роль: partner, партнёр: СИБУР)
    curator@demo.ru / pass123  (роль: curator)
    admin@demo.ru   / pass123  (роль: admin)
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, select  # noqa: E402

from app.db import engine, init_db  # noqa: E402
from app.models import (  # noqa: E402
    Artifact,
    Author,
    Favorite,
    Internship,
    Partner,
    Request as RequestModel,
    Subscription,
    Tag,
    Teacher,
    User,
)
from app.security import hash_password  # noqa: E402
from app.sso import parse_tumgu_profile  # noqa: E402


def get_or_create_tag(session: Session, name: str) -> Tag:
    tag = session.exec(select(Tag).where(Tag.name == name)).first()
    if not tag:
        tag = Tag(name=name)
        session.add(tag)
        session.commit()
        session.refresh(tag)
    return tag


def get_or_create_author(session: Session, email: str, job_status: str) -> Author:
    """Имитирует тот самый 'вход через почту ТюмГУ' на этапе загрузки работы —
    то же самое, что делает POST /authors/sso/tumgu, но напрямую, без HTTP."""
    author = session.exec(select(Author).where(Author.email == email)).first()
    if author:
        return author
    profile = parse_tumgu_profile(email)
    author = Author(email=email, job_status=job_status, **profile)
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


ARTIFACTS = [
    {
        "title": "Оптимизация буровых растворов",
        "type": "vkr",
        "annotation": "ВКР о снижении затрат на буровые растворы за счёт подбора состава",
        "curator_status": "approved",
        # requires_approval — партнёру нужно запросить и дождаться решения
        # автора/куратора (тот самый флоу "запрос -> кнопка разрешить/нет").
        "read_policy": "requires_approval",
        "file_path": "https://vkr.utmn-demo.ru/works/1",  # ВКР -> редирект по ссылке
        "author_email": "petrov.i@study.utmn.ru",
        "author_job_status": "searching",
        "has_supervisor": True,
        "tag_names": ["нефтегаз"],
    },
    {
        "title": "Цифровой двойник насосной станции",
        "type": "vkr",
        "annotation": "Модель цифрового двойника для мониторинга состояния насосного оборудования",
        "curator_status": "approved",
        # open — автор разрешил читать всем партнёрам сразу, без запроса.
        "read_policy": "open",
        "file_path": "https://vkr.utmn-demo.ru/works/2",
        "author_email": "smirnova.a@study.utmn.ru",
        "author_job_status": "employed",
        "has_supervisor": True,
        "tag_names": ["цифровизация", "нефтегаз"],
    },
    {
        "title": "Прогноз спроса в логистике методами ML",
        "type": "article",
        "annotation": "Статья о применении моделей машинного обучения для прогноза спроса",
        "curator_status": "approved",
        "read_policy": "open",
        "file_path": "https://articles.utmn-demo.ru/logistics-ml.pdf",  # статья -> PDF
        "author_email": "kim.d@study.utmn.ru",
        "author_job_status": "not_searching",
        "has_supervisor": False,
        "tag_names": ["логистика", "цифровизация"],
    },
    {
        "title": "Энергоэффективность буровых установок",
        "type": "talk",
        "annotation": "Доклад с конференции о путях повышения энергоэффективности",
        "curator_status": "approved",
        "read_policy": "requires_approval",
        "file_path": "https://talks.utmn-demo.ru/energy-efficiency.pdf",
        "author_email": "volkov.e@study.utmn.ru",
        "author_job_status": "searching",
        "has_supervisor": False,
        "tag_names": ["энергетика", "нефтегаз"],
    },
    {
        "title": "Автоматизация учёта НИОКР",
        "type": "article",
        "annotation": "Статья про автоматизацию процессов учёта научно-исследовательских работ",
        "curator_status": "draft",  # ещё не прошла модерацию — не должна попадать в дайджест
        "read_policy": "requires_approval",
        "file_path": None,
        "author_email": "orlova.m@study.utmn.ru",
        "author_job_status": "searching",
        "has_supervisor": False,
        "tag_names": ["цифровизация"],
    },
]

TEACHER = {
    "full_name": "Королёва Наталья Викторовна",
    "email": "koroleva.nv@utmn.ru",
    "department": "ШКН ТюмГУ",
    "position": "доцент",
}


def seed() -> None:
    init_db()

    with Session(engine) as session:
        teacher = session.exec(select(Teacher).where(Teacher.email == TEACHER["email"])).first()
        if not teacher:
            teacher = Teacher(**TEACHER)
            session.add(teacher)
            session.commit()
            session.refresh(teacher)

        all_tag_names = {name for a in ARTIFACTS for name in a["tag_names"]}
        tags = {name: get_or_create_tag(session, name) for name in all_tag_names}

        created_artifacts = []
        authors_by_email = {}
        for data in ARTIFACTS:
            data = dict(data)  # не мутируем ARTIFACTS между повторными вызовами
            tag_names = data.pop("tag_names")
            author_email = data.pop("author_email")
            author_job_status = data.pop("author_job_status")
            has_supervisor = data.pop("has_supervisor")

            author = get_or_create_author(session, author_email, author_job_status)
            authors_by_email[author_email] = author

            artifact = Artifact(
                **data,
                author_id=author.id,
                supervisor_id=teacher.id if has_supervisor else None,
            )
            artifact.tags = [tags[name] for name in tag_names]
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            created_artifacts.append(artifact)

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
            User(
                email="admin@demo.ru",
                password_hash=hash_password("pass123"),
                role="admin",
            ),
            # Логин автора — той же университетской почтой, что и в его
            # профиле (реалистично: "вход через почту ТюмГУ" и есть логин).
            User(
                email="petrov.i@study.utmn.ru",
                password_hash=hash_password("pass123"),
                role="author",
                author_id=authors_by_email["petrov.i@study.utmn.ru"].id,
            ),
            User(
                email="smirnova.a@study.utmn.ru",
                password_hash=hash_password("pass123"),
                role="author",
                author_id=authors_by_email["smirnova.a@study.utmn.ru"].id,
            ),
        ]
        session.add_all(users)
        session.commit()

        # Избранное: ГПН сохранил себе первый артефакт (по нефтегазу)
        session.add(Favorite(artifact_id=created_artifacts[0].id, partner_id=gpn.id))
        # СИБУР сохранил артефакт по логистике/цифровизации
        session.add(Favorite(artifact_id=created_artifacts[2].id, partner_id=sibur.id))
        session.commit()

        # Стажировки: разные статусы, чтобы сразу видеть весь workflow в демо
        session.add(
            Internship(
                artifact_id=created_artifacts[0].id,
                partner_id=gpn.id,
                student_name=created_artifacts[0].author.full_name,
                status="sent",
            )
        )
        session.add(
            Internship(
                artifact_id=created_artifacts[1].id,
                partner_id=gpn.id,
                student_name=created_artifacts[1].author.full_name,
                status="in_progress",
                response_date=datetime.utcnow(),
            )
        )
        session.commit()

        # Демо-запрос на полный текст артефакта с read_policy="requires_approval" —
        # чтобы сразу было видно кабинет автора/куратора с ожидающей заявкой
        # (кнопка "разрешить/нет"), а не только пустой список.
        session.add(
            RequestModel(
                artifact_id=created_artifacts[0].id,  # "Оптимизация буровых растворов"
                partner_id=gpn.id,
                type="full_text",
                status="sent",
            )
        )
        session.commit()

        print(
            f"Готово: {len(ARTIFACTS)} артефактов, {len(ARTIFACTS)} авторов, 1 преподаватель, "
            "2 партнёра, 2 подписки, 6 пользователей, 2 избранных, 2 стажировки, "
            "1 запрос на полный текст (ожидает решения).\n"
            "Логины:\n"
            "  gpn@demo.ru / sibur@demo.ru        — partner, pass123\n"
            "  curator@demo.ru / admin@demo.ru    — curator/admin, pass123\n"
            "  petrov.i@study.utmn.ru             — author (есть входящий запрос), pass123\n"
            "  smirnova.a@study.utmn.ru           — author (работа открыта всем, read_policy=open), pass123"
        )


if __name__ == "__main__":
    seed()
