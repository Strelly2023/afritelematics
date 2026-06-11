"""Deterministic legal-proof formats for external audit and regulatory exchange."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from afritech.partner_verification import PartnerVerificationPacket


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class LegalProofDocument:
    format_id: str
    legal_format: str
    packet_hash: str
    anchor_id: str
    publication_id: str
    evidence_pointer: str
    authority_boundary: str
    document_hash: str
    classification: str = "bounded_external_evidence"

    def canonical_dict(self) -> dict[str, str]:
        return {
            "schema": "afritech.legal_proof_document.v1",
            "format_id": self.format_id,
            "legal_format": self.legal_format,
            "packet_hash": self.packet_hash,
            "anchor_id": self.anchor_id,
            "publication_id": self.publication_id,
            "evidence_pointer": self.evidence_pointer,
            "authority_boundary": self.authority_boundary,
            "classification": self.classification,
            "document_hash": self.document_hash,
        }


def build_legal_proof_document(
    packet: PartnerVerificationPacket,
    *,
    legal_format: str = "REGULATORY_AUDIT_V1",
) -> LegalProofDocument:
    if not legal_format:
        raise ValueError("legal_format is required")
    packet_hash = _canonical_hash(packet.canonical_dict())
    format_id = f"legal-{packet.anchor_id}-{legal_format.lower()}"
    authority_boundary = (
        "document packages evidence for legal or compliance review; "
        "document does not replace replay truth"
    )
    document_hash = _canonical_hash(
        {
            "legal_format": legal_format,
            "packet_hash": packet_hash,
            "anchor_id": packet.anchor_id,
            "publication_id": packet.publication_id,
            "evidence_pointer": packet.evidence_pointer,
        }
    )
    return LegalProofDocument(
        format_id=format_id,
        legal_format=legal_format,
        packet_hash=packet_hash,
        anchor_id=packet.anchor_id,
        publication_id=packet.publication_id,
        evidence_pointer=packet.evidence_pointer,
        authority_boundary=authority_boundary,
        document_hash=document_hash,
    )


__all__ = ["LegalProofDocument", "build_legal_proof_document"]
