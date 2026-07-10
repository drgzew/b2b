import argparse
from datetime import datetime
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter

from sqlmodel import Session, select, delete
from sqlmodel import SQLModel

from backend.app.db import *
from backend.app.models import *

def load_normalized_data(path: str) -> List[Dict]:
    """ Load normalized data in JSON fromat.
    """
    file_path = Path(path)
    if not file_path.exists():
        print(f"Файл {file_path} не найден")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'artifacts' in data:
        return data['artifacts']
    else:
        print(f"Неизвестный формат данных в {path}")
        return []


def import_artifacts(artifacts_data: List[Dict], session: Session, wipe: bool = False) -> Dict:
    """ Import artifacts in database.
    """
    stats = {
        'total': len(artifacts_data),
        'imported': 0,
        'skipped': 0,
        'errors': 0,
        'tags_created': 0,
        'tags_existing': 0,
        'with_annotation': 0,
        'with_tags': 0,
        'tag_counter': Counter()
    }

    if wipe:
        print("Очистка базы данных...")
        # Удаляем все записи (каскадно)
        session.execute(delete(SubscriptionTag))
        session.execute(delete(ArtifactTag))
        session.execute(delete(Artifact))
        session.execute(delete(Tag))
        session.commit()
        print("База данных очищена")

    # Сначала создаем все теги (для избежания конфликтов)
    all_tags = {}
    for artifact_data in artifacts_data:
        for tag_data in artifact_data.get('tags', []):
            tag_name = tag_data.get('name')
            if tag_name and tag_name not in all_tags:
                # Проверяем, существует ли тег в БД
                existing_tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
                if existing_tag:
                    all_tags[tag_name] = existing_tag
                    stats['tags_existing'] += 1
                else:
                    # Создаем новый тег
                    new_tag = Tag(name=tag_name)
                    session.add(new_tag)
                    session.flush()  # Получаем ID
                    all_tags[tag_name] = new_tag
                    stats['tags_created'] += 1

    # Коммитим теги
    session.commit()
    print(f"Теги: {stats['tags_created']} создано, {stats['tags_existing']} уже существовало")

    # Импортируем артефакты
    print(f"\nИмпорт артефактов ({stats['total']})...")
    print("-" * 60)

    for i, artifact_data in enumerate(artifacts_data, 1):
        try:
            # Пропускаем, если нет названия
            title = artifact_data.get('title', '')
            if not title:
                print(f"[{i}/{stats['total']}] Пропущен (нет названия)")
                stats['skipped'] += 1
                continue

            # Считаем артефакты с аннотацией
            annotation = artifact_data.get('annotation', '')
            if annotation and len(annotation.strip()) > 10:
                stats['with_annotation'] += 1

            # Считаем артефакты с тегами
            artifact_tags = artifact_data.get('tags', [])
            if artifact_tags:
                stats['with_tags'] += 1
                for tag_data in artifact_tags:
                    tag_name = tag_data.get('name')
                    if tag_name:
                        stats['tag_counter'][tag_name] += 1

            # Создаём артефакт
            artifact = Artifact(
                title=artifact_data.get('title', ''),
                type=artifact_data.get('type'),
                annotation=artifact_data.get('annotation', ''),
                file_path=artifact_data.get('file_path'),
                curator_status=artifact_data.get('curator_status', 'draft'),
                access_level=artifact_data.get('access_level', 'none'),
                author_name=artifact_data.get('author_name'),
                created_at=artifact_data.get('created_at'),
                embedding=artifact_data.get('embedding'),
                # doi=artifact_data.get('doi'),
                # source_url=artifact_data.get('source_url'),
                # year=artifact_data.get('year'),
                # openalex_id=artifact_data.get('openalex_id')
            )

            # Добавляем теги
            for tag_data in artifact_data.get('tags', []):
                tag_name = tag_data.get('name')
                if tag_name and tag_name in all_tags:
                    artifact.tags.append(all_tags[tag_name])

            session.add(artifact)
            stats['imported'] += 1

            # Коммитим каждые 10 артефактов для экономии памяти
            if i % 10 == 0:
                session.commit()
                print(f"[{i}/{stats['total']}] Импортировано: {artifact.title[:50]}...")
 
        except Exception as e:
            print(f"[{i}/{stats['total']}] Ошибка: {e}")
            stats['errors'] += 1
            session.rollback()
            continue

    # Финальный коммит
    session.commit()
    return stats

def generate_report(stats: Dict, output_path: str = "data-report.md") -> None:
    """ Generate a Markdown report of import statistics.
    """
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

    lines.append("## Данные")
    lines.append("")
    lines.append(f"- **С непустой аннотацией:** {stats['with_annotation']} ({stats['with_annotation']/stats['total']*100:.1f}%)")
    lines.append(f"- **С проставленными тегами:** {stats['with_tags']} ({stats['with_tags']/stats['total']*100:.1f}%)")
    lines.append("")

    lines.append("## Топ-10 самых популярных тегов")
    lines.append("")
    lines.append("| # | Тег | Количество артефактов |")
    lines.append("|---|-----|-----------------------|")

    top_tags = stats['tag_counter'].most_common(10)
    for i, (tag_name, count) in enumerate(top_tags, 1):
        lines.append(f"| {i} | `{tag_name}` | {count} |")

    if not top_tags:
        lines.append("| - | *Нет тегов* | - |")

    lines.append("")

    lines.append("## Дополнительно")
    lines.append("")
    lines.append(f"- **Уникальных тегов:** {len(stats['tag_counter'])}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def import_from_file(file_path: str, wipe: bool = False):
    """ Main function of import from file.
    """
    artifacts_data = load_normalized_data(file_path)

    if not artifacts_data:
        print("Нет данных для импорта")
        return

    print(f"Загружено артефактов: {len(artifacts_data)}")
    print()

    # 2. Подключаемся к БД
    print("Подключение к базе данных...")
    init_db()  # Создаем таблицы, если их нет

    with Session(engine) as session:
        # 3. Импортируем
        stats = import_artifacts(artifacts_data, session, wipe=wipe)

    print("\n" + "=" * 60)
    print("СТАТИСТИКА ИМПОРТА")
    print("=" * 60)
    print(f"Всего артефактов в файле: {stats['total']}")
    print(f"Импортировано: {stats['imported']}")
    print(f"Пропущено (дубликаты): {stats['skipped']}")
    print(f"Ошибок: {stats['errors']}")
    print(f"Создано тегов: {stats['tags_created']}")
    print(f"Существующих тегов: {stats['tags_existing']}")
    print(f"С непустой аннотацией: {stats['with_annotation']}")
    print(f"С проставленными тегами: {stats['with_tags']}")
    print("=" * 60)
    
    if stats['imported'] > 0:
        print(f"\nДобавлено {stats['imported']} артефактов.")
    else:
        print("\nНовых артефактов не добавлено!!")

    generate_report(stats, "data-report.md")


def main():
    parser = argparse.ArgumentParser(
        description="Импорт артефактов из normalized.json в базу данных"
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Очистить базу данных перед импортом (перезалив)"
    )
    parser.add_argument(
        "--file",
        type=str,
        default="parsing/data/normalized.json",
        help="Путь к файлу с нормализованными данными (по умолчанию: parsing/data/normalized.json)"
    )

    args = parser.parse_args()

    # Если указан --wipe, запрашиваем подтверждение
    if args.wipe:
        print("Опция --wipe удалит все существующие артефакты и теги")
        response = input("Продолжить? (y/N): ")
        if response.lower() != 'y':
            print("Импорт отменён")
            return

    # Запускаем импорт
    import_from_file(args.file, wipe=args.wipe)

if __name__ == "__main__":
    main()
