from __future__ import annotations

from typing import Any

from django.db import IntegrityError, OperationalError, ProgrammingError

from afritech.models import RiskScore


def compute_risk(
    proposal: dict[str, Any],
    validation: dict[str, Any],
    decision: dict[str, Any],
    dependencies: list[str] | None = None,
) -> dict[str, Any]:
    dependencies = dependencies or []
    score = 0
    breakdown: dict[str, Any] = {}

    if not validation.get("passed"):
        score += 50
        breakdown["validation"] = "failed"
    else:
        breakdown["validation"] = "passed"

    failed_rules = [
        rule for rule in decision.get("rules", []) if not rule.get("passed")
    ]
    score += len(failed_rules) * 20
    breakdown["rule_failures"] = len(failed_rules)

    score += len(set(dependencies)) * 5
    breakdown["dependency_impact"] = len(set(dependencies))

    if proposal.get("type") in {"TripCompleted", "RideAccepted"}:
        score += 5
        breakdown["execution_sensitive"] = True

    level = "low"
    if score > 50:
        level = "high"
    elif score > 20:
        level = "medium"

    return {"score": score, "level": level, "breakdown": breakdown}


def store_risk_score(reference_id: str, risk: dict[str, Any], scope: str = "proposal") -> None:
    try:
        RiskScore.objects.create(
            scope=scope,
            reference_id=reference_id,
            score=risk["score"],
            level=risk["level"],
            breakdown=risk["breakdown"],
        )
    except (IntegrityError, OperationalError, ProgrammingError):
        pass
