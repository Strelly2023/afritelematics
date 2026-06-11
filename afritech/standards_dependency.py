"""Standard dependency and conformance records for multi-party protocol use."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


STANDARD_NAME = "AFRIRIDE_TRUST_PROTOCOL"
STANDARD_PROFILE = "MULTI_PARTY_REPLAY_VERIFICATION_V1"
STANDARD_VERSION = "1.0.0"
REQUIRED_SURFACES = (
    "POST /v1/partner/verify",
    "GET /v1/partner/anchors/{anchor_id}",
    "GET /v1/trust/registry",
    "POST /v1/trust/registry/publish",
    "POST /v1/trust/network/verify",
    "GET /v1/trust/standards/profile",
    "POST /v1/trust/dependents/register",
    "GET /v1/trust/dependents",
)


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class StandardConformanceProfile:
    standard_name: str
    profile_id: str
    protocol_version: str
    required_surfaces: tuple[str, ...]
    authority_boundary: str
    profile_hash: str
    standard_status: str = "REFERENCE_STANDARD"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.standard_conformance_profile.v1",
            "standard_name": self.standard_name,
            "profile_id": self.profile_id,
            "protocol_version": self.protocol_version,
            "required_surfaces": list(self.required_surfaces),
            "authority_boundary": self.authority_boundary,
            "profile_hash": self.profile_hash,
            "standard_status": self.standard_status,
        }


@dataclass(frozen=True)
class DependentSystemRecord:
    dependency_id: str
    dependent_id: str
    organization: str
    use_case: str
    protocol_version: str
    profile_id: str
    profile_hash: str
    required_surfaces: tuple[str, ...]
    dependency_hash: str
    status: str = "DECLARED_DEPENDENCY"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.dependent_system_record.v1",
            "dependency_id": self.dependency_id,
            "dependent_id": self.dependent_id,
            "organization": self.organization,
            "use_case": self.use_case,
            "protocol_version": self.protocol_version,
            "profile_id": self.profile_id,
            "profile_hash": self.profile_hash,
            "required_surfaces": list(self.required_surfaces),
            "dependency_hash": self.dependency_hash,
            "status": self.status,
        }


class StandardsDependencyStore:
    """Small in-memory store for systems declaring protocol dependence."""

    def __init__(self, records: tuple[DependentSystemRecord, ...] = ()) -> None:
        self._records = {record.dependent_id: record for record in records}

    def register(self, record: DependentSystemRecord) -> None:
        self._records[record.dependent_id] = record

    def list_records(self) -> tuple[DependentSystemRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: item.dependent_id))

    def load(self, dependent_id: str) -> DependentSystemRecord:
        if dependent_id not in self._records:
            raise KeyError(dependent_id)
        return self._records[dependent_id]


def build_standard_conformance_profile(
    *,
    protocol_version: str = STANDARD_VERSION,
    profile_id: str = STANDARD_PROFILE,
    standard_name: str = STANDARD_NAME,
    required_surfaces: tuple[str, ...] = REQUIRED_SURFACES,
) -> StandardConformanceProfile:
    payload = {
        "standard_name": standard_name,
        "profile_id": profile_id,
        "protocol_version": protocol_version,
        "required_surfaces": list(required_surfaces),
        "authority_boundary": "dependents_consume_verification_not_truth",
    }
    profile_hash = _canonical_hash(payload)
    return StandardConformanceProfile(
        standard_name=standard_name,
        profile_id=profile_id,
        protocol_version=protocol_version,
        required_surfaces=required_surfaces,
        authority_boundary="dependents_consume_verification_not_truth",
        profile_hash=profile_hash,
    )


def register_protocol_dependency(
    *,
    dependent_id: str,
    organization: str,
    use_case: str,
    protocol_version: str = STANDARD_VERSION,
    profile: StandardConformanceProfile | None = None,
    required_surfaces: tuple[str, ...] | None = None,
) -> DependentSystemRecord:
    if not dependent_id or not organization or not use_case:
        raise ValueError("dependent_id, organization, and use_case are required")
    resolved_profile = profile or build_standard_conformance_profile(
        protocol_version=protocol_version
    )
    resolved_surfaces = required_surfaces or resolved_profile.required_surfaces
    if not resolved_surfaces:
        raise ValueError("at least one required surface is required")
    dependency_hash = _canonical_hash(
        {
            "dependent_id": dependent_id,
            "organization": organization,
            "use_case": use_case,
            "protocol_version": protocol_version,
            "profile_hash": resolved_profile.profile_hash,
            "required_surfaces": list(resolved_surfaces),
        }
    )
    return DependentSystemRecord(
        dependency_id=f"dep-{dependency_hash[:12]}",
        dependent_id=dependent_id,
        organization=organization,
        use_case=use_case,
        protocol_version=protocol_version,
        profile_id=resolved_profile.profile_id,
        profile_hash=resolved_profile.profile_hash,
        required_surfaces=resolved_surfaces,
        dependency_hash=dependency_hash,
    )


def dependency_manifest_hash(records: tuple[DependentSystemRecord, ...]) -> str:
    return _canonical_hash(
        {
            "dependencies": [record.canonical_dict() for record in records],
        }
    )


__all__ = [
    "DependentSystemRecord",
    "STANDARD_NAME",
    "STANDARD_PROFILE",
    "STANDARD_VERSION",
    "StandardConformanceProfile",
    "StandardsDependencyStore",
    "build_standard_conformance_profile",
    "dependency_manifest_hash",
    "register_protocol_dependency",
]
