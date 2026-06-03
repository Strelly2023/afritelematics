"""Recovery planning for incomplete continuity traces."""

from __future__ import annotations

from dataclasses import dataclass

from afritech.continuity.engine.gap_detector import ContinuityGap
from afritech.continuity.engine.integrity_guard import IntegrityFinding


@dataclass(frozen=True)
class RecoveryPlan:
    strategy: str
    reason: str
    gap_count: int
    isolated_event_count: int

    @property
    def reconstructable(self) -> bool:
        return self.strategy == "reconstructable"

    def canonical_dict(self) -> dict[str, object]:
        return {
            "gap_count": self.gap_count,
            "isolated_event_count": self.isolated_event_count,
            "reason": self.reason,
            "reconstructable": self.reconstructable,
            "strategy": self.strategy,
        }


def plan_recovery(
    gaps: tuple[ContinuityGap, ...],
    findings: tuple[IntegrityFinding, ...],
) -> RecoveryPlan:
    rejected = tuple(finding for finding in findings if not finding.admitted)
    if any(gap.gap_type == "broken_chain" for gap in gaps):
        return RecoveryPlan(
            gap_count=len(gaps),
            isolated_event_count=len(rejected),
            reason="chain_integrity_violation",
            strategy="rejectable",
        )
    if gaps:
        return RecoveryPlan(
            gap_count=len(gaps),
            isolated_event_count=len(rejected),
            reason="missing_history_requires_completion",
            strategy="deferrable",
        )
    return RecoveryPlan(
        gap_count=0,
        isolated_event_count=len(rejected),
        reason="all_required_sequences_observed",
        strategy="reconstructable",
    )

