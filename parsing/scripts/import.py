import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import List, Dict
from collections import Counter

from sqlmodel import Session, select, delete

from backend.app.db import *
from backend.app.models import *


def load_normalized_data(path: str) -> List[Dict]:
    """Load normalized data in JSON format."""
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


def get_or_create_author(session: Session, author_name: str, email: str = None) -> Optional[Author]:
    """
    Получает или создаёт автора по имени и email.
    """
    if not author_name:
        return None
    
    # Пробуем найти существующего автора по имени
    existing = session.exec(
        select(Author).where(Author.full_name == author_name)
    ).first()
    
    if existing:
        return existing
    
    # Если email не указан, генерируем уникальный email
    if not email:
        # Создаём основу для email из имени (транслитерация)
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        name_parts = author_name.lower().split()
        if name_parts:
            last_name = name_parts[0]
            base_email = ''.join(translit_map.get(c, c) for c in last_name)
        else:
            base_email = 'unknown'
        
        # Добавляем уникальный суффикс, чтобы избежать коллизий
        # Проверяем существование email в БД
        counter = 1
        email = f"{base_email}@utmn.ru"
        while session.exec(select(Author).where(Author.email == email)).first():
            email = f"{base_email}{counter}@utmn.ru"
            counter += 1
    
    # Создаём нового автора
    new_author = Author(
        email=email,
        full_name=author_name,
        photo_url=None,
        birth_date=None,
        program=None,
        job_status='searching'
    )
    session.add(new_author)
    session.flush()
    return new_author


def get_or_create_teacher(session: Session, teacher_name: str, department: str = None) -> Optional[Teacher]:
    """Получает или создаёт преподавателя."""
    if not teacher_name:
        return None
    
    existing = session.exec(
        select(Teacher).where(Teacher.full_name == teacher_name)
    ).first()
    
    if existing:
        return existing
    
    # Генерируем уникальный email
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    name_parts = teacher_name.lower().split()
    if name_parts:
        last_name = name_parts[0]
        base_email = ''.join(translit_map.get(c, c) for c in last_name)
    else:
        base_email = 'unknown'
    
    # Проверяем уникальность
    counter = 1
    email = f"{base_email}@utmn.ru"
    while session.exec(select(Teacher).where(Teacher.email == email)).first():
        email = f"{base_email}{counter}@utmn.ru"
        counter += 1
    
    new_teacher = Teacher(
        full_name=teacher_name,
        email=email,
        department=department or 'Не указан',
        position='Преподаватель'
    )
    session.add(new_teacher)
    session.flush()
    return new_teacher


def import_artifacts(artifacts_data: List[Dict], session: Session, wipe: bool = False) -> Dict:
    """Import artifacts into database."""
    stats = {
        'total': len(artifacts_data),
        'imported': 0,
        'skipped': 0,
        'errors': 0,
        'tags_created': 0,
        'tags_existing': 0,
        'with_annotation': 0,
        'with_tags': 0,
        'authors_created': 0,
        'teachers_created': 0,
        'tag_counter': Counter()
    }

    if wipe:
        print("Очистка базы данных...")
        # Правильный порядок удаления (сначала зависимые таблицы)
        session.execute(delete(SubscriptionTag))
        session.execute(delete(ArtifactTag))
        session.execute(delete(Internship))
        session.execute(delete(Request))
        session.execute(delete(PartnerArtifactAccess))
        session.execute(delete(Favorite))
        session.execute(delete(DigestItem))
        session.execute(delete(Artifact))
        session.execute(delete(Author))
        session.execute(delete(Teacher))
        session.execute(delete(Tag))
        session.commit()
        print("База данных очищена")

    # 1. Создаём всех авторов и преподавателей
    authors_cache = {}
    teachers_cache = {}
    
    print("Создание авторов и преподавателей...")
    for artifact_data in artifacts_data:
        # Автор
        author_name = artifact_data.get('author_name')
        if author_name and author_name not in authors_cache:
            author = get_or_create_author(session, author_name)
            if author:
                authors_cache[author_name] = author
                stats['authors_created'] += 1
        
        # Преподаватель (для ВКР из libtheses можно попробовать извлечь)
        # Пока оставляем пустым, т.к. в данных нет информации о руководителе
    
    session.commit()
    print(f"Авторов создано: {stats['authors_created']}")

    # 2. Создаём все теги
    all_tags = {}
    print("Создание тегов...")
    for artifact_data in artifacts_data:
        for tag_data in artifact_data.get('tags', []):
            tag_name = tag_data.get('name')
            if tag_name and tag_name not in all_tags:
                existing_tag = session.exec(select(Tag).where(Tag.name == tag_name)).first()
                if existing_tag:
                    all_tags[tag_name] = existing_tag
                    stats['tags_existing'] += 1
                else:
                    new_tag = Tag(name=tag_name)
                    session.add(new_tag)
                    session.flush()
                    all_tags[tag_name] = new_tag
                    stats['tags_created'] += 1

    session.commit()
    print(f"Теги: {stats['tags_created']} создано, {stats['tags_existing']} уже существовало")

    # 3. Импортируем артефакты
    print(f"\nИмпорт артефактов ({stats['total']})...")
    print("-" * 60)

    for i, artifact_data in enumerate(artifacts_data, 1):
        try:
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

            # Находим автора
            author_name = artifact_data.get('author_name')
            author = authors_cache.get(author_name) if author_name else None

            # Определяем тип артефакта
            artifact_type = artifact_data.get('type', 'article')
            
            # Определяем read_policy на основе access_level
            access_level = artifact_data.get('access_level', 'none')
            read_policy = 'open' if access_level == 'full' else 'requires_approval'

            # Создаём артефакт
            artifact = Artifact(
                title=title,
                type=artifact_type,
                annotation=annotation,
                file_path=artifact_data.get('file_path'),
                curator_status=artifact_data.get('curator_status', 'draft'),
                read_policy=read_policy,
                author_id=author.id if author else None,
                supervisor_id=None,  # Пока нет данных о руководителе
                created_at=artifact_data.get('created_at'),
                embedding=artifact_data.get('embedding'),
                # doi=artifact_data.get('doi'),  # Если добавили в модель
                # source_url=artifact_data.get('source_url'),
                # year=artifact_data.get('year'),
                # openalex_id=artifact_data.get('openalex_id')
            )

            # Добавляем теги
            for tag_data in artifact_tags:
                tag_name = tag_data.get('name')
                if tag_name and tag_name in all_tags:
                    artifact.tags.append(all_tags[tag_name])

            session.add(artifact)
            stats['imported'] += 1

            if i % 10 == 0:
                session.commit()
                print(f"[{i}/{stats['total']}] Импортировано: {title[:50]}...")

        except Exception as e:
            print(f"[{i}/{stats['total']}] Ошибка: {e}")
            stats['errors'] += 1
            session.rollback()
            continue

    session.commit()
    
    stats['openalex_count'] = sum(1 for a in artifacts_data if a.get('source') == 'openalex')
    stats['libtheses_count'] = sum(1 for a in artifacts_data if a.get('source') == 'utmnlib')
    return stats


def generate_report(stats: Dict, output_path: str = "data-report.md") -> None:
    """Generate a Markdown report of import statistics."""
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
    lines.append(f"- **Создано авторов:** {stats['authors_created']}")
    lines.append("")

    lines.append("## Данные")
    lines.append("")
    lines.append(f"- **С непустой аннотацией:** {stats['with_annotation']} ({stats['with_annotation']/stats['total']*100:.1f}%)")
    lines.append(f"- **С проставленными тегами:** {stats['with_tags']} ({stats['with_tags']/stats['total']*100:.1f}%)")
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
    """Main function of import from file."""
    artifacts_data = load_normalized_data(file_path)

    if not artifacts_data:
        print("Нет данных для импорта")
        return

    print(f"Загружено артефактов: {len(artifacts_data)}")
    print()

    print("Подключение к базе данных...")
    init_db()

    with Session(engine) as session:
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
    print(f"Создано авторов: {stats['authors_created']}")
    print(f"OpenAlex: {stats['openalex_count']}")
    print(f"UTMN Library: {stats['libtheses_count']}")
    print("=" * 60)

    if stats['imported'] > 0:
        print(f"\n✅ Добавлено {stats['imported']} артефактов.")
    else:
        print("\n⚠️ Новых артефактов не добавлено.")

    generate_report(stats)


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
        default="data/normalized.json",
        help="Путь к файлу с нормализованными данными"
    )

    args = parser.parse_args()

    if args.wipe:
        print("Опция --wipe удалит все существующие артефакты и теги")
        response = input("Продолжить? (y/N): ")
        if response.lower() != 'y':
            print("Импорт отменён")
            return

    import_from_file(args.file, wipe=args.wipe)


if __name__ == "__main__":
    main()
