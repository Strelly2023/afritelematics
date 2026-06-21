from __future__ import annotations

from hashlib import sha256
from typing import Any


class NovaScriptStandardProfile:
    def profile(self) -> dict[str, Any]:
        family = self.family()
        controls = [
            "policy_dsl",
            "governance_receipts",
            "certificate_chain",
            "federation_consensus",
            "continuous_assurance",
            "evidence_retention",
            "external_audit_verification",
        ]
        return {
            "mode": "novascript_trust_standard",
            "standard_id": "NOVASCRIPT-TRUST-STD-001",
            "version": "v1",
            "classification": "proof_governed_engineering_trust_standard",
            "controls": controls,
            "standards_family": family,
            "standard_hash": sha256(":".join(controls).encode("utf-8")).hexdigest(),
        }

    def family(self) -> list[dict[str, Any]]:
        standards = [
            ("NOVASCRIPT-TRUST-STD-001", "trust_infrastructure"),
            ("NOVASCRIPT-RECEIPT-STD-001", "governance_receipts"),
            ("NOVASCRIPT-CERT-STD-001", "certificate_chains"),
            ("NOVASCRIPT-AUDIT-STD-001", "external_audit_packages"),
            ("NOVASCRIPT-FEDERATION-STD-001", "trust_exchange"),
            ("NOVASCRIPT-ASSURANCE-STD-001", "continuous_assurance"),
        ]
        return [
            {
                "standard_id": standard_id,
                "domain": domain,
                "status": "active",
                "standard_hash": sha256(f"{standard_id}:{domain}:active".encode()).hexdigest(),
            }
            for standard_id, domain in standards
        ]


class PlatformIntegrationRegistry:
    def __init__(self) -> None:
        self._integrations: dict[str, dict[str, Any]] = {}

    def register(
        self,
        *,
        organization_id: str,
        integration_name: str,
        integration_type: str,
        scopes: list[str],
    ) -> dict[str, Any]:
        integration_hash = sha256(
            f"{organization_id}:{integration_name}:{integration_type}:{','.join(sorted(scopes))}".encode()
        ).hexdigest()
        record = {
            "mode": "platform_plugin_registry",
            "integration_id": "plugin-" + integration_hash[:12],
            "organization_id": organization_id,
            "integration_name": integration_name,
            "integration_type": integration_type,
            "scopes": sorted(scopes),
            "status": "active",
            "integration_hash": integration_hash,
        }
        self._integrations[record["integration_id"]] = record
        return record

    def list(self, *, organization_id: str | None = None) -> list[dict[str, Any]]:
        records = list(self._integrations.values())
        if organization_id is not None:
            records = [record for record in records if record["organization_id"] == organization_id]
        return sorted(records, key=lambda item: item["integration_id"])


class FieldAdoptionRegistry:
    def __init__(self) -> None:
        self._organizations: dict[str, dict[str, Any]] = {}
        self._certifications: dict[str, dict[str, Any]] = {}

    def onboard(
        self,
        *,
        organization_id: str,
        legal_name: str,
        sector: str,
        trust_domain: str,
    ) -> dict[str, Any]:
        adoption_hash = sha256(f"{organization_id}:{legal_name}:{sector}:{trust_domain}".encode()).hexdigest()
        record = {
            "mode": "field_adoption_registry",
            "adoption_id": "adopt-" + adoption_hash[:12],
            "organization_id": organization_id,
            "legal_name": legal_name,
            "sector": sector,
            "trust_domain": trust_domain,
            "status": "pilot_ready",
            "adoption_hash": adoption_hash,
        }
        self._organizations[organization_id] = record
        return record

    def certify(
        self,
        *,
        organization_id: str,
        trust_score: int,
        evidence_count: int,
        audit_verified: bool,
    ) -> dict[str, Any]:
        if trust_score >= 90 and evidence_count >= 2 and audit_verified:
            level = 3
            label = "NovaScript Certified"
        elif trust_score >= 75 and evidence_count >= 1:
            level = 2
            label = "NovaScript Trusted"
        else:
            level = 1
            label = "NovaScript Verified"
        certification_hash = sha256(f"{organization_id}:{level}:{trust_score}:{evidence_count}:{audit_verified}".encode()).hexdigest()
        record = {
            "mode": "adoption_certification_program",
            "certification_id": "nscert-" + certification_hash[:12],
            "organization_id": organization_id,
            "level": level,
            "label": label,
            "requirements": ["receipt_verified", "certificate_chain_present", "production_evidence_recorded"],
            "certification_hash": certification_hash,
        }
        self._certifications[organization_id] = record
        return record

    def status(self) -> dict[str, Any]:
        return {
            "mode": "field_adoption_status",
            "organization_count": len(self._organizations),
            "organizations": sorted(self._organizations.values(), key=lambda item: item["organization_id"]),
            "certifications": sorted(self._certifications.values(), key=lambda item: item["organization_id"]),
        }


class ProductionEvidenceRegistry:
    def __init__(self) -> None:
        self._evidence: dict[tuple[str, str], list[dict[str, Any]]] = {}

    def record(
        self,
        *,
        organization_id: str,
        project_id: str,
        environment: str,
        evidence_type: str,
        validation_status: str,
        evidence_hash: str | None = None,
    ) -> dict[str, Any]:
        key = (organization_id, project_id)
        sequence = len(self._evidence.get(key, [])) + 1
        digest = evidence_hash or sha256(
            f"{organization_id}:{project_id}:{environment}:{evidence_type}:{validation_status}:{sequence}".encode()
        ).hexdigest()
        record = {
            "mode": "production_evidence_registry",
            "evidence_id": "prodev-" + digest[:12],
            "sequence": sequence,
            "organization_id": organization_id,
            "project_id": project_id,
            "environment": environment,
            "evidence_type": evidence_type,
            "validation_status": validation_status,
            "evidence_hash": digest,
            "verified": validation_status in {"validated", "passed", "verified"},
        }
        self._evidence.setdefault(key, []).append(record)
        return record

    def snapshot(self, *, organization_id: str, project_id: str) -> dict[str, Any]:
        records = self._evidence.get((organization_id, project_id), [])
        verified = [record for record in records if record["verified"]]
        return {
            "mode": "real_production_evidence",
            "organization_id": organization_id,
            "project_id": project_id,
            "evidence_count": len(records),
            "verified_count": len(verified),
            "recent": records[-10:],
        }


class ExternalAuditMarketplace:
    def package(
        self,
        *,
        organization_id: str,
        project_id: str,
        receipt: dict[str, Any],
        certificate_chain: dict[str, Any],
        assurance_report: dict[str, Any],
        production_evidence: dict[str, Any],
    ) -> dict[str, Any]:
        package_hash = sha256(
            (
                f"{organization_id}:{project_id}:{receipt.get('receipt_id')}:"
                f"{certificate_chain.get('chain_hash')}:{assurance_report.get('report_hash')}:"
                f"{production_evidence.get('verified_count')}"
            ).encode()
        ).hexdigest()
        return {
            "mode": "external_audit_marketplace_package",
            "audit_package_id": "auditpkg-" + package_hash[:12],
            "organization_id": organization_id,
            "project_id": project_id,
            "receipt_id": receipt.get("receipt_id"),
            "certificate_chain_hash": certificate_chain.get("chain_hash"),
            "assurance_report_id": assurance_report.get("report_id"),
            "production_evidence_verified": production_evidence.get("verified_count", 0),
            "sellable_verification": True,
            "package_hash": package_hash,
        }


_DEFAULT_STANDARD = NovaScriptStandardProfile()
_DEFAULT_INTEGRATIONS = PlatformIntegrationRegistry()
_DEFAULT_ADOPTION = FieldAdoptionRegistry()
_DEFAULT_PRODUCTION_EVIDENCE = ProductionEvidenceRegistry()
_DEFAULT_AUDIT_MARKETPLACE = ExternalAuditMarketplace()


def get_novascript_standard_profile() -> NovaScriptStandardProfile:
    return _DEFAULT_STANDARD


def get_platform_integration_registry() -> PlatformIntegrationRegistry:
    return _DEFAULT_INTEGRATIONS


def get_field_adoption_registry() -> FieldAdoptionRegistry:
    return _DEFAULT_ADOPTION


def get_production_evidence_registry() -> ProductionEvidenceRegistry:
    return _DEFAULT_PRODUCTION_EVIDENCE


def get_external_audit_marketplace() -> ExternalAuditMarketplace:
    return _DEFAULT_AUDIT_MARKETPLACE
