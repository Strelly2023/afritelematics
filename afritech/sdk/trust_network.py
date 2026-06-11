from __future__ import annotations

from typing import Any

from afritech.crypto.multi_party_verification import (
    VerificationWitness,
    build_multi_party_verification_record,
)
from afritech.partner_verification import build_partner_verification_packet
from afritech.standards_dependency import (
    build_standard_conformance_profile,
    register_protocol_dependency,
)
from afritech.trust_network import (
    build_trust_network_verification,
    publish_trust_registry_entry,
)


class TrustNetworkClient:
    def standards_profile(self) -> dict[str, Any]:
        return build_standard_conformance_profile().canonical_dict()

    def prepare_dependency_request(
        self,
        *,
        dependent_id: str,
        organization: str,
        use_case: str,
        protocol_version: str = "1.0.0",
    ) -> dict[str, Any]:
        return {
            "dependent_id": dependent_id,
            "organization": organization,
            "use_case": use_case,
            "protocol_version": protocol_version,
        }

    def register_dependency_locally(self, payload: dict[str, Any]) -> dict[str, Any]:
        return register_protocol_dependency(
            dependent_id=str(payload["dependent_id"]),
            organization=str(payload["organization"]),
            use_case=str(payload["use_case"]),
            protocol_version=str(payload.get("protocol_version", "1.0.0")),
        ).canonical_dict()

    def publish_registry_locally(
        self,
        *,
        partner_payload: dict[str, Any],
        dependents: tuple[dict[str, Any], ...] = (),
    ) -> dict[str, Any]:
        packet = build_partner_verification_packet(
            tenant_id=str(partner_payload["tenant_id"]),
            region_id=str(partner_payload["region_id"]),
            trace_hash=str(partner_payload["trace_hash"]),
            replay_hash=str(partner_payload["replay_hash"]),
            receipt_hash=str(partner_payload["receipt_hash"]),
            authority_hash=str(partner_payload["authority_hash"]),
            execution_fingerprint=str(partner_payload["execution_fingerprint"]),
            publication_target=str(partner_payload["publication_target"]),
            network=str(partner_payload.get("network", "external-ledger-testnet")),
            publisher_id=str(partner_payload.get("publisher_id", "afritech-anchor-publisher")),
            external_reference=partner_payload.get("external_reference"),
        )
        dependent_records = tuple(
            register_protocol_dependency(
                dependent_id=str(item["dependent_id"]),
                organization=str(item["organization"]),
                use_case=str(item["use_case"]),
                protocol_version=str(item.get("protocol_version", "1.0.0")),
            )
            for item in dependents
        )
        return publish_trust_registry_entry(packet, dependent_records).canonical_dict()

    def verify_network_locally(
        self,
        *,
        partner_payload: dict[str, Any],
        witnesses: tuple[dict[str, Any], ...],
        quorum: int,
        dependents: tuple[dict[str, Any], ...] = (),
    ) -> dict[str, Any]:
        packet = build_partner_verification_packet(
            tenant_id=str(partner_payload["tenant_id"]),
            region_id=str(partner_payload["region_id"]),
            trace_hash=str(partner_payload["trace_hash"]),
            replay_hash=str(partner_payload["replay_hash"]),
            receipt_hash=str(partner_payload["receipt_hash"]),
            authority_hash=str(partner_payload["authority_hash"]),
            execution_fingerprint=str(partner_payload["execution_fingerprint"]),
            publication_target=str(partner_payload["publication_target"]),
            network=str(partner_payload.get("network", "external-ledger-testnet")),
            publisher_id=str(partner_payload.get("publisher_id", "afritech-anchor-publisher")),
            external_reference=partner_payload.get("external_reference"),
        )
        witness_records = tuple(
            VerificationWitness(
                verifier_id=str(item["verifier_id"]),
                organization=str(item["organization"]),
                decision=str(item["decision"]),
                evidence_hash=str(item["evidence_hash"]),
            )
            for item in witnesses
        )
        dependent_records = tuple(
            register_protocol_dependency(
                dependent_id=str(item["dependent_id"]),
                organization=str(item["organization"]),
                use_case=str(item["use_case"]),
                protocol_version=str(item.get("protocol_version", "1.0.0")),
            )
            for item in dependents
        )
        record = build_multi_party_verification_record(packet, witness_records, quorum=quorum)
        return build_trust_network_verification(record, dependent_records).canonical_dict()
