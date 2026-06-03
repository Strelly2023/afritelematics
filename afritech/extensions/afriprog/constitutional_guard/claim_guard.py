from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ClaimDecision:
    admitted: bool
    reason: str
    violations: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "reason": self.reason,
            "violations": list(self.violations),
        }


class ClaimGuard:
    """
    AfriProgramming claim discipline guard.

    Enforces:
    - no claim without evidence
    - no production claim without deployment evidence
    - no authority claim from an engineering assistant
    """

    FORBIDDEN_UNSUPPORTED_CLAIMS = frozenset(
        {
            "production ready",
            "production proven",
            "guaranteed",
            "fully autonomous",
            "cannot fail",
            "cannot drift",
            "cannot misrepresent",
            "mathematically incapable",
            "truth defining",
            "source of truth",
            "authority layer",
        }
    )

    def evaluate_claims(
        self,
        claims: tuple[str, ...] | list[str],
        evidence_ids: tuple[str, ...] | list[str] = (),
    ) -> ClaimDecision:
        normalized_claims = tuple(claim.lower() for claim in claims)
        normalized_evidence = tuple(item.strip() for item in evidence_ids if item.strip())

        violations = []

        if normalized_claims and not normalized_evidence:
            violations.append("claim_without_evidence")

        for claim in normalized_claims:
            for forbidden in self.FORBIDDEN_UNSUPPORTED_CLAIMS:
                if forbidden in claim:
                    violations.append(f"unsupported_claim:{forbidden}")

        if violations:
            return ClaimDecision(
                admitted=False,
                reason="claim_discipline_violation",
                violations=tuple(sorted(set(violations))),
            )

        return ClaimDecision(
            admitted=True,
            reason="claims_admitted",
            violations=(),
        )

    def evaluate_payload(self, payload: dict[str, Any]) -> ClaimDecision:
        claims = tuple(str(item) for item in payload.get("claims", ()))
        evidence_ids = tuple(str(item) for item in payload.get("evidence_ids", ()))

        return self.evaluate_claims(
            claims=claims,
            evidence_ids=evidence_ids,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "guard": "ClaimGuard",
            "forbidden_claim_count": len(self.FORBIDDEN_UNSUPPORTED_CLAIMS),
            "requires_evidence": True,
        }