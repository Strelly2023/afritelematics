"""Deterministic, allow-listed NovaLogistics persistence codecs."""

from __future__ import annotations

import json
from typing import Any, Mapping

from . import domain
from .domain import DomainEvent, Entity, Identifier, LifecycleAggregate
from .persistence import SerializationError, UnsupportedSchemaVersionError


PERSISTENCE_SCHEMA = "afritech.novalogistics.persistence.v1"


_ALLOWED_TYPES = {
    name: value
    for name in domain.__all__
    if isinstance((value := getattr(domain, name, None)), type)
    and issubclass(value, (Entity, LifecycleAggregate))
    and value not in {Entity, LifecycleAggregate}
}


def encode_aggregate(value: Entity | LifecycleAggregate) -> str:
    if type(value).__name__ not in _ALLOWED_TYPES:
        raise SerializationError(f"unsupported aggregate type: {type(value).__name__}")
    payload: dict[str, Any] = {
        "schema": PERSISTENCE_SCHEMA,
        "type": type(value).__name__,
        "id": str(value.id),
        "tenant_id": str(value.tenant_id),
    }
    if isinstance(value, LifecycleAggregate):
        payload.update(value.to_dict())
    else:
        payload["name"] = value.name
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def decode_aggregate(payload_json: str) -> Entity | LifecycleAggregate:
    try:
        payload = json.loads(payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise SerializationError("malformed aggregate JSON") from exc
    if not isinstance(payload, Mapping):
        raise SerializationError("aggregate payload must be an object")
    if payload.get("schema") != PERSISTENCE_SCHEMA:
        raise UnsupportedSchemaVersionError(str(payload.get("schema")))
    aggregate_type = _ALLOWED_TYPES.get(str(payload.get("type")))
    if aggregate_type is None:
        raise SerializationError("aggregate type is not allow-listed")
    try:
        if issubclass(aggregate_type, LifecycleAggregate):
            normalized = dict(payload)
            normalized["schema_version"] = normalized.pop("schema", domain.SCHEMA_VERSION)
            return aggregate_type.from_dict(normalized)
        return aggregate_type(
            id=Identifier(str(payload["id"])),
            tenant_id=Identifier(str(payload["tenant_id"])),
            name=str(payload["name"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise SerializationError("invalid aggregate payload") from exc


def encode_event(event: DomainEvent) -> str:
    return json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def decode_event(payload_json: str) -> DomainEvent:
    try:
        payload = json.loads(payload_json)
        return DomainEvent(
            event_type=payload["event_type"],
            aggregate_id=Identifier(payload["aggregate_id"]),
            tenant_id=Identifier(payload["tenant_id"]),
            occurred_at=domain.datetime.fromisoformat(payload["occurred_at"]),
            data=payload.get("data", {}),
            schema_version=payload.get("schema_version", domain.SCHEMA_VERSION),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SerializationError("invalid event payload") from exc
