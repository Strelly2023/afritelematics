"""Versioned, data-driven NovaPower policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import yaml


OPERATIONS_CONTRACT = Path(__file__).with_name("operations.yaml")


@dataclass(frozen=True)
class PolicyInput:
    tenant_id: str
    identity_tenant_id: str
    actor_id: str
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    action: str
    required_roles: tuple[str, ...] = ()
    required_scopes: tuple[str, ...] = ()
    resource_owner_id: str | None = None
    risk_score: Decimal = Decimal("0")
    risk_score_max: Decimal = Decimal("0.70")


@dataclass(frozen=True)
class PolicyEvaluation:
    decision: str
    reason: str
    checks: tuple[str, ...]
    policy_version: str
    policy_hash: str
    trace_id: str


class VersionedPolicyEngine:
    def __init__(self, contract_path: Path = OPERATIONS_CONTRACT) -> None:
        payload = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        self.policy = payload["policy"]
        encoded = json.dumps(self.policy, sort_keys=True, separators=(",", ":"))
        self.policy_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def evaluate(self, value: PolicyInput) -> PolicyEvaluation:
        outcomes = {
            "tenant_aligned": value.tenant_id == value.identity_tenant_id,
            "role_allowed": (
                not value.required_roles
                or bool(set(value.required_roles).intersection(value.roles))
            ),
            "scope_allowed": set(value.required_scopes).issubset(value.scopes),
            "ownership_valid": value.resource_owner_id in {None, value.actor_id},
            "risk_within_policy": value.risk_score <= value.risk_score_max,
        }
        checks: list[str] = []
        failures: list[str] = []
        failure_names = {
            "tenant_aligned": "tenant_mismatch",
            "role_allowed": "role_missing",
            "scope_allowed": "scope_missing",
            "ownership_valid": "ownership_mismatch",
            "risk_within_policy": "risk_above_policy",
        }
        for rule in sorted(self.policy["rules"], key=lambda item: item["order"]):
            check = rule["check"]
            if outcomes[check]:
                checks.append(check)
            else:
                failures.append(failure_names[check])
        decision = "ALLOW" if not failures else self.policy["default_effect"]
        reason = "All core constraints passed" if not failures else ", ".join(failures)
        trace = {
            "input": _canonical_input(value),
            "policy_version": self.policy["policy_version"],
            "policy_hash": self.policy_hash,
        }
        trace_id = hashlib.sha256(
            json.dumps(trace, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:24]
        return PolicyEvaluation(
            decision=decision,
            reason=reason,
            checks=tuple(checks + failures),
            policy_version=self.policy["policy_version"],
            policy_hash=self.policy_hash,
            trace_id=trace_id,
        )


def _canonical_input(value: PolicyInput) -> dict[str, object]:
    return {
        "tenant_id": value.tenant_id,
        "identity_tenant_id": value.identity_tenant_id,
        "actor_id": value.actor_id,
        "roles": sorted(value.roles),
        "scopes": sorted(value.scopes),
        "action": value.action,
        "required_roles": sorted(value.required_roles),
        "required_scopes": sorted(value.required_scopes),
        "resource_owner_id": value.resource_owner_id,
        "risk_score": str(value.risk_score),
        "risk_score_max": str(value.risk_score_max),
    }
