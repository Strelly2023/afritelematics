from __future__ import annotations

from typing import Any

from afritech.afriprogramming.assurance.cert_signer import hash_payload
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


DEFAULT_POLICIES = (
    ("deployment_requires_approval", "deployment", {"require_approval": True}),
    ("production_requires_verifier", "deployment", {"environment": "production", "required_role": "VERIFIER"}),
    ("proof_required_after_deployment", "verification", {"require_proof": True}),
    ("audit_chain_must_verify", "audit", {"require_chain": True}),
    ("cross_org_access_denied", "access", {"deny_cross_org": True}),
    ("quota_required_before_execution", "quota", {"require_quota": True}),
    ("certification_requires_high_trust", "certification", {"min_trust_score": 80}),
)


class PolicyRegistryService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def seed_defaults(self, organization_id: str, created_by: str = "system") -> list[dict[str, Any]]:
        policies = self.repository.list_policy_definitions(organization_id=organization_id, limit=100)
        existing = {(policy["policy_name"], policy["version"]) for policy in policies}
        created: list[dict[str, Any]] = []
        for policy_name, rule_type, payload in DEFAULT_POLICIES:
            key = (policy_name, "v1")
            if key in existing:
                continue
            created.append(
                self.repository.store_policy_definition(
                    organization_id=organization_id,
                    policy_name=policy_name,
                    version="v1",
                    rule_type=rule_type,
                    rule_payload=payload,
                    active=True,
                    created_by=created_by,
                )
            )
        return created

    def create_policy(
        self,
        *,
        organization_id: str,
        policy_name: str,
        version: str,
        rule_type: str,
        rule_payload: dict[str, Any],
        active: bool,
        created_by: str,
    ) -> dict[str, Any]:
        return self.repository.store_policy_definition(
            organization_id=organization_id,
            policy_name=policy_name,
            version=version,
            rule_type=rule_type,
            rule_payload=rule_payload,
            active=active,
            created_by=created_by,
        )

    def list_policies(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_policy_definitions(organization_id=organization_id)

    def decisions(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_policy_decisions(organization_id=organization_id)

    def evaluate(
        self,
        *,
        organization_id: str,
        action: str,
        actor_user_id: str,
        target: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        policies = self.repository.list_policy_definitions(organization_id=organization_id, limit=100)
        active = {policy["policy_name"]: policy for policy in policies if policy["active"]}
        allowed = True
        reason = "allowed"

        if action == "deploy":
            policy = active.get("deployment_requires_approval")
            if policy and not bool(payload.get("approved")):
                allowed = False
                reason = "deployment not approved"
            policy = active.get("production_requires_verifier")
            if payload.get("environment") == "production" and payload.get("actor_role") != "VERIFIER":
                allowed = False
                reason = "production requires verifier"

        if action == "verify":
            policy = active.get("proof_required_after_deployment")
            if policy and not bool(payload.get("proof_exists")):
                allowed = False
                reason = "proof required after deployment"

        if action == "certification":
            policy = active.get("certification_requires_high_trust")
            if policy and int(payload.get("trust_score", 0)) < int(policy["rule_payload"].get("min_trust_score", 80)):
                allowed = False
                reason = "high trust required for certification"

        if action == "access":
            policy = active.get("cross_org_access_denied")
            if policy and bool(payload.get("cross_org")):
                allowed = False
                reason = "cross organization access denied"

        if action == "execution":
            policy = active.get("quota_required_before_execution")
            if policy and not bool(payload.get("quota_available", True)):
                allowed = False
                reason = "quota required before execution"

        decision = self.repository.store_policy_decision(
            organization_id=organization_id,
            policy_id=active.get("deployment_requires_approval", next(iter(active.values()), {"policy_id": "policy-default"}))["policy_id"],
            action=action,
            allowed=allowed,
            reason=reason,
            actor_user_id=actor_user_id,
            target=target,
            payload=payload,
        )
        return {
            **decision,
            "allowed": allowed,
            "reason": reason,
        }

    def payload_hash(self, payload: dict[str, Any]) -> str:
        return hash_payload(payload)
