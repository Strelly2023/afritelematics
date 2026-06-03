"""Partial replay that halts at the first continuity boundary."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.continuity.engine.gap_detector import ContinuityGap, detect_gaps
from afritech.runtime.entropy.convergence import ConvergenceResult, converge
from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent


@dataclass(frozen=True)
class PartialReplayResult:
    replayed_events: tuple[NormalizedEntropyEvent, ...]
    gaps: tuple[ContinuityGap, ...]
    boundary_sequence: int | None
    convergence: ConvergenceResult

    @property
    def halted_at_gap(self) -> bool:
        return self.boundary_sequence is not None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "boundary_sequence": self.boundary_sequence,
            "convergence": self.convergence.canonical_dict(),
            "gaps": [gap.canonical_dict() for gap in self.gaps],
            "halted_at_gap": self.halted_at_gap,
            "replay_hash": self.replay_hash,
            "replayed_events": [
                event.canonical_dict() for event in self.replayed_events
            ],
        }

    @property
    def replay_hash(self) -> str:
        return _canonical_hash(
            [event.canonical_dict() for event in self.replayed_events]
        )


def partial_replay(
    trace: Iterable[Mapping[str, Any] | NormalizedEntropyEvent],
    *,
    expected_sequence_end: int | None = None,
) -> PartialReplayResult:
    from afritech.continuity.engine.integrity_guard import guard_trace

    events, _ = guard_trace(trace)
    events = tuple(sorted(events, key=lambda item: (item.sequence, item.canonical_id)))
    gaps = detect_gaps(events, expected_sequence_end=expected_sequence_end)
    missing = [
        gap for gap in gaps if gap.gap_type in {"missing_events", "missing_segment"}
    ]
    boundary = min((gap.start_sequence for gap in missing), default=None)
    replayed = (
        tuple(event for event in events if event.sequence < boundary)
        if boundary is not None
        else events
    )
    convergence = converge(event.canonical_dict() for event in replayed)
    return PartialReplayResult(
        boundary_sequence=boundary,
        convergence=convergence,
        gaps=gaps,
        replayed_events=replayed,
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
