"""Governed progressive delivery and automatic rollback decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RolloutPlan:
    release_id: str
    source_environment: str
    target_environment: str
    strategy: str
    canary_percent: int
    approved_change: bool
    contract_validation: bool
    security_review: bool
    error_budget_available: bool
    rollback_verified: bool
    observability_ready: bool
    data_migration_safe: bool


@dataclass(frozen=True)
class RolloutDecision:
    status: str
    reasons: tuple[str, ...]
    next_canary_percent: int | None


ENVIRONMENTS = ("development", "integration", "staging", "production")
CANARY_STAGES = (1, 5, 25, 50, 100)


def evaluate_rollout(
    plan: RolloutPlan,
    *,
    slo_burn_rate_exceeded: bool = False,
    replay_mismatch: bool = False,
    signature_failure: bool = False,
    tenant_isolation_violation: bool = False,
    schema_error_rate_exceeded: bool = False,
) -> RolloutDecision:
    source = ENVIRONMENTS.index(plan.source_environment)
    target = ENVIRONMENTS.index(plan.target_environment)
    if target != source + 1:
        return RolloutDecision("BLOCKED", ("environment_promotion_order",), None)
    incidents = {
        "slo_burn_rate_exceeded": slo_burn_rate_exceeded,
        "replay_mismatch": replay_mismatch,
        "signature_failure": signature_failure,
        "tenant_isolation_violation": tenant_isolation_violation,
        "schema_error_rate_exceeded": schema_error_rate_exceeded,
    }
    triggered = tuple(name for name, present in incidents.items() if present)
    if triggered:
        return RolloutDecision("ROLLBACK", triggered, None)
    required = {
        "approved_change": plan.approved_change,
        "contract_validation": plan.contract_validation,
        "security_review": plan.security_review,
        "error_budget_available": plan.error_budget_available,
        "rollback_verified": plan.rollback_verified,
        "observability_ready": plan.observability_ready,
        "data_migration_safe": plan.data_migration_safe,
    }
    missing = tuple(name for name, present in required.items() if not present)
    if missing:
        return RolloutDecision("BLOCKED", missing, None)
    if plan.strategy not in {"canary", "blue_green"}:
        return RolloutDecision("BLOCKED", ("unsupported_strategy",), None)
    if plan.strategy == "blue_green":
        return RolloutDecision("PROMOTE", (), 100)
    if plan.canary_percent not in CANARY_STAGES:
        return RolloutDecision("BLOCKED", ("invalid_canary_stage",), None)
    position = CANARY_STAGES.index(plan.canary_percent)
    next_percent = (
        CANARY_STAGES[position + 1] if position + 1 < len(CANARY_STAGES) else None
    )
    return RolloutDecision(
        "COMPLETE" if next_percent is None else "PROMOTE",
        (),
        next_percent,
    )
