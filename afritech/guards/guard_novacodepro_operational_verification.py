from __future__ import annotations


def verify_no_production_claim_from_ci(evidence: dict[str, object]) -> bool:
    return not (evidence.get("environment") == "ci" and evidence.get("verified") is True)


def verify_no_request_boolean_approval(payload: dict[str, object]) -> bool:
    return not any(key in payload for key in ("ga_allowed", "real_payments_enabled", "approved"))
