from __future__ import annotations

import hashlib
import json
from typing import Iterable, Mapping

from afritech.simulation.continuity.models import ContinuityEvent, JSONValue


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def event_sort_key(event: ContinuityEvent) -> tuple[int, str, int, str, str]:
    return (
        event.epoch,
        event.canonical_identity,
        event.causal_index,
        event.node_id,
        event.event_id,
    )


def canonical_event_order(
    events: Iterable[ContinuityEvent],
) -> tuple[ContinuityEvent, ...]:
    return tuple(sorted(events, key=event_sort_key))


def canonical_merge(
    node_events: Mapping[str, Iterable[ContinuityEvent]],
) -> tuple[ContinuityEvent, ...]:
    merged: dict[str, ContinuityEvent] = {}

    for node_id in sorted(node_events):
        for event in node_events[node_id]:
            existing = merged.get(event.event_id)
            if existing is None or event_sort_key(event) < event_sort_key(existing):
                merged[event.event_id] = event

    return canonical_event_order(merged.values())


def apply_events(
    events: Iterable[ContinuityEvent],
) -> dict[str, dict[str, JSONValue]]:
    state: dict[str, dict[str, JSONValue]] = {}

    for event in canonical_event_order(events):
        current = dict(state.get(event.canonical_identity, {}))
        for key, value in sorted(event.payload.items()):
            current[key] = value
        current["_last_event"] = event.event_id
        current["_last_node"] = event.node_id
        current["_operation"] = event.operation
        state[event.canonical_identity] = current

    return state


def state_hash_for(
    events: Iterable[ContinuityEvent],
) -> str:
    return canonical_hash(apply_events(events))


def transcript_hash_for(
    events: Iterable[ContinuityEvent],
) -> str:
    transcript = [
        {
            "event_id": event.event_id,
            "canonical_identity": event.canonical_identity,
            "epoch": event.epoch,
            "node_id": event.node_id,
            "causal_index": event.causal_index,
            "operation": event.operation,
            "payload": dict(event.payload),
            "lineage": list(event.lineage),
            "offline_admissible": event.offline_admissible,
        }
        for event in canonical_event_order(events)
    ]
    return canonical_hash(transcript)


def mutation_trace_hash_for(
    events: Iterable[ContinuityEvent],
) -> str:
    state: dict[str, dict[str, JSONValue]] = {}
    transitions: list[dict[str, object]] = []

    for event in canonical_event_order(events):
        before = canonical_hash(state.get(event.canonical_identity, {}))
        current = dict(state.get(event.canonical_identity, {}))
        for key, value in sorted(event.payload.items()):
            current[key] = value
        state[event.canonical_identity] = current
        transitions.append(
            {
                "identity": event.canonical_identity,
                "operation": event.operation,
                "before_state_hash": before,
                "after_state_hash": canonical_hash(current),
            }
        )

    return canonical_hash(transitions)


def continuity_hash_for(
    events: Iterable[ContinuityEvent],
) -> str:
    ordered = canonical_event_order(events)
    return canonical_hash(
        {
            "state_hash": state_hash_for(ordered),
            "transcript_hash": transcript_hash_for(ordered),
            "mutation_trace_hash": mutation_trace_hash_for(ordered),
        }
    )


def reject_invalid_lineage(
    events: Iterable[ContinuityEvent],
    valid_lineage_hashes: set[str],
) -> tuple[ContinuityEvent, ...]:
    admitted = []

    for event in canonical_event_order(events):
        if not event.lineage:
            admitted.append(event)
            continue

        if all(item in valid_lineage_hashes for item in event.lineage):
            admitted.append(event)

    return tuple(admitted)


def canonical_identity_for(
    identity: str,
    aliases: Mapping[str, str],
) -> str:
    return aliases.get(identity, identity)


def deterministic_coordinator(
    node_ids: Iterable[str],
) -> str:
    return sorted(node_ids)[0]
