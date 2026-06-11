"""Bounded partner verification packets built from replay-linked anchor evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.crypto.anchor_publication import (
    AnchorPublicationEnvelope,
    build_anchor_publication_envelope,
)
from afritech.crypto.external_anchor import build_external_anchor_commitment


@dataclass(frozen=True)
class PartnerVerificationPacket:
    anchor_id: str
    publication_id: str
    verification_status: str
    mismatch_reasons: tuple[str, ...]
    tenant_id: str
    region_id: str
    network: str
    trace_hash: str
    replay_hash: str
    receipt_hash: str
    authority_hash: str
    execution_fingerprint: str
    commitment_hash: str
    payload_hash: str
    publication_target: str
    publication_hash: str
    external_reference: str
    receipt_commitment: str
    authority_boundary: str
    evidence_pointer: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.partner_verification_packet.v1",
            "anchor_id": self.anchor_id,
            "publication_id": self.publication_id,
            "verification_status": self.verification_status,
            "mismatch_reasons": list(self.mismatch_reasons),
            "tenant_id": self.tenant_id,
            "region_id": self.region_id,
            "network": self.network,
            "trace_hash": self.trace_hash,
            "replay_hash": self.replay_hash,
            "receipt_hash": self.receipt_hash,
            "authority_hash": self.authority_hash,
            "execution_fingerprint": self.execution_fingerprint,
            "commitment_hash": self.commitment_hash,
            "payload_hash": self.payload_hash,
            "publication_target": self.publication_target,
            "publication_hash": self.publication_hash,
            "external_reference": self.external_reference,
            "receipt_commitment": self.receipt_commitment,
            "authority_boundary": self.authority_boundary,
            "evidence_pointer": self.evidence_pointer,
        }


class PartnerVerificationStore:
    """In-memory anchor packet store for bounded partner lookups."""

    def __init__(
        self,
        packets: tuple[PartnerVerificationPacket, ...] = (),
    ) -> None:
        self._packets = {packet.anchor_id: packet for packet in packets}

    def remember(self, packet: PartnerVerificationPacket) -> None:
        self._packets[packet.anchor_id] = packet

    def load(self, anchor_id: str) -> PartnerVerificationPacket:
        if anchor_id not in self._packets:
            raise KeyError(anchor_id)
        return self._packets[anchor_id]


def build_partner_verification_packet(
    *,
    tenant_id: str,
    region_id: str,
    trace_hash: str,
    replay_hash: str,
    receipt_hash: str,
    authority_hash: str,
    execution_fingerprint: str,
    publication_target: str,
    network: str = "external-ledger-testnet",
    publisher_id: str = "afritech-anchor-publisher",
    external_reference: str | None = None,
    expected_anchor_id: str | None = None,
    expected_commitment_hash: str | None = None,
    expected_publication_hash: str | None = None,
    expected_receipt_hash: str | None = None,
) -> PartnerVerificationPacket:
    commitment = build_external_anchor_commitment(
        tenant_id=tenant_id,
        region_id=region_id,
        trace_hash=trace_hash,
        replay_hash=replay_hash,
        receipt_hash=receipt_hash,
        authority_hash=authority_hash,
        execution_fingerprint=execution_fingerprint,
        network=network,
    )
    envelope = build_anchor_publication_envelope(
        commitment,
        publication_target=publication_target,
        publisher_id=publisher_id,
        external_reference=external_reference,
    )
    return verify_partner_anchor(
        envelope,
        expected_anchor_id=expected_anchor_id,
        expected_commitment_hash=expected_commitment_hash,
        expected_publication_hash=expected_publication_hash,
        expected_receipt_hash=expected_receipt_hash,
    )


def verify_partner_anchor(
    envelope: AnchorPublicationEnvelope,
    *,
    expected_anchor_id: str | None = None,
    expected_commitment_hash: str | None = None,
    expected_publication_hash: str | None = None,
    expected_receipt_hash: str | None = None,
) -> PartnerVerificationPacket:
    mismatches: list[str] = []
    if expected_anchor_id and expected_anchor_id != envelope.anchor_id:
        mismatches.append("anchor_id_mismatch")
    if expected_commitment_hash and expected_commitment_hash != envelope.commitment_hash:
        mismatches.append("commitment_hash_mismatch")
    if expected_publication_hash and expected_publication_hash != envelope.publication_hash:
        mismatches.append("publication_hash_mismatch")
    if expected_receipt_hash and expected_receipt_hash != envelope.receipt_hash:
        mismatches.append("receipt_hash_mismatch")

    verification_status = "VERIFIED" if not mismatches else "REJECTED"
    return PartnerVerificationPacket(
        anchor_id=envelope.anchor_id,
        publication_id=envelope.publication_id,
        verification_status=verification_status,
        mismatch_reasons=tuple(mismatches),
        tenant_id=envelope.tenant_id,
        region_id=envelope.region_id,
        network=envelope.network,
        trace_hash=envelope.trace_hash,
        replay_hash=envelope.replay_hash,
        receipt_hash=envelope.receipt_hash,
        authority_hash=envelope.authority_hash,
        execution_fingerprint=envelope.execution_fingerprint,
        commitment_hash=envelope.commitment_hash,
        payload_hash=envelope.payload_hash,
        publication_target=envelope.publication_target,
        publication_hash=envelope.publication_hash,
        external_reference=envelope.external_reference,
        receipt_commitment=envelope.receipt_commitment,
        authority_boundary=(
            "trace records authority; replay reconstructs truth; "
            "anchor proves export integrity only"
        ),
        evidence_pointer=(
            f"anchor:{envelope.anchor_id}:publication:{envelope.publication_id}"
        ),
    )


__all__ = [
    "PartnerVerificationPacket",
    "PartnerVerificationStore",
    "build_partner_verification_packet",
    "verify_partner_anchor",
]
