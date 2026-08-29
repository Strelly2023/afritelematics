"""Transaction-bound PostgreSQL EventFabric for NovaRide.

This bridge preserves the canonical EventFabric.emit() contract while using
repositories that are already bound to an open PostgresRuntimeSession.

It deliberately does not:
- open a UnitOfWork;
- set tenant context;
- commit;
- roll back;
- close the connection;
- perform settings-driven runtime selection.

The outer PostgresRuntimeSession owns transaction lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.novaride_runtime.events.envelope import (
    MobilityEvent,
)
from afritech.novaride_runtime.persistence.memory import (
    RuntimeRepositories,
)
from afritech.novaride_runtime.persistence.postgres.runtime_repositories import (
    PostgresRuntimeSupportRepositories,
)
from afritech.novaride_runtime.services import (
    RuntimeContext,
    _json,
)


@dataclass(slots=True)
class PostgresEventFabric:
    """Persist one event and one publication intent in the caller transaction."""

    repositories: RuntimeRepositories
    support: PostgresRuntimeSupportRepositories

    def emit(
        self,
        context: RuntimeContext,
        *,
        event_type: str,
        aggregate_id: str,
        aggregate_type: str,
        aggregate_version: int,
        payload: dict[str, Any],
        causation_id: str | None = None,
    ) -> MobilityEvent:
        event = MobilityEvent(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            aggregate_version=aggregate_version,
            tenant_id=context.tenant_id,
            region=context.region_code,
            actor_type=context.actor_type.value,
            actor_id=context.actor_id,
            correlation_id=context.correlation_id,
            causation_id=causation_id,
            payload=_json(payload),
        )

        self.repositories.events.append(
            event
        )

        self.support.event_outbox.append(
            event
        )

        return event


__all__ = [
    "PostgresEventFabric",
]
