"""Deterministic anchor publication envelopes for external evidence exchange."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from afritech.crypto.external_anchor import ExternalAnchorCommitment


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class AnchorPublicationEnvelope:
    publication_id: str
    anchor_id: str
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
    publisher_id: str
    external_reference: str
    publication_hash: str
    receipt_commitment: str
    status: str = "READY_TO_PUBLISH"

    def canonical_dict(self) -> dict[str, str]:
        return {
            "schema": "afritech.anchor_publication_envelope.v1",
            "publication_id": self.publication_id,
            "anchor_id": self.anchor_id,
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
            "publisher_id": self.publisher_id,
            "external_reference": self.external_reference,
            "publication_hash": self.publication_hash,
            "receipt_commitment": self.receipt_commitment,
            "status": self.status,
        }


def build_anchor_publication_envelope(
    commitment: ExternalAnchorCommitment,
    *,
    publication_target: str,
    publisher_id: str = "afritech-anchor-publisher",
    external_reference: str | None = None,
) -> AnchorPublicationEnvelope:
    if not publication_target:
        raise ValueError("publication_target is required")
    if not publisher_id:
        raise ValueError("publisher_id is required")

    reference = external_reference or f"ledger-ref-{commitment.commitment_hash[:16]}"
    publication_payload = {
        "anchor_id": commitment.anchor_id,
        "commitment_hash": commitment.commitment_hash,
        "external_reference": reference,
        "payload_hash": commitment.payload_hash,
        "publication_target": publication_target,
        "publisher_id": publisher_id,
    }
    publication_hash = _canonical_hash(publication_payload)
    receipt_commitment = _canonical_hash(
        {
            "publication_hash": publication_hash,
            "publication_target": publication_target,
            "external_reference": reference,
        }
    )
    publication_id = f"publish-{publication_hash[:12]}"

    return AnchorPublicationEnvelope(
        publication_id=publication_id,
        anchor_id=commitment.anchor_id,
        tenant_id=commitment.tenant_id,
        region_id=commitment.region_id,
        network=commitment.network,
        trace_hash=commitment.trace_hash,
        replay_hash=commitment.replay_hash,
        receipt_hash=commitment.receipt_hash,
        authority_hash=commitment.authority_hash,
        execution_fingerprint=commitment.execution_fingerprint,
        commitment_hash=commitment.commitment_hash,
        payload_hash=commitment.payload_hash,
        publication_target=publication_target,
        publisher_id=publisher_id,
        external_reference=reference,
        publication_hash=publication_hash,
        receipt_commitment=receipt_commitment,
    )


__all__ = [
    "AnchorPublicationEnvelope",
    "build_anchor_publication_envelope",
]
