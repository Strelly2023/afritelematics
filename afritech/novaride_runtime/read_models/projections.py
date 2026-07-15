"""Durable projection contracts for NovaRide runtime."""

from __future__ import annotations

from dataclasses import dataclass, field

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.events.replay import rebuild_projection


@dataclass(slots=True)
class ProjectionRecord:
    projection_name: str
    tenant_id: str
    region: str
    schema_version: str = "2026.2"
    checkpoint: int = 0
    last_event_id: str | None = None
    last_event_timestamp: str | None = None
    state_hash: str | None = None
    rebuild_status: str = "EMPTY"
    lag_seconds: float = 0.0


@dataclass(slots=True)
class ProjectionStore:
    records: dict[tuple[str, str, str], ProjectionRecord] = field(default_factory=dict)

    def rebuild(self, projection_name: str, tenant_id: str, region: str, events: list[MobilityEvent]) -> ProjectionRecord:
        selected = [event for event in events if event.tenant_id == tenant_id and event.region == region]
        state = rebuild_projection(selected, projection_name=projection_name)
        record = ProjectionRecord(
            projection_name=projection_name,
            tenant_id=tenant_id,
            region=region,
            checkpoint=len(selected),
            last_event_id=state.last_event_id,
            last_event_timestamp=selected[-1].occurred_at.isoformat() if selected else None,
            state_hash=state.state_hash,
            rebuild_status="COMPLETE",
            lag_seconds=0.0 if not selected else max(0.0, (utc_now() - selected[-1].occurred_at).total_seconds()),
        )
        self.records[(projection_name, tenant_id, region)] = record
        return record

    def shadow_rebuild(self, projection_name: str, tenant_id: str, region: str, events: list[MobilityEvent]) -> ProjectionRecord:
        return self.rebuild(f"shadow:{projection_name}", tenant_id, region, events)
