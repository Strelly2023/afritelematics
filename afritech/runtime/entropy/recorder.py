"""Replay-safe entropy evidence recording."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.runtime.entropy.admissibility import AdmissibilityDecision
from afritech.runtime.entropy.classifier import DisturbanceType
from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent


@dataclass(frozen=True)
class EntropyRecord:
    event: NormalizedEntropyEvent
    classification: DisturbanceType
    admissibility: AdmissibilityDecision

    @property
    def replay_hash(self) -> str:
        return _canonical_hash(
            {
                "admissibility": self.admissibility.canonical_dict(),
                "canonical_event_hash": self.event.canonical_event_hash,
                "classification": self.classification.value,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "admissibility": self.admissibility.canonical_dict(),
            "classification": self.classification.value,
            "event": self.event.canonical_dict(),
            "replay_hash": self.replay_hash,
        }


def record(
    event: NormalizedEntropyEvent,
    classification: DisturbanceType,
    decision: AdmissibilityDecision,
) -> EntropyRecord:
    return EntropyRecord(
        admissibility=decision,
        classification=classification,
        event=event,
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
