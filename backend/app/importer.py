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
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlmodel import Session, delete, select

from .models import Artifact, ArtifactTag, Author, SubscriptionTag, Tag
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


def _synthetic_email_for_author(full_name: str) -> str:
    """Синтетический email для автора без реального адреса (парсер не знает
    почту реальных авторов — только их имя). Детерминирован по имени: один и
    тот же автор в разных артефактах получает одну и ту же учётку вместо
    дублей, но имя не публикуется наружу как часть email."""
    digest = hashlib.sha256(full_name.encode()).hexdigest()[:16]
    return f"parsed-{digest}@import.utmn.ru"


def get_or_create_author_by_name(session: Session, full_name: str) -> Author:
    email = _synthetic_email_for_author(full_name)
    author = session.exec(select(Author).where(Author.email == email)).first()
    if author:
        return author
    profile = parse_tumgu_profile(email)
    author = Author(
        email=email,
        full_name=full_name,  # реальное имя из парсера — не перезаписываем моком
        photo_url=profile.get("photo_url"),
        birth_date=profile.get("birth_date"),
        program=None,  # у парсера нет данных о направлении подготовки
        job_status="searching",
    )
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


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

    if wipe:
        print("Очистка базы данных...")
        # ArtifactTag/SubscriptionTag — явные модели связки (см. models.py),
        # используем их вместо текстовых имён таблиц, чтобы не разъезжаться
        # при переименованиях схемы.
        session.execute(delete(SubscriptionTag))
        session.execute(delete(ArtifactTag))
        session.execute(delete(Artifact))
        session.execute(delete(Tag))
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

    for i, artifact_data in enumerate(artifacts_data, 1):
        try:
            title = artifact_data.get("title", "")
            if not title:
                print(f"[{i}/{stats['total']}] Пропущен (нет названия)")
                stats["skipped"] += 1
                continue

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

            # author_name -> author_id: раньше это было свободной строкой на
            # самом Artifact, сейчас — связь на Author (см. models.py).
            author_id: Optional[int] = None
            author_name = artifact_data.get("author_name")
            if author_name:
                if author_name not in authors_by_name:
                    authors_by_name[author_name] = get_or_create_author_by_name(session, author_name)
                author_id = authors_by_name[author_name].id

            # access_level -> read_policy, см. ACCESS_LEVEL_TO_READ_POLICY выше.
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
                created_at=created_at,
                embedding=artifact_data.get("embedding"),
            )

            for tag_data in artifact_tags:
                tag_name = tag_data.get("name")
                if tag_name and tag_name in all_tags:
                    artifact.tags.append(all_tags[tag_name])

            session.add(artifact)
            stats["imported"] += 1

            if i % 10 == 0:
                session.commit()
                print(f"[{i}/{stats['total']}] Импортировано: {artifact.title[:50]}...")

        except Exception as e:
            print(f"[{i}/{stats['total']}] Ошибка: {e}")
            stats["errors"] += 1
            if len(stats["error_details"]) < 20:
                stats["error_details"].append(f"[{i}] {artifact_data.get('title', '?')[:60]}: {e}")
            session.rollback()
            continue

    session.commit()

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
