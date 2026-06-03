"""Integrity guard for continuity reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from afritech.runtime.entropy.admissibility import check_admissibility
from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent, normalize


@dataclass(frozen=True)
class IntegrityFinding:
    sequence: int
    event_id: str
    admitted: bool
    reason: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "admitted": self.admitted,
            "event_id": self.event_id,
            "reason": self.reason,
            "sequence": self.sequence,
        }


def guard_trace(
    trace: Iterable[Mapping[str, Any] | NormalizedEntropyEvent],
) -> tuple[tuple[NormalizedEntropyEvent, ...], tuple[IntegrityFinding, ...]]:
    accepted: list[NormalizedEntropyEvent] = []
    findings: list[IntegrityFinding] = []
    for raw in trace:
        event = raw if isinstance(raw, NormalizedEntropyEvent) else normalize(raw)
        decision = check_admissibility(event)
        finding = IntegrityFinding(
            admitted=decision.admitted,
            event_id=event.event_id,
            reason=decision.reason,
            sequence=event.sequence,
        )
        findings.append(finding)
        if decision.admitted:
            accepted.append(event)
    return tuple(accepted), tuple(findings)

