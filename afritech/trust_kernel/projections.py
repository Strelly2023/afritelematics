from __future__ import annotations

from typing import Any

from afritech.models import EventRecord
from afritech.trust_kernel.replay.engine import apply_event, hash_state, _verify_event_hash


def replay_projection() -> dict[str, Any]:
    state: dict[str, Any] = {}
    for event in EventRecord.objects.order_by("created_at", "event_id"):
        _verify_event_hash(event)
        apply_event(state, event)
    return state


def projection_hash() -> str:
    return hash_state(replay_projection())


def get_subject_projection(subject_id: str) -> dict[str, Any] | None:
    subjects = replay_projection().get("subjects", {})
    if not isinstance(subjects, dict):
        return None
    subject = subjects.get(subject_id)
    if not isinstance(subject, dict):
        return None
    return subject
