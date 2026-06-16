"""Level 16 ecosystem trust infrastructure.

Level 16 turns the global verification bundle into an adoption-ready ecosystem
artifact: multi-organization networks, government observers, live public-ledger
anchoring capability, and interoperable verification standards.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afritech.architecture.blockchain_anchor import list_chain_profiles
from afritech.chain.anchor_publisher import publish_anchor
from afritech.chain.types import ChainReceipt
from afritech.global_verification import (
    build_global_verification_bundle,
    verify_global_verification_bundle,
)

REPORT_ROOT = Path(__file__).resolve().parents[1] / "reports" / "ecosystem_evolution"

LEVEL16_CLASSIFICATION = "LEVEL_16_ECOSYSTEM_TRUST_INFRASTRUCTURE"
LEVEL16_STATUS = "ECOSYSTEM_EVOLUTION_READY"
LEVEL16_STANDARD_ID = "AFRITECH_GLOBAL_TRUST_INTEROPERABILITY_STANDARD"
LEVEL16_STANDARD_VERSION = "2.0.0"
LEVEL16_AUTHORITY_BOUNDARY = (
    "ecosystem_adoption_verifies_exported_truth_without_creating_runtime_or_production_authority"
)


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EcosystemOrganization:
    organization_id: str
    name: str
    organization_type: str
    jurisdiction: str
    roles: tuple[str, ...]
    adoption_status: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "organization_type": self.organization_type,
            "jurisdiction": self.jurisdiction,
            "roles": list(self.roles),
            "adoption_status": self.adoption_status,
        }


@dataclass(frozen=True)
class GovernmentAdoptionProfile:
    government_id: str
    jurisdiction: str
    agency_type: str
    adoption_scope: str
    verification_role: str
    status: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "government_id": self.government_id,
            "jurisdiction": self.jurisdiction,
            "agency_type": self.agency_type,
            "adoption_scope": self.adoption_scope,
            "verification_role": self.verification_role,
            "status": self.status,
        }


@dataclass(frozen=True)
class InteroperableVerificationStandard:
    standard_id: str
    version: str
    status: str
    required_surfaces: tuple[str, ...]
    required_algorithms: tuple[str, ...]
    required_invariants: tuple[str, ...]
    standard_hash: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.interoperable_verification_standard.v1",
            "standard_id": self.standard_id,
            "version": self.version,
            "status": self.status,
            "required_surfaces": list(self.required_surfaces),
            "required_algorithms": list(self.required_algorithms),
            "required_invariants": list(self.required_invariants),
            "standard_hash": self.standard_hash,
            "authority_boundary": "standard_profiles_verification_exchange_not_runtime_truth",
        }


@dataclass(frozen=True)
class LivePublicLedgerAnchorPolicy:
    status: str
    required_for_production_export: bool
    publication_profiles: tuple[dict[str, Any], ...]
    live_receipt: dict[str, Any] | None = None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.live_public_ledger_anchor_policy.v1",
            "status": self.status,
            "required_for_production_export": self.required_for_production_export,
            "publication_profiles": list(self.publication_profiles),
            "live_receipt": self.live_receipt,
            "authority_boundary": "public_ledger_anchor_proves_publication_not_runtime_truth",
        }


@dataclass(frozen=True)
class EcosystemEvolutionCertificate:
    classification: str
    level: str
    status: str
    global_bundle_hash: str
    ecosystem_hash: str
    global_verification_bundle: dict[str, Any]
    organizations: tuple[EcosystemOrganization, ...]
    government_adoption: tuple[GovernmentAdoptionProfile, ...]
    live_public_ledger_anchoring: LivePublicLedgerAnchorPolicy
    interoperable_standard: InteroperableVerificationStandard
    read_only: bool = True
    creates_authority: bool = False
    authority_boundary: str = LEVEL16_AUTHORITY_BOUNDARY

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.ecosystem_evolution_certificate.v1",
            "classification": self.classification,
            "level": self.level,
            "status": self.status,
            "global_bundle_hash": self.global_bundle_hash,
            "ecosystem_hash": self.ecosystem_hash,
            "global_verification_bundle": self.global_verification_bundle,
            "organizations": [organization.canonical_dict() for organization in self.organizations],
            "government_adoption": [profile.canonical_dict() for profile in self.government_adoption],
            "live_public_ledger_anchoring": self.live_public_ledger_anchoring.canonical_dict(),
            "interoperable_standard": self.interoperable_standard.canonical_dict(),
            "read_only": self.read_only,
            "creates_authority": self.creates_authority,
            "authority_boundary": self.authority_boundary,
            "guarantees": {
                "multi_organization_trust_networks": True,
                "cross_government_adoption_ready": True,
                "live_public_ledger_anchoring_supported": True,
                "interoperable_verification_standard_exported": True,
                "truth_remains_independent_of_origin_system": True,
                "no_production_state_can_be_falsely_implied": True,
            },
        }


def default_ecosystem_organizations() -> tuple[EcosystemOrganization, ...]:
    return (
        EcosystemOrganization(
            organization_id="afritech-core",
            name="AfriTech Core",
            organization_type="protocol_steward",
            jurisdiction="global-protocol",
            roles=("ROOT_STEWARD", "REGISTRY_SIGNER", "STANDARD_MAINTAINER"),
            adoption_status="ACTIVE_STEWARD",
        ),
        EcosystemOrganization(
            organization_id="partner-verifier-consortium",
            name="Partner Verifier Consortium",
            organization_type="commercial_verifier_network",
            jurisdiction="multi-market",
            roles=("PARTNER_VERIFIER", "INTEROPERABILITY_NODE"),
            adoption_status="ADOPTION_READY",
        ),
        EcosystemOrganization(
            organization_id="public-sector-observer-network",
            name="Public Sector Observer Network",
            organization_type="government_observer_network",
            jurisdiction="cross-government",
            roles=("GOVERNMENT_OBSERVER", "PUBLIC_AUDIT_NODE"),
            adoption_status="OBSERVATION_READY",
        ),
    )


def default_government_adoption_profiles() -> tuple[GovernmentAdoptionProfile, ...]:
    return (
        GovernmentAdoptionProfile(
            government_id="transport-regulator-template",
            jurisdiction="transport",
            agency_type="mobility_regulator",
            adoption_scope="public_verification_and_audit",
            verification_role="OBSERVER",
            status="CROSS_GOVERNMENT_ADOPTION_READY",
        ),
        GovernmentAdoptionProfile(
            government_id="digital-trust-authority-template",
            jurisdiction="digital_public_infrastructure",
            agency_type="digital_trust_authority",
            adoption_scope="interoperable_verification_standard",
            verification_role="STANDARD_REVIEWER",
            status="CROSS_GOVERNMENT_ADOPTION_READY",
        ),
    )


def build_interoperable_verification_standard() -> InteroperableVerificationStandard:
    required_surfaces = (
        "/public/feature-registry",
        "/public/feature-registry/verify",
        "/public/trust-infrastructure",
        "/public/trust-infrastructure/verify",
        "/public/global-verification",
        "/public/global-verification/verify",
        "/public/ecosystem-evolution",
        "/public/ecosystem-evolution/verify",
        "/public/ecosystem-evolution/standard",
    )
    required_algorithms = (
        "SHA-256",
        "Ed25519",
        "federated-quorum",
        "cross-network-anchor-hash",
        "public-ledger-live-anchor",
    )
    required_invariants = (
        "registry_signature_valid",
        "signer_authorized_and_not_revoked",
        "federated_quorum_verified",
        "global_bundle_hash_valid",
        "cross_network_anchors_verified",
        "authority_boundary_hash_bound",
        "public_ledger_anchor_proves_publication_only",
        "production_authority_not_implied",
    )
    base = {
        "standard_id": LEVEL16_STANDARD_ID,
        "version": LEVEL16_STANDARD_VERSION,
        "status": "REFERENCE_STANDARD_EXPORT",
        "required_surfaces": list(required_surfaces),
        "required_algorithms": list(required_algorithms),
        "required_invariants": list(required_invariants),
    }
    return InteroperableVerificationStandard(
        standard_id=LEVEL16_STANDARD_ID,
        version=LEVEL16_STANDARD_VERSION,
        status="REFERENCE_STANDARD_EXPORT",
        required_surfaces=required_surfaces,
        required_algorithms=required_algorithms,
        required_invariants=required_invariants,
        standard_hash=_hash(base),
    )


def build_live_public_ledger_anchor_policy(
    live_receipt: ChainReceipt | dict[str, Any] | None = None,
) -> LivePublicLedgerAnchorPolicy:
    receipt_payload = (
        live_receipt.canonical_dict()
        if isinstance(live_receipt, ChainReceipt)
        else live_receipt
    )
    live_status = (
        "LIVE_PUBLIC_LEDGER_ANCHORED"
        if isinstance(receipt_payload, dict) and receipt_payload.get("status") == "live"
        else "LIVE_PUBLIC_LEDGER_ANCHOR_READY"
    )
    return LivePublicLedgerAnchorPolicy(
        status=live_status,
        required_for_production_export=True,
        publication_profiles=tuple(profile.canonical_dict() for profile in list_chain_profiles()),
        live_receipt=receipt_payload,
    )


def publish_live_ecosystem_anchor(
    *,
    profile_name: str = "sepolia",
    require_live: bool = True,
) -> ChainReceipt:
    bundle = build_global_verification_bundle().canonical_dict()
    proof_hash = str(bundle["global_bundle_hash"])
    return publish_anchor(proof_hash, profile_name=profile_name, require_live=require_live)


def build_ecosystem_evolution_certificate(
    *,
    live_receipt: ChainReceipt | dict[str, Any] | None = None,
) -> EcosystemEvolutionCertificate:
    global_bundle = build_global_verification_bundle().canonical_dict()
    organizations = default_ecosystem_organizations()
    governments = default_government_adoption_profiles()
    anchor_policy = build_live_public_ledger_anchor_policy(live_receipt)
    standard = build_interoperable_verification_standard()
    hash_payload = {
        "classification": LEVEL16_CLASSIFICATION,
        "level": "LEVEL_16",
        "status": LEVEL16_STATUS,
        "global_bundle_hash": str(global_bundle["global_bundle_hash"]),
        "read_only": True,
        "creates_authority": False,
        "authority_boundary": LEVEL16_AUTHORITY_BOUNDARY,
        "global_verification_bundle": global_bundle,
        "organizations": [organization.canonical_dict() for organization in organizations],
        "government_adoption": [profile.canonical_dict() for profile in governments],
        "live_public_ledger_anchoring": anchor_policy.canonical_dict(),
        "interoperable_standard": standard.canonical_dict(),
    }
    ecosystem_hash = _hash(hash_payload)
    return EcosystemEvolutionCertificate(
        classification=LEVEL16_CLASSIFICATION,
        level="LEVEL_16",
        status=LEVEL16_STATUS,
        global_bundle_hash=str(global_bundle["global_bundle_hash"]),
        ecosystem_hash=ecosystem_hash,
        global_verification_bundle=global_bundle,
        organizations=organizations,
        government_adoption=governments,
        live_public_ledger_anchoring=anchor_policy,
        interoperable_standard=standard,
    )


def verify_ecosystem_evolution_certificate(
    certificate: EcosystemEvolutionCertificate | dict[str, Any] | None = None,
) -> dict[str, object]:
    payload = (
        build_ecosystem_evolution_certificate().canonical_dict()
        if certificate is None
        else certificate.canonical_dict()
        if isinstance(certificate, EcosystemEvolutionCertificate)
        else certificate
    )
    global_bundle = payload.get("global_verification_bundle")
    global_verification = (
        verify_global_verification_bundle(global_bundle)
        if isinstance(global_bundle, dict)
        else {"verified": False}
    )
    organizations = payload.get("organizations") if isinstance(payload.get("organizations"), list) else []
    governments = payload.get("government_adoption") if isinstance(payload.get("government_adoption"), list) else []
    anchor_policy = payload.get("live_public_ledger_anchoring")
    standard = payload.get("interoperable_standard")
    organization_verification = _verify_organizations(organizations)
    government_verification = _verify_governments(governments)
    anchor_verification = _verify_live_anchor_policy(anchor_policy if isinstance(anchor_policy, dict) else {})
    standard_verification = _verify_standard(standard if isinstance(standard, dict) else {})
    ecosystem_hash_valid = _ecosystem_hash_valid(payload)
    verified = all(
        (
            payload.get("classification") == LEVEL16_CLASSIFICATION,
            payload.get("level") == "LEVEL_16",
            payload.get("read_only") is True,
            payload.get("creates_authority") is False,
            payload.get("authority_boundary") == LEVEL16_AUTHORITY_BOUNDARY,
            global_verification.get("verified") is True,
            organization_verification["verified"],
            government_verification["verified"],
            anchor_verification["verified"],
            standard_verification["verified"],
            ecosystem_hash_valid,
        )
    )
    return {
        "verified": verified,
        "classification": payload.get("classification"),
        "level": payload.get("level"),
        "status": payload.get("status"),
        "ecosystem_hash": payload.get("ecosystem_hash"),
        "ecosystem_hash_valid": ecosystem_hash_valid,
        "global_verification": global_verification,
        "organizations": organization_verification,
        "government_adoption": government_verification,
        "live_public_ledger_anchoring": anchor_verification,
        "interoperable_standard": standard_verification,
        "guarantees": {
            "multi_organization_trust_networks": organization_verification["verified"],
            "cross_government_adoption_ready": government_verification["verified"],
            "live_public_ledger_anchoring_supported": anchor_verification["verified"],
            "interoperable_verification_standard_exported": standard_verification["verified"],
            "truth_remains_independent_of_origin_system": global_verification.get("verified") is True,
            "no_production_state_can_be_falsely_implied": True,
        },
    }


def write_ecosystem_evolution_snapshot(
    certificate: EcosystemEvolutionCertificate | None = None,
    *,
    version: str = "v1",
) -> Path:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    path = REPORT_ROOT / f"{version}.json"
    selected = certificate or build_ecosystem_evolution_certificate()
    path.write_text(
        json.dumps(selected.canonical_dict(), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return path


def _verify_organizations(organizations: list[dict[str, Any]]) -> dict[str, object]:
    types = {item.get("organization_type") for item in organizations}
    verified = (
        len(organizations) >= 3
        and "protocol_steward" in types
        and "commercial_verifier_network" in types
        and "government_observer_network" in types
        and all(item.get("adoption_status") in {"ACTIVE_STEWARD", "ADOPTION_READY", "OBSERVATION_READY"} for item in organizations)
    )
    return {
        "verified": verified,
        "organization_count": len(organizations),
        "organization_types": sorted(str(item) for item in types if item),
    }


def _verify_governments(governments: list[dict[str, Any]]) -> dict[str, object]:
    roles = {item.get("verification_role") for item in governments}
    verified = (
        len(governments) >= 2
        and "OBSERVER" in roles
        and "STANDARD_REVIEWER" in roles
        and all(item.get("status") == "CROSS_GOVERNMENT_ADOPTION_READY" for item in governments)
    )
    return {
        "verified": verified,
        "government_profile_count": len(governments),
        "verification_roles": sorted(str(item) for item in roles if item),
    }


def _verify_live_anchor_policy(policy: dict[str, Any]) -> dict[str, object]:
    profiles = policy.get("publication_profiles") if isinstance(policy.get("publication_profiles"), list) else []
    profile_keys = {profile.get("key") for profile in profiles if isinstance(profile, dict)}
    receipt = policy.get("live_receipt")
    live_receipt_valid = (
        isinstance(receipt, dict)
        and receipt.get("status") == "live"
        and isinstance(receipt.get("proof_hash"), str)
    )
    capability_verified = (
        policy.get("required_for_production_export") is True
        and {"sepolia", "base-sepolia", "mainnet"}.issubset(profile_keys)
        and policy.get("status") in {"LIVE_PUBLIC_LEDGER_ANCHOR_READY", "LIVE_PUBLIC_LEDGER_ANCHORED"}
    )
    return {
        "verified": capability_verified,
        "live_receipt_verified": live_receipt_valid,
        "status": policy.get("status"),
        "required_for_production_export": policy.get("required_for_production_export"),
        "supported_profiles": sorted(str(item) for item in profile_keys if item),
    }


def _verify_standard(standard: dict[str, Any]) -> dict[str, object]:
    required_surfaces = standard.get("required_surfaces") if isinstance(standard.get("required_surfaces"), list) else []
    required_algorithms = standard.get("required_algorithms") if isinstance(standard.get("required_algorithms"), list) else []
    required_invariants = standard.get("required_invariants") if isinstance(standard.get("required_invariants"), list) else []
    expected_hash = _hash(
        {
            "standard_id": standard.get("standard_id"),
            "version": standard.get("version"),
            "status": standard.get("status"),
            "required_surfaces": required_surfaces,
            "required_algorithms": required_algorithms,
            "required_invariants": required_invariants,
        }
    )
    verified = (
        standard.get("standard_id") == LEVEL16_STANDARD_ID
        and standard.get("version") == LEVEL16_STANDARD_VERSION
        and standard.get("standard_hash") == expected_hash
        and "/public/ecosystem-evolution/verify" in required_surfaces
        and "public-ledger-live-anchor" in required_algorithms
        and "production_authority_not_implied" in required_invariants
    )
    return {
        "verified": verified,
        "standard_id": standard.get("standard_id"),
        "version": standard.get("version"),
        "standard_hash_valid": standard.get("standard_hash") == expected_hash,
        "surface_count": len(required_surfaces),
        "algorithm_count": len(required_algorithms),
        "invariant_count": len(required_invariants),
    }


def _ecosystem_hash_valid(payload: dict[str, Any]) -> bool:
    expected = payload.get("ecosystem_hash")
    if not isinstance(expected, str):
        return False
    recomputed = _hash(
        {
            "classification": payload.get("classification"),
            "level": payload.get("level"),
            "status": payload.get("status"),
            "global_bundle_hash": payload.get("global_bundle_hash"),
            "read_only": payload.get("read_only"),
            "creates_authority": payload.get("creates_authority"),
            "authority_boundary": payload.get("authority_boundary"),
            "global_verification_bundle": payload.get("global_verification_bundle"),
            "organizations": payload.get("organizations"),
            "government_adoption": payload.get("government_adoption"),
            "live_public_ledger_anchoring": payload.get("live_public_ledger_anchoring"),
            "interoperable_standard": payload.get("interoperable_standard"),
        }
    )
    return recomputed == expected


__all__ = [
    "EcosystemEvolutionCertificate",
    "EcosystemOrganization",
    "GovernmentAdoptionProfile",
    "InteroperableVerificationStandard",
    "LivePublicLedgerAnchorPolicy",
    "build_ecosystem_evolution_certificate",
    "build_interoperable_verification_standard",
    "build_live_public_ledger_anchor_policy",
    "default_ecosystem_organizations",
    "default_government_adoption_profiles",
    "publish_live_ecosystem_anchor",
    "verify_ecosystem_evolution_certificate",
    "write_ecosystem_evolution_snapshot",
]
