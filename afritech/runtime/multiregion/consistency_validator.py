"""Validate multi-region convergence invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from afritech.runtime.multiregion.convergence_engine import GlobalConvergenceResult


@dataclass(frozen=True)
class MultiRegionConsistency:
    truth_unique: bool
    identity_consistent: bool
    admissibility_consistent: bool
    convergence_consistent: bool
    partition_safe: bool

    @property
    def verified(self) -> bool:
        return (
            self.truth_unique
            and self.identity_consistent
            and self.admissibility_consistent
            and self.convergence_consistent
            and self.partition_safe
        )

    @property
    def consistency_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload = {
            "admissibility_consistent": self.admissibility_consistent,
            "convergence_consistent": self.convergence_consistent,
            "identity_consistent": self.identity_consistent,
            "partition_safe": self.partition_safe,
            "truth_unique": self.truth_unique,
            "verified": self.verified,
        }
        if include_hash:
            payload["consistency_hash"] = self.consistency_hash
        return payload


def validate_consistency(
    result: GlobalConvergenceResult,
) -> MultiRegionConsistency:
    baseline = result.baseline
    global_result = result.global_result
    return MultiRegionConsistency(
        admissibility_consistent=baseline.admissibility_hash
        == global_result.admissibility_hash,
        convergence_consistent=baseline.convergence_hash
        == global_result.convergence_hash,
        identity_consistent=baseline.identity_resolution_hash
        == global_result.identity_resolution_hash,
        partition_safe=all(
            region.local_result.status in {"deferrable", "reconstructable"}
            for region in result.regions
        ),
        truth_unique=baseline.replay_hash == global_result.replay_hash,
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

