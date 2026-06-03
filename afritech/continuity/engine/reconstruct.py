"""Deterministic continuity reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.continuity.engine.gap_detector import ContinuityGap, detect_gaps
from afritech.continuity.engine.integrity_guard import IntegrityFinding, guard_trace
from afritech.continuity.engine.partial_replay import PartialReplayResult, partial_replay
from afritech.continuity.engine.recovery_planner import RecoveryPlan, plan_recovery
from afritech.runtime.entropy.convergence import ConvergenceResult, converge
from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent


@dataclass(frozen=True)
class ReconstructionResult:
    status: str
    plan: RecoveryPlan
    gaps: tuple[ContinuityGap, ...]
    findings: tuple[IntegrityFinding, ...]
    accepted_events: tuple[NormalizedEntropyEvent, ...]
    partial: PartialReplayResult
    convergence: ConvergenceResult

    @property
    def complete(self) -> bool:
        return self.status == "reconstructable"

    def canonical_dict(self) -> dict[str, object]:
        return {
            "accepted_events": [
                event.canonical_dict() for event in self.accepted_events
            ],
            "complete": self.complete,
            "convergence": self.convergence.canonical_dict(),
            "continuity_hash": self.continuity_hash,
            "findings": [finding.canonical_dict() for finding in self.findings],
            "gaps": [gap.canonical_dict() for gap in self.gaps],
            "partial": self.partial.canonical_dict(),
            "plan": self.plan.canonical_dict(),
            "status": self.status,
        }

    @property
    def continuity_hash(self) -> str:
        return _canonical_hash(
            {
                "accepted_events": [
                    event.canonical_event_hash for event in self.accepted_events
                ],
                "convergence_hash": self.convergence.convergence_hash,
                "gaps": [gap.canonical_dict() for gap in self.gaps],
                "status": self.status,
            }
        )


def reconstruct_trace(
    partial_trace: Iterable[Mapping[str, Any]],
    *,
    recovery_trace: Iterable[Mapping[str, Any]] = (),
    expected_sequence_end: int | None = None,
) -> ReconstructionResult:
    accepted, findings = guard_trace((*partial_trace, *recovery_trace))
    accepted = _dedupe(accepted)
    gaps = detect_gaps(accepted, expected_sequence_end=expected_sequence_end)
    plan = plan_recovery(gaps, findings)
    partial = partial_replay(accepted, expected_sequence_end=expected_sequence_end)

    if plan.strategy == "reconstructable":
        convergence = converge(event.canonical_dict() for event in accepted)
        status = "reconstructable"
    elif plan.strategy == "deferrable":
        convergence = partial.convergence
        status = "deferrable"
    else:
        convergence = partial.convergence
        status = "rejectable"

    return ReconstructionResult(
        accepted_events=accepted,
        convergence=convergence,
        findings=findings,
        gaps=gaps,
        partial=partial,
        plan=plan,
        status=status,
    )


def _dedupe(
    events: Iterable[NormalizedEntropyEvent],
) -> tuple[NormalizedEntropyEvent, ...]:
    by_id: dict[str, NormalizedEntropyEvent] = {}
    for event in events:
        by_id[event.canonical_id] = event
    return tuple(
        sorted(by_id.values(), key=lambda item: (item.sequence, item.canonical_id))
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
