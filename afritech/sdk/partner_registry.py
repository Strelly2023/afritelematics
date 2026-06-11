from __future__ import annotations

from typing import Any


class PartnerRegistryClient:
    def prepare_registration_request(
        self,
        *,
        partner_id: str,
        organization: str,
        sector: str,
        region_id: str,
        integration_stage: str = "discovery",
        verifier_sdk_status: str = "planned",
    ) -> dict[str, Any]:
        return {
            "partner_id": partner_id,
            "organization": organization,
            "sector": sector,
            "region_id": region_id,
            "integration_stage": integration_stage,
            "verifier_sdk_status": verifier_sdk_status,
        }

    def prepare_onboarding_update(
        self,
        *,
        status: str,
        integration_stage: str | None = None,
        public_endpoint_enabled: bool | None = None,
        trust_registry_enabled: bool | None = None,
        evidence_anchor_count: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": status}
        if integration_stage is not None:
            payload["integration_stage"] = integration_stage
        if public_endpoint_enabled is not None:
            payload["public_endpoint_enabled"] = public_endpoint_enabled
        if trust_registry_enabled is not None:
            payload["trust_registry_enabled"] = trust_registry_enabled
        if evidence_anchor_count is not None:
            payload["evidence_anchor_count"] = evidence_anchor_count
        return payload
