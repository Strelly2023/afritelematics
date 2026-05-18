from __future__ import annotations

import hashlib
import json
from typing import Iterable, Mapping

from afritech.simulation.adversarial.models import AdversarialEvent, JSONValue


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def event_sort_key(event: AdversarialEvent) -> tuple[int, str, int, str, str]:
    return (
        event.epoch,
        event.object_id,
        event.causal_index,
        event.node_id,
        event.event_id,
    )


def canonical_event_order(
    events: Iterable[AdversarialEvent],
) -> tuple[AdversarialEvent, ...]:
    return tuple(sorted(events, key=event_sort_key))


def apply_events(
    events: Iterable[AdversarialEvent],
) -> dict[str, dict[str, JSONValue]]:
    state: dict[str, dict[str, JSONValue]] = {}

    for event in canonical_event_order(events):
        current = dict(state.get(event.object_id, {}))
        for key, value in sorted(event.mutation.items()):
            current[key] = value
        current["_last_event"] = event.event_id
        current["_last_node"] = event.node_id
        state[event.object_id] = current

    return state


def state_hash_for(
    events: Iterable[AdversarialEvent],
) -> str:
    return canonical_hash(apply_events(events))


def reject_invalid_lineage(
    events: Iterable[AdversarialEvent],
    valid_lineage_hashes: set[str],
) -> tuple[AdversarialEvent, ...]:
    admitted = []

    for event in canonical_event_order(events):
        if not event.lineage:
            admitted.append(event)
            continue

        if all(item in valid_lineage_hashes for item in event.lineage):
            admitted.append(event)

    return tuple(admitted)


def canonical_merge(
    node_states: Mapping[str, Iterable[AdversarialEvent]],
) -> tuple[AdversarialEvent, ...]:
    merged: dict[str, AdversarialEvent] = {}

    for node_id in sorted(node_states):
        for event in node_states[node_id]:
            existing = merged.get(event.event_id)
            if existing is None or event_sort_key(event) < event_sort_key(existing):
                merged[event.event_id] = event

    return canonical_event_order(merged.values())
