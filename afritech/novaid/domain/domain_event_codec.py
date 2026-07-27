from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from .domain_events import (
    NovaIDDomainEvent,
    domain_event_subject_ids,
)


DOMAIN_EVENT_SCHEMA_VERSION = 1


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, tuple):
        return [_json_value(item) for item in value]

    if isinstance(value, list):
        return [_json_value(item) for item in value]

    if isinstance(value, Mapping):
        return {
            str(key): _json_value(item)
            for key, item in value.items()
        }

    return value


def encode_domain_event(
    event: NovaIDDomainEvent,
) -> dict[str, Any]:
    if not is_dataclass(event):
        raise TypeError("DOMAIN_EVENT_DATACLASS_REQUIRED")

    payload = _json_value(asdict(event))

    return {
        "schema_version": DOMAIN_EVENT_SCHEMA_VERSION,
        "event_id": event.event_id,
        "event_type": event.event_type,
        "tenant_id": event.tenant_id,
        "subject_identity_ids": list(
            domain_event_subject_ids(event)
        ),
        "actor_identity_id": event.actor_identity_id,
        "correlation_id": event.correlation_id,
        "request_id": event.request_id,
        "occurred_at": event.occurred_at.isoformat(),
        "payload": payload,
    }
