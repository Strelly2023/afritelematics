"""Cross-region trace synchronization."""

from __future__ import annotations

from typing import Any, Mapping

from afritech.runtime.entropy.normalizer import normalize
from afritech.runtime.multiregion.region_model import RegionExecution


def merge_region_traces(
    regions: tuple[RegionExecution, ...],
) -> tuple[Mapping[str, Any], ...]:
    by_canonical_id: dict[str, Mapping[str, Any]] = {}
    for region in regions:
        for event in (*region.visible_events, *region.recovery_events):
            normalized = normalize(event)
            by_canonical_id[normalized.canonical_id] = event
    return tuple(
        by_canonical_id[key]
        for key in sorted(
            by_canonical_id,
            key=lambda item: (
                normalize(by_canonical_id[item]).sequence,
                item,
            ),
        )
    )

