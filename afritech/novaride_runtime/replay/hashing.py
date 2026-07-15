from __future__ import annotations

from typing import Any

from afritech.novaride_runtime.events.hashing import canonical_hash


def canonical_sha256(payload: dict[str, Any]) -> str:
    return canonical_hash(payload)


def replay_plan_hash(plan: Any) -> str:
    payload = {
        "id": str(plan.id),
        "version": int(plan.version),
        "scenario_type": plan.scenario_type,
        "source_reference": plan.source_reference,
        "target_environment": plan.target_environment,
        "actions": list(plan.actions),
        "validation_requirements": list(plan.validation_requirements),
        "rollback_plan": plan.rollback_plan,
        "risk_level": plan.risk_level,
        "affected_resources": list(plan.affected_resources),
    }
    return canonical_sha256(payload)
