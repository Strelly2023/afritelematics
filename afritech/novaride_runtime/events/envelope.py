"""Immutable event envelope."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.identifiers import new_id
from afritech.novaride_runtime.events.hashing import canonical_hash


@dataclass(frozen=True, slots=True)
class MobilityEvent:
    event_type: str
    aggregate_id: str
    aggregate_type: str
    aggregate_version: int
    tenant_id: str
    region: str
    actor_type: str
    actor_id: str
    correlation_id: str
    causation_id: str | None
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: new_id("evt"))
    occurred_at: datetime = field(default_factory=utc_now)
    schema_version: str = "2026.2"
    integrity_hash: str = ""

    def __post_init__(self) -> None:
        if not self.integrity_hash:
            object.__setattr__(
                self,
                "integrity_hash",
                canonical_hash(
                    {
                        "event_type": self.event_type,
                        "aggregate_id": self.aggregate_id,
                        "aggregate_type": self.aggregate_type,
                        "aggregate_version": self.aggregate_version,
                        "tenant_id": self.tenant_id,
                        "region": self.region,
                        "actor_type": self.actor_type,
                        "actor_id": self.actor_id,
                        "correlation_id": self.correlation_id,
                        "causation_id": self.causation_id,
                        "schema_version": self.schema_version,
                        "payload": self.payload,
                    }
                ),
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "aggregate_version": self.aggregate_version,
            "occurred_at": self.occurred_at.isoformat(),
            "tenant_id": self.tenant_id,
            "region": self.region,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "schema_version": self.schema_version,
            "payload": self.payload,
            "integrity_hash": self.integrity_hash,
        }
