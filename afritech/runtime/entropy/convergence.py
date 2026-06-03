"""Deterministic convergence for entropy-bound execution paths."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.runtime.entropy.admissibility import check_admissibility
from afritech.runtime.entropy.classifier import DisturbanceType, classify
from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent, normalize
from afritech.runtime.entropy.recorder import EntropyRecord, record


@dataclass(frozen=True)
class ConvergenceResult:
    records: tuple[EntropyRecord, ...]
    accepted_events: tuple[NormalizedEntropyEvent, ...]
    final_state: Mapping[str, Any]
    replay_hash: str
    identity_resolution_hash: str
    admissibility_hash: str
    convergence_hash: str

    @property
    def verified(self) -> bool:
        return all(
            len(value) == 64
            for value in (
                self.replay_hash,
                self.identity_resolution_hash,
                self.admissibility_hash,
                self.convergence_hash,
            )
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "accepted_events": [
                event.canonical_dict() for event in self.accepted_events
            ],
            "admissibility_hash": self.admissibility_hash,
            "classification_counts": _classification_counts(self.records),
            "convergence_hash": self.convergence_hash,
            "final_state": self.final_state,
            "identity_resolution_hash": self.identity_resolution_hash,
            "record_hashes": [item.replay_hash for item in self.records],
            "replay_hash": self.replay_hash,
            "verified": self.verified,
        }


def converge(raw_events: Iterable[Mapping[str, Any]]) -> ConvergenceResult:
    normalized: list[NormalizedEntropyEvent] = []
    records: list[EntropyRecord] = []
    for raw_event in raw_events:
        event = normalize(raw_event)
        classification = classify(event, prior_events=normalized)
        decision = check_admissibility(event)
        records.append(record(event, classification, decision))
        normalized.append(event)

    accepted_index: dict[str, NormalizedEntropyEvent] = {}
    for item in records:
        if not item.admissibility.admitted:
            continue
        if item.classification == DisturbanceType.DUPLICATE:
            continue
        accepted_index[item.event.canonical_id] = item.event

    accepted = tuple(
        sorted(
            accepted_index.values(),
            key=lambda event: (event.sequence, event.canonical_id),
        )
    )
    final_state = _final_state(accepted)
    replay_hash = _canonical_hash(
        [
            {
                "canonical_event_hash": event.canonical_event_hash,
                "event_id": event.event_id,
                "identity_id": event.identity_id,
                "payload": event.payload,
                "sequence": event.sequence,
            }
            for event in accepted
        ]
    )
    identity_resolution_hash = _canonical_hash(
        [(event.event_id, event.identity_id) for event in accepted]
    )
    admissibility_hash = _canonical_hash(
        [
            {
                "canonical_id": event.canonical_id,
                "admitted": True,
                "reason": "admissible",
            }
            for event in accepted
        ]
    )
    convergence_hash = _canonical_hash(
        {
            "final_state": final_state,
            "identity_resolution_hash": identity_resolution_hash,
            "replay_hash": replay_hash,
        }
    )
    return ConvergenceResult(
        accepted_events=accepted,
        admissibility_hash=admissibility_hash,
        convergence_hash=convergence_hash,
        final_state=final_state,
        identity_resolution_hash=identity_resolution_hash,
        records=tuple(records),
        replay_hash=replay_hash,
    )


def _final_state(events: tuple[NormalizedEntropyEvent, ...]) -> dict[str, object]:
    return {
        "accepted_event_count": len(events),
        "accepted_event_ids": [event.event_id for event in events],
        "identity_ids": sorted({event.identity_id for event in events}),
        "last_sequence": events[-1].sequence if events else None,
        "state_hash": _canonical_hash(
            [(event.event_id, event.identity_id, event.sequence) for event in events]
        ),
    }


def _classification_counts(records: tuple[EntropyRecord, ...]) -> dict[str, int]:
    counts = {kind.value: 0 for kind in DisturbanceType}
    for item in records:
        counts[item.classification.value] += 1
    return counts


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
