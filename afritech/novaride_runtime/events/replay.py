"""Event replay helpers and projection rebuild."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.events.hashing import canonical_hash


def replay_by_aggregate(events: list[MobilityEvent], aggregate_id: str) -> list[MobilityEvent]:
    return [event for event in events if event.aggregate_id == aggregate_id]


def replay_by_correlation(events: list[MobilityEvent], correlation_id: str) -> list[MobilityEvent]:
    return [event for event in events if event.correlation_id == correlation_id]


def replay_range(
    events: list[MobilityEvent], start: int = 0, end: int | None = None
) -> list[MobilityEvent]:
    return events[start:end]


def replay_by_tenant(events: list[MobilityEvent], tenant_id: str) -> list[MobilityEvent]:
    return [event for event in events if event.tenant_id == tenant_id]


def replay_by_region(events: list[MobilityEvent], region: str) -> list[MobilityEvent]:
    return [event for event in events if event.region == region]


def replay_by_event_type_range(
    events: list[MobilityEvent], event_types: set[str]
) -> list[MobilityEvent]:
    return [event for event in events if event.event_type in event_types]


@dataclass(frozen=True, slots=True)
class ProjectionState:
    projection_name: str
    state: dict[str, Any]
    event_count: int
    first_event_id: str | None
    last_event_id: str | None
    state_hash: str


def verify_event_hash(event: MobilityEvent) -> bool:
    expected = canonical_hash(
        {
            "event_type": event.event_type,
            "aggregate_id": event.aggregate_id,
            "aggregate_type": event.aggregate_type,
            "aggregate_version": event.aggregate_version,
            "tenant_id": event.tenant_id,
            "region": event.region,
            "actor_type": event.actor_type,
            "actor_id": event.actor_id,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
            "schema_version": event.schema_version,
            "payload": event.payload,
        }
    )
    return expected == event.integrity_hash


def canonical_state_hash(state: dict[str, Any], *, domain: str = "NOVARIDE_REPLAY_STATE_V1") -> str:
    return canonical_hash({"domain": domain, "state": state})


def rebuild_projection(
    events: list[MobilityEvent], *, projection_name: str = "shadow"
) -> ProjectionState:
    ordered = sorted(events, key=lambda event: (event.occurred_at, event.event_id))
    state: dict[str, Any] = {}
    for event in ordered:
        aggregate = state.setdefault(
            event.aggregate_id,
            {
                "aggregate_id": event.aggregate_id,
                "aggregate_type": event.aggregate_type,
                "tenant_id": event.tenant_id,
                "region": event.region,
                "events": [],
                "aggregate_version": 0,
            },
        )
        aggregate["aggregate_version"] = max(
            int(aggregate["aggregate_version"]), int(event.aggregate_version)
        )
        aggregate["events"].append(event.event_type)
        aggregate["last_event_id"] = event.event_id
    return ProjectionState(
        projection_name=projection_name,
        state=state,
        event_count=len(ordered),
        first_event_id=ordered[0].event_id if ordered else None,
        last_event_id=ordered[-1].event_id if ordered else None,
        state_hash=canonical_state_hash(state),
    )
