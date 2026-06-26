"""Read-only operational contract registry and readiness metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from afritech.platform_operations.reliability import ServiceObjective


OPERATIONS_CONTRACT = Path(__file__).with_name("operations.yaml")


def load_operations_contract() -> dict[str, Any]:
    payload = yaml.safe_load(OPERATIONS_CONTRACT.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("operations_contract_must_be_an_object")
    return payload


def service_objectives() -> tuple[ServiceObjective, ...]:
    return tuple(
        ServiceObjective(
            service=item["service"],
            availability_target=float(item["availability_target"]),
            latency_p95_ms=int(item["latency_p95_ms"]),
            window_days=int(item["window_days"]),
            rto_minutes=int(item["rto_minutes"]),
            rpo_minutes=int(item["rpo_minutes"]),
            fast_burn_threshold=float(item["fast_burn_threshold"]),
            slow_burn_threshold=float(item["slow_burn_threshold"]),
        )
        for item in load_operations_contract()["service_objectives"]
    )


def operations_readiness() -> dict[str, Any]:
    contract = load_operations_contract()
    objectives = service_objectives()
    return {
        "contract_version": contract["version"],
        "policy_version": contract["policy"]["policy_version"],
        "workflow_version": contract["workflow"]["workflow_version"],
        "service_objective_count": len(objectives),
        "production_gates": contract["rollout"]["production_requires"],
        "canary_stages_percent": contract["rollout"]["canary_stages_percent"],
        "automatic_rollback_signals": contract["rollout"]["automatic_rollback_on"],
        "data_classifications": contract["data_governance"]["classifications"],
        "retention_classes": contract["data_governance"]["retention_classes"],
        "developer_assets": contract["developer_experience"]["required_assets"],
        "ready": len(objectives) >= 3,
        "execution_authority": False,
    }
