"""In-memory partner certification registry for ecosystem onboarding."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from afritech.architecture.novaride_architecture import (
    NOVARIDE_ARCHITECTURE_SUPPORTED_VERSIONS,
    novaride_architecture_signed_publication,
    novaride_architecture_sdks,
    verify_novaride_architecture_contract,
)
from afritech.security.architecture_signing import verify_architecture_signature


CERTIFICATION_STATUSES = frozenset({"PENDING", "CERTIFIED", "REJECTED"})


@dataclass(frozen=True)
class PartnerCertificationRecord:
    partner_id: str
    certificate_id: str
    status: str
    certified_at: str | None
    supported_versions: tuple[str, ...]
    capabilities: tuple[str, ...]
    sdk_language: str | None
    verification: dict[str, Any]
    authority_boundary: str = "partner_certification_indexes_adoption_and_compatibility_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.partner_certification_record.v1",
            "partner_id": self.partner_id,
            "certificate_id": self.certificate_id,
            "status": self.status,
            "certified_at": self.certified_at,
            "supported_versions": list(self.supported_versions),
            "capabilities": list(self.capabilities),
            "sdk_language": self.sdk_language,
            "verification": dict(self.verification),
            "authority_boundary": self.authority_boundary,
        }


class PartnerCertificationStore:
    """Small in-memory certification registry used for ecosystem onboarding."""

    def __init__(self, entries: tuple[PartnerCertificationRecord, ...] = ()) -> None:
        self._entries = {entry.partner_id: entry for entry in entries}

    def register(self, entry: PartnerCertificationRecord) -> None:
        self._entries[entry.partner_id] = entry

    def list_entries(self) -> tuple[PartnerCertificationRecord, ...]:
        return tuple(sorted(self._entries.values(), key=lambda entry: entry.partner_id))

    def load(self, partner_id: str) -> PartnerCertificationRecord:
        if partner_id not in self._entries:
            raise KeyError(partner_id)
        return self._entries[partner_id]

    def certify(
        self,
        partner_id: str,
        *,
        supported_versions: tuple[str, ...],
        capabilities: tuple[str, ...],
        sdk_language: str | None = None,
    ) -> PartnerCertificationRecord:
        publication = novaride_architecture_signed_publication()
        signature = publication["signature"]
        signature_valid = verify_architecture_signature(publication["contract"], signature)
        contract_verification = verify_novaride_architecture_contract(
            publication["contract"]["requested_version"],
            publication["contract"]["schema_hash"],
            list(capabilities),
        )
        sdk_targets = {target["language"] for target in novaride_architecture_sdks()["targets"]}
        sdk_compatibility_valid = sdk_language in sdk_targets if sdk_language is not None else True
        supported_versions_valid = all(
            version in NOVARIDE_ARCHITECTURE_SUPPORTED_VERSIONS for version in supported_versions
        )
        status = "CERTIFIED" if (
            signature_valid
            and contract_verification["valid"]
            and supported_versions_valid
            and sdk_compatibility_valid
        ) else "PENDING"
        certified_at = datetime.now(UTC).isoformat() if status == "CERTIFIED" else None
        record = PartnerCertificationRecord(
            partner_id=partner_id,
            certificate_id=f"cert-{uuid4().hex[:16]}",
            status=status,
            certified_at=certified_at,
            supported_versions=supported_versions,
            capabilities=capabilities,
            sdk_language=sdk_language,
            verification={
                "architecture_version": publication["contract"]["version"],
                "signature_valid": signature_valid,
                "contract_valid": contract_verification["valid"],
                "capabilities_valid": contract_verification["capabilities_valid"],
                "supported_versions_valid": supported_versions_valid,
                "sdk_compatibility_valid": sdk_compatibility_valid,
                "checked_at": datetime.now(UTC).isoformat(),
            },
        )
        self.register(record)
        return record


def build_partner_certification_record(
    *,
    partner_id: str,
    supported_versions: tuple[str, ...],
    capabilities: tuple[str, ...] = (),
    sdk_language: str | None = None,
) -> PartnerCertificationRecord:
    if not partner_id.strip():
        raise ValueError("partner_id required")
    if not supported_versions:
        raise ValueError("supported_versions required")
    return PartnerCertificationRecord(
        partner_id=partner_id,
        certificate_id=f"cert-{uuid4().hex[:16]}",
        status="PENDING",
        certified_at=None,
        supported_versions=supported_versions,
        capabilities=capabilities,
        sdk_language=sdk_language,
        verification={
            "architecture_version": novaride_architecture_signed_publication()["contract"]["version"],
            "signature_valid": False,
            "contract_valid": False,
            "capabilities_valid": False,
            "supported_versions_valid": False,
            "sdk_compatibility_valid": False,
            "checked_at": datetime.now(UTC).isoformat(),
        },
    )


def seed_partner_certification_registry() -> tuple[PartnerCertificationRecord, ...]:
    return ()


__all__ = [
    "CERTIFICATION_STATUSES",
    "PartnerCertificationRecord",
    "PartnerCertificationStore",
    "build_partner_certification_record",
    "seed_partner_certification_registry",
]
