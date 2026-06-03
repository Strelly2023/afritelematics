from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class AuthorityGuardError(Exception):
    """Raised when authority guard validation fails."""


@dataclass(frozen=True)
class AuthorityDecision:
    admitted: bool
    reason: str
    authority_level: str
    violations: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "reason": self.reason,
            "authority_level": self.authority_level,
            "violations": list(self.violations),
        }


class AuthorityGuard:
    """
    AfriProgramming authority containment guard.

    Constitutional properties:
    - non-authoritative
    - read-only decision surface
    - prohibits authority escalation
    - prohibits mutation authority claims
    - prohibits truth-authority claims
    """

    AUTHORITY_LEVEL = "NON_AUTHORITATIVE_ENGINEERING_ASSISTANT"

    FORBIDDEN_CLAIMS = frozenset(
        {
            "authoritative",
            "source of truth",
            "defines truth",
            "redefines admissibility",
            "bypass validator",
            "override constitution",
            "override replay",
            "skip evidence",
            "force merge",
            "auto merge",
            "self approve",
            "push to main",
            "rewrite history",
            "delete evidence",
            "modify constitution",
            "production proven",
            "guaranteed safe",
        }
    )

    FORBIDDEN_ACTIONS = frozenset(
        {
            "write_core",
            "modify_constitution",
            "modify_registry",
            "modify_guard",
            "bypass_ci",
            "skip_validator",
            "commit_without_evidence",
            "merge_without_approval",
            "push_to_main",
            "delete_evidence",
            "rewrite_history",
        }
    )

    def evaluate_claims(
        self,
        claims: tuple[str, ...] | list[str],
    ) -> AuthorityDecision:
        normalized_claims = tuple(
            claim.lower()
            for claim in claims
        )

        violations = tuple(
            sorted(
                forbidden
                for forbidden in self.FORBIDDEN_CLAIMS
                if any(forbidden in claim for claim in normalized_claims)
            )
        )

        if violations:
            return AuthorityDecision(
                admitted=False,
                reason="authority_claim_violation",
                authority_level=self.AUTHORITY_LEVEL,
                violations=violations,
            )

        return AuthorityDecision(
            admitted=True,
            reason="authority_claims_admitted",
            authority_level=self.AUTHORITY_LEVEL,
            violations=(),
        )

    def evaluate_actions(
        self,
        actions: tuple[str, ...] | list[str],
    ) -> AuthorityDecision:
        normalized_actions = tuple(
            action.lower()
            for action in actions
        )

        violations = tuple(
            sorted(
                action
                for action in normalized_actions
                if action in self.FORBIDDEN_ACTIONS
            )
        )

        if violations:
            return AuthorityDecision(
                admitted=False,
                reason="authority_action_violation",
                authority_level=self.AUTHORITY_LEVEL,
                violations=violations,
            )

        return AuthorityDecision(
            admitted=True,
            reason="authority_actions_admitted",
            authority_level=self.AUTHORITY_LEVEL,
            violations=(),
        )

    def evaluate_payload(
        self,
        payload: dict[str, Any],
    ) -> AuthorityDecision:
        claims = tuple(
            str(item)
            for item in payload.get("claims", ())
        )
        actions = tuple(
            str(item)
            for item in payload.get("actions", ())
        )

        claim_decision = self.evaluate_claims(claims)
        action_decision = self.evaluate_actions(actions)

        violations = tuple(
            sorted(
                claim_decision.violations
                + action_decision.violations
            )
        )

        admitted = claim_decision.admitted and action_decision.admitted

        return AuthorityDecision(
            admitted=admitted,
            reason=(
                "authority_payload_admitted"
                if admitted
                else "authority_payload_rejected"
            ),
            authority_level=self.AUTHORITY_LEVEL,
            violations=violations,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_level": self.AUTHORITY_LEVEL,
            "forbidden_claim_count": len(self.FORBIDDEN_CLAIMS),
            "forbidden_action_count": len(self.FORBIDDEN_ACTIONS),
        }
