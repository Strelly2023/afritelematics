"""Validate NovaTech operational excellence contracts and runtime controls."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from afritech.platform_operations.policy import PolicyInput, VersionedPolicyEngine
from afritech.platform_operations.registry import operations_readiness
from afritech.platform_operations.reliability import evaluate_error_budget
from afritech.platform_operations.rollout import RolloutPlan, evaluate_rollout
from afritech.platform_operations.registry import service_objectives


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "afritech/platform_operations/operations.yaml"


class PlatformOperationsViolation(RuntimeError):
    pass


def validate() -> bool:
    payload = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PlatformOperationsViolation("operations contract must be an object")
    if payload.get("schema") != "novatech.platform.operations.v1":
        raise PlatformOperationsViolation("operations contract schema mismatch")
    _validate_implementation_binding(payload)
    _validate_policy(payload)
    _validate_workflow(payload)
    _validate_objectives(payload)
    _validate_rollout(payload)
    _validate_data_governance(payload)
    _validate_developer_assets(payload)
    if operations_readiness()["ready"] is not True:
        raise PlatformOperationsViolation("operations readiness is incomplete")
    return True


def _validate_implementation_binding(payload: dict[str, Any]) -> None:
    binding = payload.get("implementation_binding", {})
    expected = {
        "runtime_package": "afritech.platform_operations",
        "operator_surface": "apps/novaride-operations",
        "api_surface": "afritech.api.runtime_operations_api",
        "binding": "afritech/governance/bindings/BIND-PLATFORM-OPERATIONS-TOOLING.yaml",
    }
    mismatched = [
        name
        for name, expected_value in expected.items()
        if binding.get(name) != expected_value
    ]
    if mismatched:
        raise PlatformOperationsViolation(
            f"operations implementation binding is incomplete: {mismatched}"
        )
    runtime = ROOT / "afritech/platform_operations"
    required_paths = (
        runtime,
        ROOT / binding["operator_surface"],
        ROOT / "afritech/api/runtime_operations_api.py",
        ROOT / binding["binding"],
    )
    if not all(path.exists() for path in required_paths):
        raise PlatformOperationsViolation("operations implementation path is unresolved")
    missing_modules = [
        name
        for name in binding.get("required_modules", [])
        if not (runtime / f"{name}.py").is_file()
    ]
    if missing_modules:
        raise PlatformOperationsViolation(
            f"operations runtime modules are missing: {missing_modules}"
        )
    if binding.get("execution_authority") is not False:
        raise PlatformOperationsViolation(
            "operations tooling must not claim domain execution authority"
        )
    governed_binding = yaml.safe_load((ROOT / binding["binding"]).read_text(encoding="utf-8"))
    if (
        not isinstance(governed_binding, dict)
        or governed_binding.get("schema") != "novatech.operations_binding.v1"
        or governed_binding.get("status") != "active"
    ):
        raise PlatformOperationsViolation("operations governance binding is not active")


def _validate_policy(payload: dict[str, Any]) -> None:
    policy = payload["policy"]
    orders = [rule["order"] for rule in policy["rules"]]
    if orders != sorted(set(orders)):
        raise PlatformOperationsViolation("policy rules must have unique canonical order")
    decision = VersionedPolicyEngine().evaluate(
        PolicyInput(
            tenant_id="tenant-a",
            identity_tenant_id="tenant-b",
            actor_id="actor",
            roles=("OPERATOR",),
            scopes=("payments:write",),
            action="payment.execute",
        )
    )
    if decision.decision != "DENY" or "tenant_mismatch" not in decision.checks:
        raise PlatformOperationsViolation("policy engine does not fail closed")


def _validate_workflow(payload: dict[str, Any]) -> None:
    workflow = payload["workflow"]
    if not workflow["persistence"]["checkpoint_each_transition"]:
        raise PlatformOperationsViolation("workflow transitions must be checkpointed")
    if "COMPENSATED" not in workflow["terminal_states"]:
        raise PlatformOperationsViolation("workflow compensation state missing")


def _validate_objectives(payload: dict[str, Any]) -> None:
    objectives = service_objectives()
    if len(objectives) != len(payload["service_objectives"]):
        raise PlatformOperationsViolation("service objective registry mismatch")
    for objective in objectives:
        healthy = evaluate_error_budget(
            objective, observed_requests=1_000_000, failed_requests=0
        )
        if not healthy.release_allowed:
            raise PlatformOperationsViolation(f"healthy SLO rejected: {objective.service}")


def _validate_rollout(payload: dict[str, Any]) -> None:
    rollout = payload["rollout"]
    if rollout["canary_stages_percent"] != [1, 5, 25, 50, 100]:
        raise PlatformOperationsViolation("canonical canary stages changed")
    plan = RolloutPlan(
        release_id="validator",
        source_environment="staging",
        target_environment="production",
        strategy="canary",
        canary_percent=5,
        approved_change=True,
        contract_validation=True,
        security_review=True,
        error_budget_available=True,
        rollback_verified=True,
        observability_ready=True,
        data_migration_safe=True,
    )
    if evaluate_rollout(plan).status != "PROMOTE":
        raise PlatformOperationsViolation("healthy rollout cannot promote")
    if evaluate_rollout(plan, replay_mismatch=True).status != "ROLLBACK":
        raise PlatformOperationsViolation("replay mismatch must trigger rollback")


def _validate_data_governance(payload: dict[str, Any]) -> None:
    governance = payload["data_governance"]
    if "RESTRICTED" not in governance["classifications"]:
        raise PlatformOperationsViolation("restricted data classification missing")
    if governance["retention_classes"]["LEGAL_HOLD"] is not None:
        raise PlatformOperationsViolation("legal hold must not expire automatically")
    resources = governance["resources"]
    if len({item["id"] for item in resources}) != len(resources):
        raise PlatformOperationsViolation("duplicate governed data resource")


def _validate_developer_assets(payload: dict[str, Any]) -> None:
    paths = (
        ROOT / "docs/developer/NOVATECH_PLATFORM_QUICKSTART.md",
        ROOT / "docs/developer/NOVATECH_COMPATIBILITY_MATRIX.md",
        ROOT / "docs/developer/NOVATECH_CONTRACT_MIGRATION_GUIDE.md",
    )
    if not all(path.is_file() for path in paths):
        raise PlatformOperationsViolation("developer ecosystem assets missing")
    required = set(payload["developer_experience"]["required_assets"])
    if {"quickstart_application", "migration_guides", "compatibility_matrix"} - required:
        raise PlatformOperationsViolation("developer asset registry incomplete")


def main() -> int:
    try:
        validate()
    except Exception as exc:
        print(f"NovaTech platform operations validation FAILED: {exc}")
        return 1
    print("NovaTech platform operations validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
