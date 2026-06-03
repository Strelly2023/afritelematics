from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.extensions.afriprog.constitutional_guard.authority_guard import (
    AuthorityDecision,
    AuthorityGuard,
)
from afritech.extensions.afriprog.constitutional_guard.claim_guard import (
    ClaimDecision,
    ClaimGuard,
)
from afritech.extensions.afriprog.constitutional_guard.replay_guard import (
    ReplayDecision,
    ReplayGuard,
)
from afritech.extensions.afriprog.constitutional_guard.surface_guard import (
    SurfaceDecision,
    SurfaceGuard,
)


@dataclass(frozen=True)
class GuardDecision:
    admitted: bool
    reason: str
    guard_results: dict[str, Any]
    violations: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "reason": self.reason,
            "guard_results": self.guard_results,
            "violations": list(self.violations),
        }


class GuardOrchestrator:
    """
    AfriProgramming constitutional guard aggregator.

    Constitutional properties:
    - read-only
    - fail-closed
    - deterministic
    - non-authoritative
    - aggregates guard decisions
    """

    MODE = "PHASE_4_CONSTITUTIONAL_GUARD"

    def __init__(self):
        self.authority_guard = AuthorityGuard()
        self.replay_guard = ReplayGuard()
        self.surface_guard = SurfaceGuard()
        self.claim_guard = ClaimGuard()

    def evaluate_payload(
        self,
        payload: dict[str, Any],
    ) -> GuardDecision:
        authority = self.authority_guard.evaluate_payload(payload)
        replay = self.replay_guard.evaluate_payload(payload)
        surface = self.surface_guard.evaluate_payload(payload)
        claim = self.claim_guard.evaluate_payload(payload)

        decisions = {
            "authority": authority.canonical_dict(),
            "replay": replay.canonical_dict(),
            "surface": surface.canonical_dict(),
            "claim": claim.canonical_dict(),
        }

        all_violations = self._collect_violations(
            authority=authority,
            replay=replay,
            surface=surface,
            claim=claim,
        )

        admitted = (
            authority.admitted
            and replay.admitted
            and surface.admitted
            and claim.admitted
        )

        return GuardDecision(
            admitted=admitted,
            reason=(
                "constitutional_guard_admitted"
                if admitted
                else "constitutional_guard_rejected"
            ),
            guard_results=decisions,
            violations=all_violations,
        )

    def _collect_violations(
        self,
        *,
        authority: AuthorityDecision,
        replay: ReplayDecision,
        surface: SurfaceDecision,
        claim: ClaimDecision,
    ) -> tuple[str, ...]:
        violations = (
            tuple(f"authority:{item}" for item in authority.violations)
            + tuple(f"replay:{item}" for item in replay.violations)
            + tuple(f"surface:{item}" for item in surface.violations)
            + tuple(f"claim:{item}" for item in claim.violations)
        )

        return tuple(sorted(set(violations)))

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "mode": self.MODE,
            "guards": [
                "authority",
                "replay",
                "surface",
                "claim",
            ],
            "fail_closed": True,
        }