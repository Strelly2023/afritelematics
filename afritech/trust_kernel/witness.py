from __future__ import annotations

from afritech.models import EventRecord, WitnessSignature
from afritech.trust_kernel.policy import HIGH_VALUE_EVENT_WITNESS_REQUIREMENTS


def required_witness_count(event_type: str) -> int:
    return HIGH_VALUE_EVENT_WITNESS_REQUIREMENTS.get(event_type, 0)


def valid_witnesses(event: EventRecord) -> list[WitnessSignature]:
    return list(WitnessSignature.objects.filter(event=event).order_by("created_at", "id"))


def guard_witness_consensus(event: EventRecord) -> None:
    required = required_witness_count(event.event_type)
    witnesses = valid_witnesses(event)
    if len(witnesses) < required:
        raise ValueError(f"{event.event_type} requires at least {required} witnesses")
