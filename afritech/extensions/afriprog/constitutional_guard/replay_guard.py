from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReplayDecision:
    admitted: bool
    reason: str
    violations: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "reason": self.reason,
            "violations": list(self.violations),
        }


class ReplayGuard:
    """
    AfriProgramming replay-safety guard.

    Ensures engineering actions do not claim or perform replay-unsafe behavior.
    """

    FORBIDDEN_ACTIONS = frozenset(
        {
            "mutate_event_log",
            "rewrite_replay_trace",
            "modify_replay_hash",
            "skip_replay_verification",
            "bypass_replay_guard",
            "change_event_ordering",
            "delete_witness",
            "rewrite_witness",
        }
    )

    FORBIDDEN_CLAIMS = frozenset(
        {
            "replay is optional",
            "replay bypassed",
            "truth without replay",
            "skip replay",
            "replay not required",
        }
    )

    def evaluate_payload(self, payload: dict[str, Any]) -> ReplayDecision:
        actions = tuple(str(item).lower() for item in payload.get("actions", ()))
        claims = tuple(str(item).lower() for item in payload.get("claims", ()))

        violations = tuple(
            sorted(
                {
                    forbidden
                    for forbidden in self.FORBIDDEN_ACTIONS
                    if forbidden in actions
                }
                | {
                    forbidden
                    for forbidden in self.FORBIDDEN_CLAIMS
                    if any(forbidden in claim for claim in claims)
                }
            )
        )

        if violations:
            return ReplayDecision(
                admitted=False,
                reason="replay_safety_violation",
                violations=violations,
            )

        return ReplayDecision(
            admitted=True,
            reason="replay_safety_admitted",
            violations=(),
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "guard": "ReplayGuard",
            "forbidden_action_count": len(self.FORBIDDEN_ACTIONS),
            "forbidden_claim_count": len(self.FORBIDDEN_CLAIMS),
        }