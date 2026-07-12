"""
Workflow статусов Internship: sent -> accepted -> in_progress -> rejected|completed.

"rejected" оставлен доступным из sent/accepted/in_progress — на практике партнёр
или куратор может отказаться на любом шаге, не только в конце. "completed"
достижим только после in_progress — нельзя завершить стажировку, которая
не была принята и не шла.
"""
from typing import Dict, Set

ALL_STATUSES = {"sent", "accepted", "in_progress", "rejected", "completed"}

ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "sent": {"accepted", "rejected"},
    "accepted": {"in_progress", "rejected"},
    "in_progress": {"completed", "rejected"},
    "rejected": set(),  # терминальный статус
    "completed": set(),  # терминальный статус
}


def can_transition(current: str, new: str) -> bool:
    return new in ALLOWED_TRANSITIONS.get(current, set())
