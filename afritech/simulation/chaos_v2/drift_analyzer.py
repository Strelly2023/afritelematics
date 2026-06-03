"""Drift analysis for repeated chaos cycles."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class DriftAnalysis:
    replay_drift: bool
    identity_drift: bool
    admissibility_drift: bool
    convergence_drift: bool
    baseline_hashes: Mapping[str, str]
    current_hashes: Mapping[str, str]

    @property
    def drift_detected(self) -> bool:
        return (
            self.replay_drift
            or self.identity_drift
            or self.admissibility_drift
            or self.convergence_drift
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "admissibility_drift": self.admissibility_drift,
            "baseline_hashes": dict(self.baseline_hashes),
            "convergence_drift": self.convergence_drift,
            "current_hashes": dict(self.current_hashes),
            "drift_detected": self.drift_detected,
            "identity_drift": self.identity_drift,
            "replay_drift": self.replay_drift,
        }

    def analysis_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def detect_drift(
    baseline: Mapping[str, str],
    current: Mapping[str, str],
) -> DriftAnalysis:
    return DriftAnalysis(
        admissibility_drift=baseline["admissibility_hash"]
        != current["admissibility_hash"],
        baseline_hashes=baseline,
        convergence_drift=baseline["convergence_hash"] != current["convergence_hash"],
        current_hashes=current,
        identity_drift=baseline["identity_resolution_hash"]
        != current["identity_resolution_hash"],
        replay_drift=baseline["replay_hash"] != current["replay_hash"],
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

