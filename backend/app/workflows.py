"""Workflow статусов Internship:
sent -> accepted -> in_progress -> rejected|completed.
"rejected" и "cancelled" доступны из sent/accepted/in_progress.
"completed" достижим только после in_progress.
"""

from typing import Dict, Set

ALL_STATUSES = {"sent", "accepted", "in_progress", "rejected", "completed", "cancelled"}

ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "sent": {"accepted", "rejected", "cancelled"},
    "accepted": {"in_progress", "rejected"},
    "in_progress": {"completed", "rejected"},
    "rejected": set(),
    "completed": set(),
    "cancelled": set(),
}


def can_transition(current: str, new: str) -> bool:
    return new in ALLOWED_TRANSITIONS.get(current, set())