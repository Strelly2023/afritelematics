"""Partner onboarding registry for bounded external ecosystem growth."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


ALLOWED_STATUSES = frozenset(
    {
        "DISCOVERY",
        "QUALIFIED",
        "SANDBOX_ENABLED",
        "STAGING_ENABLED",
        "DEMO_READY",
        "LIVE_CONTROLLED",
    }
)


@dataclass(frozen=True)
class PartnerRegistryEntry:
    partner_id: str
    organization: str
    sector: str
    region_id: str
    integration_stage: str
    verifier_sdk_status: str
    public_endpoint_enabled: bool
    trust_registry_enabled: bool
    evidence_anchor_count: int
    status: str = "DISCOVERY"
    authority_boundary: str = "partner_registry_indexes_adoption_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.partner_registry_entry.v1",
            "partner_id": self.partner_id,
            "organization": self.organization,
            "sector": self.sector,
            "region_id": self.region_id,
            "integration_stage": self.integration_stage,
            "verifier_sdk_status": self.verifier_sdk_status,
            "public_endpoint_enabled": self.public_endpoint_enabled,
            "trust_registry_enabled": self.trust_registry_enabled,
            "evidence_anchor_count": self.evidence_anchor_count,
            "status": self.status,
            "authority_boundary": self.authority_boundary,
        }


class PartnerRegistryStore:
    """Small in-memory partner registry used for ecosystem onboarding."""

    def __init__(self, entries: tuple[PartnerRegistryEntry, ...] = ()) -> None:
        self._entries = {entry.partner_id: entry for entry in entries}

    def register(self, entry: PartnerRegistryEntry) -> None:
        self._entries[entry.partner_id] = entry

    def list_entries(self) -> tuple[PartnerRegistryEntry, ...]:
        return tuple(sorted(self._entries.values(), key=lambda entry: entry.partner_id))

    def load(self, partner_id: str) -> PartnerRegistryEntry:
        if partner_id not in self._entries:
            raise KeyError(partner_id)
        return self._entries[partner_id]

    def advance(
        self,
        partner_id: str,
        *,
        status: str,
        integration_stage: str | None = None,
        verifier_sdk_status: str | None = None,
        public_endpoint_enabled: bool | None = None,
        trust_registry_enabled: bool | None = None,
        evidence_anchor_count: int | None = None,
    ) -> PartnerRegistryEntry:
        current = self.load(partner_id)
        if status not in ALLOWED_STATUSES:
            raise ValueError("invalid_partner_status")
        updated = replace(
            current,
            status=status,
            integration_stage=integration_stage or current.integration_stage,
            verifier_sdk_status=verifier_sdk_status or current.verifier_sdk_status,
            public_endpoint_enabled=(
                current.public_endpoint_enabled
                if public_endpoint_enabled is None
                else public_endpoint_enabled
            ),
            trust_registry_enabled=(
                current.trust_registry_enabled
                if trust_registry_enabled is None
                else trust_registry_enabled
            ),
            evidence_anchor_count=(
                current.evidence_anchor_count
                if evidence_anchor_count is None
                else evidence_anchor_count
            ),
        )
        self.register(updated)
        return updated


def build_partner_registry_entry(
    *,
    partner_id: str,
    organization: str,
    sector: str,
    region_id: str,
    integration_stage: str,
    verifier_sdk_status: str,
    public_endpoint_enabled: bool = False,
    trust_registry_enabled: bool = False,
    evidence_anchor_count: int = 0,
    status: str = "DISCOVERY",
) -> PartnerRegistryEntry:
    if not partner_id.strip():
        raise ValueError("partner_id required")
    if not organization.strip():
        raise ValueError("organization required")
    if status not in ALLOWED_STATUSES:
        raise ValueError("invalid_partner_status")
    if evidence_anchor_count < 0:
        raise ValueError("evidence_anchor_count must be non_negative")
    return PartnerRegistryEntry(
        partner_id=partner_id,
        organization=organization,
        sector=sector,
        region_id=region_id,
        integration_stage=integration_stage,
        verifier_sdk_status=verifier_sdk_status,
        public_endpoint_enabled=public_endpoint_enabled,
        trust_registry_enabled=trust_registry_enabled,
        evidence_anchor_count=evidence_anchor_count,
        status=status,
    )


def seed_partner_registry() -> tuple[PartnerRegistryEntry, ...]:
    return (
        build_partner_registry_entry(
            partner_id="partner-city-ops",
            organization="City Mobility Operations",
            sector="government",
            region_id="mel-ap-southeast-2",
            integration_stage="sandbox onboarding",
            verifier_sdk_status="package shared",
            trust_registry_enabled=True,
            status="SANDBOX_ENABLED",
        ),
        build_partner_registry_entry(
            partner_id="partner-insure-1",
            organization="Trusted Claims Network",
            sector="insurance",
            region_id="jhb-af-south-1",
            integration_stage="staging verification",
            verifier_sdk_status="sdk integrated",
            public_endpoint_enabled=True,
            trust_registry_enabled=True,
            evidence_anchor_count=3,
            status="STAGING_ENABLED",
        ),
    )


__all__ = [
    "PartnerRegistryEntry",
    "PartnerRegistryStore",
    "build_partner_registry_entry",
    "seed_partner_registry",
]
