"""
Импорт нормализованных артефактов (parsing/data/normalized.json) в базу данных.

Раньше эта логика жила только в parsing/scripts/import.py и создавала Artifact
через устаревшие поля access_level/author_name — их больше нет на модели
(переименованы в read_policy / author_id ещё на этапе бэкенда, а парсер не
обновили). Из-за try/except на каждую запись это не падало с ошибкой, а тихо
считалось как "error" в статистике — то есть НИ ОДИН реальный артефакт не
импортировался, только теги. Здесь — исправленная версия с реальным
маппингом на текущую схему.

Вынесено сюда (а не оставлено только в parsing/scripts/import.py), чтобы одну
и ту же логику можно было дёрнуть и из консоли (CLI), и из админки без
консоли (POST /admin/import) — см. routers/admin.py.
"""
import hashlib
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlmodel import Session, delete, select

from .models import (
    Artifact,
    ArtifactTag,
    Author,
    DigestItem,
    Favorite,
    Internship,
    PartnerArtifactAccess,
    Request,
    SubscriptionTag,
    Tag,
    Teacher,
    User,
)
from .security import hash_password
from .sso import parse_tumgu_profile

# Старый формат access_level (full|annotation_only|none) — трёхстороннее
# состояние из normalize.py, который не переписывали (его выход — стабильный
# файловый контракт, а сайт-источник ВКР уже недоступен, чтобы перегенерировать
# данные заново). Маппим в новый read_policy (open|requires_approval) на входе
# в БД, а не меняем формат normalized.json.
#   full            -> open                (текст был в открытом доступе у источника)
#   annotation_only -> requires_approval    (виден только реферат — нужно решение)
#   none            -> requires_approval    (доступа не было вовсе — тем более "запрет")
ACCESS_LEVEL_TO_READ_POLICY = {
    "full": "open",
    "annotation_only": "requires_approval",
    "none": "requires_approval",
}


# Транслитерация для генерации читаемых студенческих email по ФИО
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _translit(text: str) -> str:
    return "".join(_TRANSLIT.get(ch, ch) for ch in text.lower())


def _email_for_author(full_name: str) -> str:
    """Читаемый студенческий email по ФИО ('Иванов Андрей Сергеевич' ->
    'a.s.ivanov@study.utmn.ru', 'Anna Glazkova' -> 'a.glazkova@study.utmn.ru').
    Детерминирован по имени: один автор в разных артефактах — одна учётка.
    Короткий хеш в конце защищает от коллизий однофамильцев."""
    parts = [p for p in re.split(r"[\s.,]+", full_name.strip()) if p]
    if not parts:
        digest = hashlib.sha256(full_name.encode()).hexdigest()[:8]
        return f"parsed-{digest}@import.utmn.ru"
    # У русских имён фамилия обычно первая ('Иванов Андрей Сергеевич'),
    # у западного порядка — последняя ('Anna Glazkova'). Различаем по алфавиту.
    is_cyrillic = bool(re.search(r"[а-яё]", full_name, re.I))
    surname = parts[0] if is_cyrillic else parts[-1]
    initials = parts[1:] if is_cyrillic else parts[:-1]
    prefix = ".".join([_translit(p)[0] for p in initials if p][:2])
    local = f"{prefix}.{_translit(surname)}" if prefix else _translit(surname)
    local = re.sub(r"[^a-z0-9.]", "", local)
    digest = hashlib.sha256(full_name.encode()).hexdigest()[:4]
    return f"{local}.{digest}@study.utmn.ru"


def _ensure_author_user(session: Session, author: Author) -> None:
    """Учётная запись для входа автора (role=author, пароль демо-стандарта).
    Импортированные авторы — реальные люди из статей/ВКР, им нужен рабочий
    логин в кабинет автора."""
    existing = session.exec(select(User).where(User.email == author.email)).first()
    if existing:
        return
    session.add(
        User(
            email=author.email,
            password_hash=hash_password("pass123"),
            role="author",
            author_id=author.id,
        )
    )
    session.commit()


def get_or_create_author_by_name(
    session: Session, full_name: str, program: Optional[str] = None
) -> Author:
    email = _email_for_author(full_name)
    author = session.exec(select(Author).where(Author.email == email)).first()
    if author:
        # Направление могло появиться в более поздней записи того же автора
        if program and not author.program:
            author.program = program
            session.add(author)
            session.commit()
            session.refresh(author)
        return author
    profile = parse_tumgu_profile(email)
    author = Author(
        email=email,
        full_name=full_name,  # реальное имя из парсера — не перезаписываем моком
        photo_url=profile.get("photo_url"),
        birth_date=profile.get("birth_date"),
        program=program,  # направление, подобранное normalize.py по тематике
        job_status="searching",
    )
    session.add(author)
    session.commit()
    session.refresh(author)
    _ensure_author_user(session, author)
    return author


def get_or_create_teacher_by_name(session: Session, full_name: str) -> Teacher:
    """Научный руководитель ВКР. Email синтетический (парсер знает только имя)."""
    digest = hashlib.sha256(full_name.encode()).hexdigest()[:8]
    email = f"teacher-{digest}@utmn.ru"
    teacher = session.exec(select(Teacher).where(Teacher.email == email)).first()
    if teacher:
        return teacher
    teacher = Teacher(
        full_name=full_name,
        email=email,
        department="Тюменский государственный университет",
        position="Научный руководитель",
    )
    session.add(teacher)
    session.commit()
    session.refresh(teacher)
    return teacher


def import_artifacts(artifacts_data: List[Dict], session: Session, wipe: bool = False) -> Dict:
    """Импортирует нормализованные артефакты в БД. Возвращает статистику."""
    stats = {
        "total": len(artifacts_data),
        "imported": 0,
        "skipped": 0,
        "errors": 0,
        "error_details": [],  # первые несколько текстов ошибок — для диагностики
        "tags_created": 0,
        "tags_existing": 0,
        "with_annotation": 0,
        "with_tags": 0,
        "tag_counter": Counter(),
    }

    # При wipe теги подписок партнёров тоже удаляются (FK на tag) — запоминаем
    # их по именам, чтобы восстановить связи после импорта. Иначе после
    # «очистить и импортировать заново» все дайджесты партнёров пустеют.
    subscription_tag_names: Dict[int, List[str]] = {}

    if wipe:
        print("Очистка базы данных...")
        from .models import Subscription

        for sub in session.exec(select(Subscription)).all():
            subscription_tag_names[sub.id] = [t.name for t in sub.tags]

        # Важно удалить ВСЕ таблицы, у которых есть FK на artifact.id, а не
        # только artifacttag — иначе DELETE FROM artifact падает по внешнему
        # ключу, если в базе уже есть избранное/запросы/стажировки/дайджесты
        # (например, от ранее отработавшего scripts/seed.py). Порядок должен
        # идти от таблиц-потомков к artifact/tag, а не наоборот.
        session.execute(delete(DigestItem))
        session.execute(delete(Request))
        session.execute(delete(Favorite))
        session.execute(delete(Internship))
        session.execute(delete(PartnerArtifactAccess))
        session.execute(delete(SubscriptionTag))
        session.execute(delete(ArtifactTag))
        session.execute(delete(Artifact))
        session.execute(delete(Tag))
        # Авторов и их учётки тоже чистим: работы удалены, а повторный импорт
        # создал бы каждому автору дубль профиля (email-генерация здесь и в
        # seed.py отличается) — в списках админки появлялись бы двойники, а
        # старые логины открывали бы пустые кабинеты.
        session.execute(delete(User).where(User.role == "author"))
        session.execute(delete(Author))
        session.commit()
        print("База данных очищена")

    # Сначала все теги — чтобы избежать конфликтов и лишних select внутри цикла артефактов.
    all_tags: Dict[str, Tag] = {}
    for artifact_data in artifacts_data:
        for tag_data in artifact_data.get("tags", []):
            tag_name = tag_data.get("name")
            if tag_name and tag_name not in all_tags:
                existing_tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
                if existing_tag:
                    all_tags[tag_name] = existing_tag
                    stats["tags_existing"] += 1
                else:
                    new_tag = Tag(name=tag_name)
                    session.add(new_tag)
                    session.flush()
                    all_tags[tag_name] = new_tag
                    stats["tags_created"] += 1
    session.commit()
    print(f"Теги: {stats['tags_created']} создано, {stats['tags_existing']} уже существовало")

    # Авторы — по имени, отдельным проходом, чтобы не плодить дубли одного и
    # того же автора при повторяющемся author_name на разных артефактах.
    authors_by_name: Dict[str, Author] = {}

    print(f"\nИмпорт артефактов ({stats['total']})...")
    print("-" * 60)

    # Названия уже существующих артефактов — защита от дублей: seed.py сеет
    # ВКР из libtheses.json, а normalized.json содержит их же; повторный
    # импорт того же файла тоже не должен плодить копии.
    existing_titles = {
        row for row in session.exec(select(Artifact.title)).all()
    }

    for i, artifact_data in enumerate(artifacts_data, 1):
        try:
            title = artifact_data.get("title", "")
            if not title:
                print(f"[{i}/{stats['total']}] Пропущен (нет названия)")
                stats["skipped"] += 1
                continue

            if title in existing_titles:
                stats["skipped"] += 1
                continue
            existing_titles.add(title)

            annotation = artifact_data.get("annotation", "")
            if annotation and len(annotation.strip()) > 10:
                stats["with_annotation"] += 1

            artifact_tags = artifact_data.get("tags", [])
            if artifact_tags:
                stats["with_tags"] += 1
                for tag_data in artifact_tags:
                    tag_name = tag_data.get("name")
                    if tag_name:
                        stats["tag_counter"][tag_name] += 1

            # Автор: формат v2 — объект {full_name, program} (реальный автор
            # ТюмГУ, направление подобрано normalize.py по тематике работы);
            # legacy-формат — свободная строка author_name.
            author_id: Optional[int] = None
            author_obj = artifact_data.get("author")
            if isinstance(author_obj, dict) and author_obj.get("full_name"):
                full_name = author_obj["full_name"]
                if full_name not in authors_by_name:
                    authors_by_name[full_name] = get_or_create_author_by_name(
                        session, full_name, program=author_obj.get("program")
                    )
                author_id = authors_by_name[full_name].id
            else:
                author_name = artifact_data.get("author_name")
                if author_name:
                    if author_name not in authors_by_name:
                        authors_by_name[author_name] = get_or_create_author_by_name(session, author_name)
                    author_id = authors_by_name[author_name].id

            # Научный руководитель (у ВКР; извлекается normalize.py из описания)
            supervisor_id: Optional[int] = None
            supervisor_obj = artifact_data.get("supervisor")
            if isinstance(supervisor_obj, dict) and supervisor_obj.get("full_name"):
                supervisor_id = get_or_create_teacher_by_name(
                    session, supervisor_obj["full_name"]
                ).id

            # read_policy: v2 пишет его напрямую; legacy-файлы несут только
            # access_level — маппим по ACCESS_LEVEL_TO_READ_POLICY выше.
            read_policy = artifact_data.get("read_policy")
            if read_policy not in ("open", "requires_approval"):
                access_level = artifact_data.get("access_level", "none")
                read_policy = ACCESS_LEVEL_TO_READ_POLICY.get(access_level, "requires_approval")

            created_at_raw = artifact_data.get("created_at")
            created_at = datetime.fromisoformat(created_at_raw) if created_at_raw else datetime.utcnow()

            artifact = Artifact(
                title=title,
                type=artifact_data.get("type") or "article",
                annotation=annotation,
                file_path=artifact_data.get("file_path") or artifact_data.get("source_url"),
                curator_status=artifact_data.get("curator_status", "draft"),
                read_policy=read_policy,
                author_id=author_id,
                supervisor_id=supervisor_id,
                created_at=created_at,
                embedding=artifact_data.get("embedding"),
            )

            for tag_data in artifact_tags:
                tag_name = tag_data.get("name")
                if tag_name and tag_name in all_tags:
                    artifact.tags.append(all_tags[tag_name])

            session.add(artifact)
            # Коммитим каждый артефакт отдельно: батчевый коммит при ошибке
            # откатывал бы уже посчитанные в статистике записи.
            session.commit()
            stats["imported"] += 1

            if i % 50 == 0:
                print(f"[{i}/{stats['total']}] Импортировано: {artifact.title[:50]}...")

        except Exception as e:
            print(f"[{i}/{stats['total']}] Ошибка: {e}")
            stats["errors"] += 1
            if len(stats["error_details"]) < 20:
                stats["error_details"].append(f"[{i}] {artifact_data.get('title', '?')[:60]}: {e}")
            session.rollback()
            continue

    session.commit()

    # Восстанавливаем теги подписок, снесённые wipe-ом: тег с тем же именем
    # либо уже пересоздан импортом, либо создаётся заново.
    if subscription_tag_names:
        from .models import Subscription

        restored_links = 0
        for sub_id, tag_names in subscription_tag_names.items():
            subscription = session.get(Subscription, sub_id)
            if not subscription:
                continue
            sub_tags = []
            for name in tag_names:
                if name not in all_tags:
                    existing = session.exec(select(Tag).where(Tag.name == name)).first()
                    if not existing:
                        existing = Tag(name=name)
                        session.add(existing)
                        session.flush()
                    all_tags[name] = existing
                sub_tags.append(all_tags[name])
            subscription.tags = sub_tags
            session.add(subscription)
            restored_links += len(sub_tags)
        session.commit()
        print(f"Восстановлены теги подписок: {restored_links} связей")

    stats["openalex_count"] = sum(1 for a in artifacts_data if a.get("source") == "openalex")
    stats["libtheses_count"] = sum(1 for a in artifacts_data if a.get("source") == "utmnlib")
    return stats


def load_normalized_data(path: str) -> List[Dict]:
    file_path = Path(path)
    if not file_path.exists():
        print(f"Файл {file_path} не найден")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        import json

        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "artifacts" in data:
        return data["artifacts"]
    else:
        print(f"Неизвестный формат данных в {path}")
        return []


def generate_report(stats: Dict, output_path: str = "data-report.md") -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Отчёт по импорту артефактов")
    lines.append("")
    lines.append(f"*Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    lines.append("## Общая статистика")
    lines.append("")
    lines.append(f"- **Всего артефактов в файле:** {stats['total']}")
    lines.append(f"- **Импортировано:** {stats['imported']}")
    lines.append(f"- **Пропущено (ошибки):** {stats['errors']}")
    lines.append(f"- **Создано тегов:** {stats['tags_created']}")
    lines.append(f"- **Существующих тегов:** {stats['tags_existing']}")
    lines.append("")

    if stats.get("error_details"):
        lines.append("## Первые ошибки (для диагностики)")
        lines.append("")
        for detail in stats["error_details"]:
            lines.append(f"- {detail}")
        lines.append("")

    lines.append("## Данные")
    lines.append("")
    total = max(stats["total"], 1)  # защита от деления на 0 на пустом файле
    lines.append(f"- **С непустой аннотацией:** {stats['with_annotation']} ({stats['with_annotation']/total*100:.1f}%)")
    lines.append(f"- **С проставленными тегами:** {stats['with_tags']} ({stats['with_tags']/total*100:.1f}%)")
    lines.append("")

    lines.append("## По источникам")
    lines.append("")
    lines.append(f"- **OpenAlex:** {stats.get('openalex_count', 0)}")
    lines.append(f"- **UTMN Library (ВКР):** {stats.get('libtheses_count', 0)}")
    lines.append("")

    lines.append("## Топ-10 самых популярных тегов")
    lines.append("")
    lines.append("| # | Тег | Количество артефактов |")
    lines.append("|---|-----|-----------------------|")

    top_tags = stats["tag_counter"].most_common(10)
    for i, (tag_name, count) in enumerate(top_tags, 1):
        lines.append(f"| {i} | `{tag_name}` | {count} |")
    if not top_tags:
        lines.append("| - | *Нет тегов* | - |")
    lines.append("")

    lines.append("## Дополнительно")
    lines.append("")
    lines.append(f"- **Уникальных тегов:** {len(stats['tag_counter'])}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
