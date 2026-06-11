"""Governed multi-party verification for partner proof packets."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from afritech.partner_verification import PartnerVerificationPacket
from afritech.standards_dependency import build_standard_conformance_profile


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class VerificationWitness:
    verifier_id: str
    organization: str
    decision: str
    evidence_hash: str

    def canonical_dict(self) -> dict[str, str]:
        return {
            "verifier_id": self.verifier_id,
            "organization": self.organization,
            "decision": self.decision,
            "evidence_hash": self.evidence_hash,
        }


@dataclass(frozen=True)
class MultiPartyVerificationRecord:
    verification_id: str
    anchor_id: str
    quorum: int
    witness_count: int
    verified_count: int
    aggregate_status: str
    protocol_version: str
    standard_profile: str
    witness_manifest_hash: str
    witnesses: tuple[VerificationWitness, ...]
    authority_boundary: str = "quorum_records_verifier_alignment_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.multi_party_verification_record.v1",
            "verification_id": self.verification_id,
            "anchor_id": self.anchor_id,
            "quorum": self.quorum,
            "witness_count": self.witness_count,
            "verified_count": self.verified_count,
            "aggregate_status": self.aggregate_status,
            "protocol_version": self.protocol_version,
            "standard_profile": self.standard_profile,
            "witness_manifest_hash": self.witness_manifest_hash,
            "witnesses": [witness.canonical_dict() for witness in self.witnesses],
            "authority_boundary": self.authority_boundary,
        }


def build_multi_party_verification_record(
    packet: PartnerVerificationPacket,
    witnesses: tuple[VerificationWitness, ...],
    *,
    quorum: int,
) -> MultiPartyVerificationRecord:
    if quorum <= 0:
        raise ValueError("quorum must be positive")
    if not witnesses:
        raise ValueError("at least one witness is required")

    verifier_ids = [witness.verifier_id for witness in witnesses]
    if len(verifier_ids) != len(set(verifier_ids)):
        raise ValueError("verifier_id values must be unique")

    decisions = {witness.decision for witness in witnesses}
    if not decisions.issubset({"VERIFIED", "REJECTED"}):
        raise ValueError("witness decisions must be VERIFIED or REJECTED")

    verified_count = sum(1 for witness in witnesses if witness.decision == "VERIFIED")
    if verified_count >= quorum:
        aggregate_status = "QUORUM_VERIFIED"
    elif (len(witnesses) - verified_count) >= quorum:
        aggregate_status = "QUORUM_REJECTED"
    else:
        aggregate_status = "INSUFFICIENT_QUORUM"

    profile = build_standard_conformance_profile()
    witness_manifest_hash = _canonical_hash(
        {
            "anchor_id": packet.anchor_id,
            "publication_hash": packet.publication_hash,
            "profile_hash": profile.profile_hash,
            "witnesses": [witness.canonical_dict() for witness in witnesses],
            "quorum": quorum,
        }
    )
    verification_id = f"mpv-{witness_manifest_hash[:12]}"
    return MultiPartyVerificationRecord(
        verification_id=verification_id,
        anchor_id=packet.anchor_id,
        quorum=quorum,
        witness_count=len(witnesses),
        verified_count=verified_count,
        aggregate_status=aggregate_status,
        protocol_version=profile.protocol_version,
        standard_profile=profile.profile_id,
        witness_manifest_hash=witness_manifest_hash,
        witnesses=witnesses,
    )


__all__ = [
    "MultiPartyVerificationRecord",
    "VerificationWitness",
    "build_multi_party_verification_record",
]
