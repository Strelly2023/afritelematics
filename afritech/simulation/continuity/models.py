from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | Sequence["JSONValue"] | Mapping[str, "JSONValue"]


@dataclass(frozen=True)
class ContinuityEvent:
    event_id: str
    canonical_identity: str
    epoch: int
    node_id: str
    causal_index: int
    operation: str
    payload: Mapping[str, JSONValue]
    lineage: tuple[str, ...] = ()
    offline_admissible: bool = False


@dataclass(frozen=True)
class ContinuityScenarioResult:
    scenario_id: str
    accepted: bool
    reason: str
    continuity_hash: str | None
    targets: tuple[str, ...]
    metrics: Mapping[str, bool]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "accepted": self.accepted,
            "reason": self.reason,
            "continuity_hash": self.continuity_hash,
            "targets": list(self.targets),
            "metrics": dict(self.metrics),
        }
