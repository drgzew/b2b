"""
CLI для импорта normalized.json в базу данных.

Сама логика импорта — в backend/app/importer.py, чтобы её же можно было
дёрнуть без консоли, через POST /admin/import (см. routers/admin.py).
Этот файл — только разбор аргументов командной строки и печать статистики,
поведение и флаги (--wipe, --file) не изменились.
"""
import argparse

from sqlmodel import Session

from backend.app.db import engine, init_db
from backend.app.importer import generate_report, import_artifacts, load_normalized_data


def import_from_file(file_path: str, wipe: bool = False):
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
    print("=" * 60)

    if stats["imported"] > 0:
        print(f"\nДобавлено {stats['imported']} артефактов.")
    else:
        print("\nНовых артефактов не добавлено!!")
        if stats["errors"] > 0:
            print(f"Ошибок при импорте: {stats['errors']} — см. отчёт ниже.")
            for detail in stats["error_details"][:5]:
                print(f"  - {detail}")

    generate_report(stats, "data-report.md")


def main():
    parser = argparse.ArgumentParser(
        description="Импорт артефактов из normalized.json в базу данных"
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Очистить базу данных перед импортом (перезалив)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default="parsing/data/normalized.json",
        help="Путь к файлу с нормализованными данными (по умолчанию: parsing/data/normalized.json)",
    )

    args = parser.parse_args()

    if args.wipe:
        print("Опция --wipe удалит все существующие артефакты и теги")
        response = input("Продолжить? (y/N): ")
        if response.lower() != "y":
            print("Импорт отменён")
            return

    import_from_file(args.file, wipe=args.wipe)


if __name__ == "__main__":
    main()
