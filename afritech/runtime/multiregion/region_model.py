"""Region-local execution model."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.continuity.engine.reconstruct import ReconstructionResult, reconstruct_trace


REGIONS = ("region_A", "region_B", "region_C")


@dataclass(frozen=True)
class RegionView:
    region_id: str
    events: tuple[Mapping[str, Any], ...]
    recovery_events: tuple[Mapping[str, Any], ...] = ()

    def canonical_dict(self) -> dict[str, object]:
        return {
            "events": [_canonicalize(event) for event in self.events],
            "recovery_events": [
                _canonicalize(event) for event in self.recovery_events
            ],
            "region_id": self.region_id,
        }


@dataclass(frozen=True)
class RegionExecution:
    region_id: str
    local_result: ReconstructionResult
    visible_events: tuple[Mapping[str, Any], ...]
    recovery_events: tuple[Mapping[str, Any], ...]

    @property
    def region_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload = {
            "local_result": self.local_result.canonical_dict(),
            "recovery_events": [
                _canonicalize(event) for event in self.recovery_events
            ],
            "region_id": self.region_id,
            "visible_events": [_canonicalize(event) for event in self.visible_events],
        }
        if include_hash:
            payload["region_hash"] = self.region_hash
        return payload


def execute_region(
    view: RegionView,
    *,
    expected_sequence_end: int,
) -> RegionExecution:
    result = reconstruct_trace(
        view.events,
        recovery_trace=view.recovery_events,
        expected_sequence_end=expected_sequence_end,
    )
    return RegionExecution(
        local_result=result,
        recovery_events=view.recovery_events,
        region_id=view.region_id,
        visible_events=view.events,
    )


def execute_regions(
    views: Iterable[RegionView],
    *,
    expected_sequence_end: int,
) -> tuple[RegionExecution, ...]:
    return tuple(
        execute_region(view, expected_sequence_end=expected_sequence_end)
        for view in sorted(views, key=lambda item: item.region_id)
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

