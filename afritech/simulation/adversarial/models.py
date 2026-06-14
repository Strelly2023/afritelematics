from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Union


JSONScalar = Union[str, int, float, bool, None]
JSONValue = Union[JSONScalar, Sequence["JSONValue"], Mapping[str, "JSONValue"]]


@dataclass(frozen=True)
class AdversarialEvent:
    event_id: str
    object_id: str
    epoch: int
    node_id: str
    causal_index: int
    mutation: Mapping[str, JSONValue]
    lineage: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    accepted: bool
    reason: str
    state_hash: Optional[str]
    targets: tuple[str, ...]
    metrics: Mapping[str, bool]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "accepted": self.accepted,
            "reason": self.reason,
            "state_hash": self.state_hash,
            "targets": list(self.targets),
            "metrics": dict(self.metrics),
        }
