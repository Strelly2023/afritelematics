"""Gap detection for incomplete replay traces."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent, normalize


@dataclass(frozen=True)
class ContinuityGap:
    gap_type: str
    start_sequence: int
    end_sequence: int
    reason: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "end_sequence": self.end_sequence,
            "gap_type": self.gap_type,
            "reason": self.reason,
            "start_sequence": self.start_sequence,
        }


def detect_gaps(
    trace: Iterable[Mapping[str, Any] | NormalizedEntropyEvent],
    *,
    expected_sequence_end: int | None = None,
) -> tuple[ContinuityGap, ...]:
    events = _normalized(trace)
    if not events:
        if expected_sequence_end is None:
            return ()
        return (
            ContinuityGap(
                gap_type="missing_segment",
                start_sequence=0,
                end_sequence=expected_sequence_end,
                reason="trace_empty",
            ),
        )

    by_sequence: dict[int, list[NormalizedEntropyEvent]] = {}
    for event in events:
        by_sequence.setdefault(event.sequence, []).append(event)

    upper = expected_sequence_end
    if upper is None:
        upper = max(by_sequence)

    gaps: list[ContinuityGap] = []
    lower = min(0, min(by_sequence))
    missing_start: int | None = None
    for sequence in range(lower, upper + 1):
        if sequence not in by_sequence and missing_start is None:
            missing_start = sequence
        elif sequence in by_sequence and missing_start is not None:
            gaps.append(
                ContinuityGap(
                    gap_type="missing_events",
                    start_sequence=missing_start,
                    end_sequence=sequence - 1,
                    reason="sequence_not_present",
                )
            )
            missing_start = None
    if missing_start is not None:
        gaps.append(
            ContinuityGap(
                gap_type="missing_segment",
                start_sequence=missing_start,
                end_sequence=upper,
                reason="tail_sequence_not_present",
            )
        )

    for event in sorted(events, key=lambda item: (item.sequence, item.canonical_id)):
        expected_previous = getattr(event, "previous_event_hash", None)
        if expected_previous is None:
            expected_previous = ""
        if not isinstance(expected_previous, str) or not expected_previous:
            continue
        previous = by_sequence.get(event.sequence - 1, ())
        actual_hashes = {item.canonical_event_hash for item in previous}
        if expected_previous not in actual_hashes:
            gaps.append(
                ContinuityGap(
                    gap_type="broken_chain",
                    start_sequence=event.sequence - 1,
                    end_sequence=event.sequence,
                    reason="previous_event_hash_not_observed",
                )
            )

    return tuple(gaps)


def gap_hash(gaps: Iterable[ContinuityGap]) -> str:
    return _canonical_hash([gap.canonical_dict() for gap in gaps])


def _normalized(
    trace: Iterable[Mapping[str, Any] | NormalizedEntropyEvent],
) -> tuple[NormalizedEntropyEvent, ...]:
    events: list[NormalizedEntropyEvent] = []
    for item in trace:
        if isinstance(item, NormalizedEntropyEvent):
            events.append(item)
        else:
            events.append(normalize(item))
    return tuple(events)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

