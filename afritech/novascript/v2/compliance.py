from __future__ import annotations

from hashlib import sha256
from typing import Any


class AIRegulatoryComplianceLayer:
    def assess(
        self,
        *,
        organization_id: str,
        project_id: str,
        policy_decision: dict[str, Any],
        certificate_chain: dict[str, Any],
        assurance: dict[str, Any],
    ) -> dict[str, Any]:
        controls = {
            "policy_provenance": bool(policy_decision.get("policy_hash")),
            "certificate_lineage": bool(certificate_chain.get("chain_hash")),
            "continuous_assurance": assurance.get("mode") == "continuous_assurance",
            "auditability": assurance.get("assurance_status") in {"assured", "review"},
        }
        compliance_hash = sha256(f"{organization_id}:{project_id}:{sorted(controls.items())}".encode()).hexdigest()
        return {
            "mode": "ai_regulatory_compliance_layer",
            "organization_id": organization_id,
            "project_id": project_id,
            "controls": controls,
            "compliant": all(controls.values()),
            "frameworks": ["AI_GOVERNANCE", "SOFTWARE_ASSURANCE", "AUDIT_READINESS"],
            "compliance_hash": compliance_hash,
        }


_DEFAULT_REGULATORY_COMPLIANCE = AIRegulatoryComplianceLayer()


def get_ai_regulatory_compliance_layer() -> AIRegulatoryComplianceLayer:
    return _DEFAULT_REGULATORY_COMPLIANCE
