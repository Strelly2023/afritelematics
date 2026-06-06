from __future__ import annotations

from typing import Any

from django.db import IntegrityError, OperationalError, ProgrammingError

from afritech.models import PredictionSignal, TrustGraphRecord


def predict_failure(
    proposal: dict[str, Any],
    validation: dict[str, Any],
    decision: dict[str, Any],
    risk: dict[str, Any],
) -> dict[str, Any]:
    factors: list[str] = []
    score = risk.get("score", 0)

    if not validation.get("passed"):
        factors.append("validation_failure")
    if any(not rule.get("passed") for rule in decision.get("rules", [])):
        factors.append("rule_instability")

    try:
        similar_blocked = TrustGraphRecord.objects.filter(
            proposal__type=proposal.get("type"),
            execution__status__startswith="blocked",
        ).count()
    except (OperationalError, ProgrammingError):
        similar_blocked = 0

    if similar_blocked > 3:
        score += 20
        factors.append("historical_blocks")

    will_fail = score > 65
    return {
        "will_fail": will_fail,
        "confidence": min(score / 100, 1.0),
        "factors": factors,
    }


def store_prediction_signal(proposal_id: str, prediction: dict[str, Any]) -> None:
    try:
        PredictionSignal.objects.create(
            proposal_id=proposal_id,
            predicted_failure=prediction["will_fail"],
            confidence=prediction["confidence"],
            risk_factors=prediction["factors"],
        )
    except (IntegrityError, OperationalError, ProgrammingError):
        pass
