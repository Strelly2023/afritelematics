from __future__ import annotations

from typing import Any

from .impact_analysis import analyze_rule_change, detect_conflicts
from .risk_engine import compute_risk
from .rules_engine import evaluate_rules
from .validation_engine import validate_proposal


def simulate(
    payload: dict[str, Any],
    event_type: str = "ManualTrustEvent",
    target_rule: str | None = None,
) -> dict[str, Any]:
    proposal = {
        "proposal_id": "simulation",
        "event_id": "simulation",
        "type": event_type,
        "change": payload,
        "source": "simulation",
    }
    validation = validate_proposal(proposal)
    decision = evaluate_rules(proposal, validation)
    impacted_rules = analyze_rule_change(target_rule) if target_rule else []
    conflicts = detect_conflicts(target_rule) if target_rule else []
    risk = compute_risk(proposal, validation, decision, impacted_rules)
    return {
        "validation": validation,
        "decision": decision,
        "risk": risk,
        "impacted_rules": impacted_rules,
        "conflicts": conflicts,
    }
