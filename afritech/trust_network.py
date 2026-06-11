"""Bounded AfriRide Trust Network registry and verification records."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from afritech.crypto.multi_party_verification import MultiPartyVerificationRecord
from afritech.partner_verification import PartnerVerificationPacket
from afritech.standards_dependency import (
    DependentSystemRecord,
    StandardConformanceProfile,
    build_standard_conformance_profile,
    dependency_manifest_hash,
)


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class TrustRegistryEntry:
    registry_id: str
    anchor_id: str
    publication_id: str
    network: str
    tenant_id: str
    region_id: str
    publication_target: str
    protocol_version: str
    standard_profile: str
    dependent_system_count: int
    dependency_manifest_hash: str
    packet_hash: str
    registry_hash: str
    authority_boundary: str = "registry_indexes_evidence_only"

    def canonical_dict(self) -> dict[str, str]:
        return {
            "schema": "afritech.trust_registry_entry.v1",
            "registry_id": self.registry_id,
            "anchor_id": self.anchor_id,
            "publication_id": self.publication_id,
            "network": self.network,
            "tenant_id": self.tenant_id,
            "region_id": self.region_id,
            "publication_target": self.publication_target,
            "protocol_version": self.protocol_version,
            "standard_profile": self.standard_profile,
            "dependent_system_count": self.dependent_system_count,
            "dependency_manifest_hash": self.dependency_manifest_hash,
            "packet_hash": self.packet_hash,
            "registry_hash": self.registry_hash,
            "authority_boundary": self.authority_boundary,
        }


@dataclass(frozen=True)
class TrustNetworkVerification:
    verification_network_id: str
    anchor_id: str
    aggregate_status: str
    quorum: int
    witness_count: int
    verified_count: int
    protocol_version: str
    standard_profile: str
    dependent_system_count: int
    dependency_manifest_hash: str
    network_hash: str
    authority_boundary: str = "verification_network_records_alignment_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.trust_network_verification.v1",
            "verification_network_id": self.verification_network_id,
            "anchor_id": self.anchor_id,
            "aggregate_status": self.aggregate_status,
            "quorum": self.quorum,
            "witness_count": self.witness_count,
            "verified_count": self.verified_count,
            "protocol_version": self.protocol_version,
            "standard_profile": self.standard_profile,
            "dependent_system_count": self.dependent_system_count,
            "dependency_manifest_hash": self.dependency_manifest_hash,
            "network_hash": self.network_hash,
            "authority_boundary": self.authority_boundary,
        }


class TrustRegistryStore:
    """Small in-memory trust registry for partner-facing publication lookups."""

    def __init__(self, entries: tuple[TrustRegistryEntry, ...] = ()) -> None:
        self._entries = {entry.anchor_id: entry for entry in entries}

    def publish(self, entry: TrustRegistryEntry) -> None:
        self._entries[entry.anchor_id] = entry

    def list_entries(self) -> tuple[TrustRegistryEntry, ...]:
        return tuple(sorted(self._entries.values(), key=lambda entry: entry.anchor_id))

    def load(self, anchor_id: str) -> TrustRegistryEntry:
        if anchor_id not in self._entries:
            raise KeyError(anchor_id)
        return self._entries[anchor_id]


def publish_trust_registry_entry(
    packet: PartnerVerificationPacket,
    dependents: tuple[DependentSystemRecord, ...] = (),
    profile: StandardConformanceProfile | None = None,
) -> TrustRegistryEntry:
    resolved_profile = profile or build_standard_conformance_profile()
    packet_hash = _canonical_hash(packet.canonical_dict())
    manifest_hash = dependency_manifest_hash(dependents)
    registry_hash = _canonical_hash(
        {
            "anchor_id": packet.anchor_id,
            "publication_id": packet.publication_id,
            "network": packet.network,
            "packet_hash": packet_hash,
            "profile_hash": resolved_profile.profile_hash,
            "dependency_manifest_hash": manifest_hash,
        }
    )
    return TrustRegistryEntry(
        registry_id=f"registry-{registry_hash[:12]}",
        anchor_id=packet.anchor_id,
        publication_id=packet.publication_id,
        network=packet.network,
        tenant_id=packet.tenant_id,
        region_id=packet.region_id,
        publication_target=packet.publication_target,
        protocol_version=resolved_profile.protocol_version,
        standard_profile=resolved_profile.profile_id,
        dependent_system_count=len(dependents),
        dependency_manifest_hash=manifest_hash,
        packet_hash=packet_hash,
        registry_hash=registry_hash,
    )


def build_trust_network_verification(
    record: MultiPartyVerificationRecord,
    dependents: tuple[DependentSystemRecord, ...] = (),
    profile: StandardConformanceProfile | None = None,
) -> TrustNetworkVerification:
    resolved_profile = profile or build_standard_conformance_profile()
    manifest_hash = dependency_manifest_hash(dependents)
    network_hash = _canonical_hash(record.canonical_dict())
    return TrustNetworkVerification(
        verification_network_id=f"tnv-{network_hash[:12]}",
        anchor_id=record.anchor_id,
        aggregate_status=record.aggregate_status,
        quorum=record.quorum,
        witness_count=record.witness_count,
        verified_count=record.verified_count,
        protocol_version=resolved_profile.protocol_version,
        standard_profile=resolved_profile.profile_id,
        dependent_system_count=len(dependents),
        dependency_manifest_hash=manifest_hash,
        network_hash=network_hash,
    )


__all__ = [
    "TrustNetworkVerification",
    "TrustRegistryEntry",
    "TrustRegistryStore",
    "build_trust_network_verification",
    "publish_trust_registry_entry",
]
