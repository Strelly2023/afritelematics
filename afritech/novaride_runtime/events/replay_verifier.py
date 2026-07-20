"""Deterministic replay verification."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.events.replay import rebuild_projection, verify_event_hash
from afritech.novaride_runtime.events.schema_registry import (
    EventSchemaRegistry,
    default_event_schema_registry,
)


@dataclass(frozen=True, slots=True)
class ReplayVerificationResult:
    replay_id: str
    source_state_hash: str
    replay_state_hash: str
    source_event_count: int
    replay_event_count: int
    first_event_id: str | None
    last_event_id: str | None
    aggregate_version: int
    matched: bool
    divergence_fields: tuple[str, ...]
    unsupported_events: tuple[str, ...]
    quarantined_events: tuple[str, ...]
    side_effects_blocked: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "replay_id": self.replay_id,
            "source_state_hash": self.source_state_hash,
            "replay_state_hash": self.replay_state_hash,
            "source_event_count": self.source_event_count,
            "replay_event_count": self.replay_event_count,
            "first_event_id": self.first_event_id,
            "last_event_id": self.last_event_id,
            "aggregate_version": self.aggregate_version,
            "matched": self.matched,
            "divergence_fields": list(self.divergence_fields),
            "unsupported_events": list(self.unsupported_events),
            "quarantined_events": list(self.quarantined_events),
            "side_effects_blocked": self.side_effects_blocked,
        }


def verify_replay(
    *,
    replay_id: str,
    events: list[MobilityEvent],
    registry: EventSchemaRegistry | None = None,
) -> ReplayVerificationResult:
    schema_registry = registry or default_event_schema_registry()
    unsupported: list[str] = []
    quarantined: list[str] = []
    for event in events:
        if not verify_event_hash(event):
            quarantined.append(event.event_id)
            continue
        valid, missing = schema_registry.validate_payload(
            event.event_type, event.schema_version, event.payload
        )
        if not valid:
            unsupported.append(f"{event.event_id}:{','.join(missing)}")
    source = rebuild_projection(
        [event for event in events if event.event_id not in quarantined], projection_name="source"
    )
    shadow = rebuild_projection(
        [event for event in events if event.event_id not in quarantined], projection_name="shadow"
    )
    matched = source.state_hash == shadow.state_hash and not unsupported and not quarantined
    return ReplayVerificationResult(
        replay_id=replay_id,
        source_state_hash=source.state_hash,
        replay_state_hash=shadow.state_hash,
        source_event_count=source.event_count,
        replay_event_count=shadow.event_count,
        first_event_id=source.first_event_id,
        last_event_id=source.last_event_id,
        aggregate_version=max((event.aggregate_version for event in events), default=0),
        matched=matched,
        divergence_fields=() if matched else ("schema_or_hash",),
        unsupported_events=tuple(unsupported),
        quarantined_events=tuple(quarantined),
    )
