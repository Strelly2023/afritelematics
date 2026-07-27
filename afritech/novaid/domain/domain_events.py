from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class NovaIDDomainEvent(Protocol):
    event_id: str
    event_type: str
    tenant_id: str
    actor_identity_id: str
    correlation_id: str
    request_id: str
    occurred_at: datetime
    metadata: Mapping[str, Any]


def domain_event_subject_ids(
    event: NovaIDDomainEvent,
) -> tuple[str, ...]:
    identity_id = getattr(event, "identity_id", None)

    if identity_id:
        return (str(identity_id),)

    source_id = getattr(event, "source_identity_id", None)
    target_id = getattr(event, "target_identity_id", None)

    values = tuple(
        str(value)
        for value in (source_id, target_id)
        if value
    )

    if not values:
        raise ValueError("DOMAIN_EVENT_SUBJECT_REQUIRED")

    return values
