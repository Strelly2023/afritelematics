"""NovaID advisory-only AI helpers."""

from __future__ import annotations

from typing import Any


def identity_assistant(*, subject_id: str, topic: str, context: dict[str, Any]) -> dict[str, Any]:
    recommendation = "Verify evidence before any approval" if topic == "risk" else "Review with an authorized operator"
    return {
        "view": "novaid_identity_assistant",
        "subject_id": subject_id,
        "topic": topic,
        "recommendation": recommendation,
        "context": context,
        "advisory_only": True,
    }


def risk_explanations(*, subject_id: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "view": "novaid_risk_explanation",
        "subject_id": subject_id,
        "reasons": reasons,
        "advisory_only": True,
    }


def renewal_recommendations(*, subject_id: str, expiry_days: int) -> dict[str, Any]:
    return {
        "view": "novaid_renewal_recommendation",
        "subject_id": subject_id,
        "recommendation": "Renew identity before expiration" if expiry_days <= 30 else "Monitor renewal window",
        "advisory_only": True,
    }


__all__ = ["identity_assistant", "risk_explanations", "renewal_recommendations"]
