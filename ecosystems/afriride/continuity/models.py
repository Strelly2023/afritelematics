from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class AfriRideContinuityResult:
    scenario_id: str
    accepted: bool
    reason: str
    receipt_hash: str
    targets: tuple[str, ...]
    metrics: Mapping[str, bool]

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "accepted": self.accepted,
            "reason": self.reason,
            "receipt_hash": self.receipt_hash,
            "targets": list(self.targets),
            "metrics": dict(self.metrics),
        }
