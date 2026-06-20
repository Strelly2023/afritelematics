from __future__ import annotations

from typing import Any

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


DEFAULT_ZERO_TRUST_POLICIES = (
    ("deployment_requires_approval", "deploy", {"require_approval": True}),
    ("production_requires_verifier", "deploy", {"environment": "production", "required_role": "VERIFIER"}),
    ("cross_org_access_denied", "access", {"deny_cross_org": True}),
    ("signed_audit_required", "audit", {"require_signed_audit": True}),
    ("certification_requires_high_trust", "certification", {"min_trust_score": 80}),
)


class ZeroTrustService:
    """OPA-style zero-trust decision engine."""

    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def seed_defaults(self, organization_id: str, created_by: str = "system") -> list[dict[str, Any]]:
        existing = {
            (policy["policy_name"], policy["version"])
            for policy in self.repository.list_zero_trust_policies(organization_id=organization_id, limit=100)
        }
        created: list[dict[str, Any]] = []
        for policy_name, rule_type, payload in DEFAULT_ZERO_TRUST_POLICIES:
            key = (policy_name, "v1")
            if key in existing:
                continue
            created.append(
                self.repository.store_zero_trust_policy(
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
        return self.repository.store_zero_trust_policy(
            organization_id=organization_id,
            policy_name=policy_name,
            version=version,
            rule_type=rule_type,
            rule_payload=rule_payload,
            active=active,
            created_by=created_by,
        )

    def list_policies(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_zero_trust_policies(organization_id=organization_id)

    def decisions(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_zero_trust_decisions(organization_id=organization_id)

    def evaluate(
        self,
        *,
        organization_id: str,
        subject: str,
        action: str,
        resource: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        self.seed_defaults(organization_id)
        policies = self.repository.list_zero_trust_policies(organization_id=organization_id, limit=100)
        active = {policy["policy_name"]: policy for policy in policies if policy["active"]}
        allowed = True
        reason = "allowed"

        if active.get("cross_org_access_denied") and bool(context.get("cross_org")):
            allowed = False
            reason = "cross organization access denied"

        if action == "deploy":
            policy = active.get("deployment_requires_approval")
            if policy and not bool(context.get("approved")):
                allowed = False
                reason = "deployment not approved"
            policy = active.get("production_requires_verifier")
            if (
                context.get("environment") == "production"
                and not bool(context.get("approved"))
                and context.get("actor_role") != "VERIFIER"
            ):
                allowed = False
                reason = "production requires verifier"

        if action == "audit":
            policy = active.get("signed_audit_required")
            if policy and not bool(context.get("signed_audit_valid")):
                allowed = False
                reason = "signed audit required"

        if action == "certification":
            policy = active.get("certification_requires_high_trust")
            min_trust = int(policy["rule_payload"].get("min_trust_score", 80)) if policy else 80
            if int(context.get("trust_score", 0)) < min_trust:
                allowed = False
                reason = "high trust required for certification"

        policy = active.get("quota_required_before_execution")
        if action == "execution" and policy and not bool(context.get("quota_available", True)):
            allowed = False
            reason = "quota required before execution"

        policy = active.get("production_requires_verifier")
        if action == "access" and policy and context.get("device_trust") == "untrusted":
            allowed = False
            reason = "device trust too low"

        policy_id = next(iter(active.values()), {"policy_id": "zt-default"})["policy_id"]
        decision = self.repository.store_zero_trust_decision(
            organization_id=organization_id,
            policy_id=policy_id,
            subject=subject,
            action=action,
            resource=resource,
            allowed=allowed,
            reason=reason,
            context=context,
        )
        return {
            **decision,
            "allowed": allowed,
            "reason": reason,
        }


__all__ = ["ZeroTrustService", "DEFAULT_ZERO_TRUST_POLICIES"]
