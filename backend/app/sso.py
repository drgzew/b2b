"""
Вход через университетскую почту ТюмГУ.

На момент пилота неизвестно, будет ли это реальный SSO/LDAP ТюмГУ или другой
механизм — поэтому вся интеграция спрятана за одной функцией с фиксированной
сигнатурой: email -> профиль. Сейчас она возвращает детерминированные фейковые
данные (по email, без похода во внешнюю систему), но вызывающий код
(routers/authors.py) уже написан так, как будто получает данные из реального
входа — переключение на боевую интеграцию не потребует менять ничего, кроме
тела этой функции.

TODO(интеграция): заменить тело parse_tumgu_profile() на реальный вызов SSO/LDAP
ТюмГУ. Сохранить сигнатуру и набор полей (full_name, photo_url, birth_date,
program) — от этого зависят Author-модель и все эндпоинты /authors.
"""
import hashlib
from datetime import date, timedelta
from typing import TypedDict


class TumguProfile(TypedDict):
    full_name: str
    photo_url: str
    birth_date: date
    program: str


# Пары (имя, фамилия) согласованы по роду, чтобы не получить "Орлова Дмитрий"
_NAME_PAIRS = [
    ("Иван", "Петров"),
    ("Мария", "Смирнова"),
    ("Алексей", "Кузнецов"),
    ("Ольга", "Волкова"),
    ("Дмитрий", "Соколов"),
    ("Анна", "Орлова"),
    ("Сергей", "Ким"),
    ("Екатерина", "Егорова"),
]
_PROGRAMS = [
    "Нефтегазовое дело",
    "Прикладная информатика",
    "Промышленная теплоэнергетика",
    "Логистика и управление цепями поставок",
    "Строительство",
]


def parse_tumgu_profile(email: str) -> TumguProfile:
    """Имитирует ответ реального входа через почту ТюмГУ.

    Данные детерминированы по email (один и тот же email всегда даёт один и тот
    же профиль), чтобы демо и тесты были воспроизводимы. Реальных данных о
    людях эта функция не использует и не запрашивает.
    """
    seed = int(hashlib.sha256(email.encode()).hexdigest(), 16)

    first_name, last_name = _NAME_PAIRS[seed % len(_NAME_PAIRS)]
    program = _PROGRAMS[(seed // len(_NAME_PAIRS)) % len(_PROGRAMS)]

    # Возраст в правдоподобном для студента/выпускника диапазоне 20-27 лет
    age_days = 20 * 365 + (seed % (7 * 365))
    birth_date = date.today() - timedelta(days=age_days)

    return TumguProfile(
        full_name=f"{last_name} {first_name}",
        photo_url=f"https://avatars.example.tyumsu.ru/{hashlib.md5(email.encode()).hexdigest()}.jpg",
        birth_date=birth_date,
        program=program,
    )
