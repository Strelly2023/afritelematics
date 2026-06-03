from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.code_executor.patch_model import Patch
from afritech.extensions.afriprog.constitutional_guard.guard_orchestrator import (
    GuardDecision,
    GuardOrchestrator,
)


@dataclass(frozen=True)
class ReviewResult:
    admitted: bool
    guard_decision: GuardDecision
    patch_count: int

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "patch_count": self.patch_count,
            "guard_decision": self.guard_decision.canonical_dict(),
        }


class Reviewer:
    """Review generated patch proposals through Afriprog guards."""

    def __init__(self, guards: GuardOrchestrator | None = None) -> None:
        self.guards = guards or GuardOrchestrator()

    def review(
        self,
        patches: tuple[Patch, ...],
        *,
        evidence_ids: tuple[str, ...],
        claims: tuple[str, ...] = (),
        actions: tuple[str, ...] = (),
    ) -> ReviewResult:
        payload = {
            "actions": (
                "generate_patch",
                "generate_tests",
                "run_validation",
                *actions,
            ),
            "claims": (
                "proposal-only generated engineering evidence",
                *claims,
            ),
            "evidence_ids": evidence_ids,
            "paths": tuple(patch.file_path for patch in patches),
        }
        decision = self.guards.evaluate_payload(payload)

        return ReviewResult(
            admitted=decision.admitted,
            guard_decision=decision,
            patch_count=len(patches),
        )
