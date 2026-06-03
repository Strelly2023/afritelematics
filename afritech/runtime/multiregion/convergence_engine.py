"""Global multi-region convergence."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from afritech.runtime.entropy.convergence import ConvergenceResult, converge
from afritech.runtime.multiregion.cross_region_sync import merge_region_traces
from afritech.runtime.multiregion.region_model import RegionExecution


@dataclass(frozen=True)
class GlobalConvergenceResult:
    baseline: ConvergenceResult
    regions: tuple[RegionExecution, ...]
    merged_trace: tuple[Mapping[str, Any], ...]
    global_result: ConvergenceResult

    @property
    def equivalent(self) -> bool:
        return (
            self.baseline.replay_hash == self.global_result.replay_hash
            and self.baseline.identity_resolution_hash
            == self.global_result.identity_resolution_hash
            and self.baseline.admissibility_hash == self.global_result.admissibility_hash
            and self.baseline.convergence_hash == self.global_result.convergence_hash
        )

    @property
    def convergence_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload = {
            "baseline": self.baseline.canonical_dict(),
            "equivalent": self.equivalent,
            "global_result": self.global_result.canonical_dict(),
            "merged_trace": [_canonicalize(event) for event in self.merged_trace],
            "regions": [region.canonical_dict() for region in self.regions],
        }
        if include_hash:
            payload["convergence_hash"] = self.convergence_hash
        return payload


def converge_regions(
    baseline_trace: tuple[Mapping[str, Any], ...],
    regions: tuple[RegionExecution, ...],
) -> GlobalConvergenceResult:
    merged = merge_region_traces(regions)
    return GlobalConvergenceResult(
        baseline=converge(baseline_trace),
        global_result=converge(merged),
        merged_trace=merged,
        regions=regions,
    )


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

