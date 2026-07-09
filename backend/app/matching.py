from typing import Set


def match_by_tags(subscription_tags: Set[str], artifact_tags: Set[str]) -> float:
    """Индекс Жаккара между тегами подписки и тегами артефакта.

    relevance = |пересечение| / |объединение|, диапазон 0..1.
    0, если хотя бы одно из множеств пустое (совпадать нечему).
    """
    if not subscription_tags or not artifact_tags:
        return 0.0

    intersection = subscription_tags & artifact_tags
    union = subscription_tags | artifact_tags

    if not union:
        return 0.0

    return len(intersection) / len(union)
