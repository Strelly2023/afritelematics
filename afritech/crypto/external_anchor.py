"""Deterministic external anchoring payloads for replay-backed evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ExternalAnchorCommitment:
    anchor_id: str
    network: str
    tenant_id: str
    region_id: str
    trace_hash: str
    replay_hash: str
    receipt_hash: str
    authority_hash: str
    execution_fingerprint: str
    commitment_hash: str
    payload_hash: str
    status: str = "PENDING"

    def canonical_dict(self) -> dict[str, str]:
        return {
            "schema": "afritech.external_anchor_commitment.v1",
            "anchor_id": self.anchor_id,
            "network": self.network,
            "tenant_id": self.tenant_id,
            "region_id": self.region_id,
            "trace_hash": self.trace_hash,
            "replay_hash": self.replay_hash,
            "receipt_hash": self.receipt_hash,
            "authority_hash": self.authority_hash,
            "execution_fingerprint": self.execution_fingerprint,
            "commitment_hash": self.commitment_hash,
            "payload_hash": self.payload_hash,
            "status": self.status,
        }


def build_external_anchor_commitment(
    *,
    tenant_id: str,
    region_id: str,
    trace_hash: str,
    replay_hash: str,
    receipt_hash: str,
    authority_hash: str,
    execution_fingerprint: str,
    network: str = "external-ledger-testnet",
) -> ExternalAnchorCommitment:
    if not tenant_id or not region_id:
        raise ValueError("tenant_id and region_id are required")
    for name, value in (
        ("trace_hash", trace_hash),
        ("replay_hash", replay_hash),
        ("receipt_hash", receipt_hash),
        ("authority_hash", authority_hash),
        ("execution_fingerprint", execution_fingerprint),
    ):
        if len(value) != 64:
            raise ValueError(f"{name} must be a 64-character hex hash")

    payload = {
        "network": network,
        "tenant_id": tenant_id,
        "region_id": region_id,
        "trace_hash": trace_hash,
        "replay_hash": replay_hash,
        "receipt_hash": receipt_hash,
        "authority_hash": authority_hash,
        "execution_fingerprint": execution_fingerprint,
    }
    payload_hash = _canonical_hash(payload)
    commitment_hash = _canonical_hash(
        {
            "payload_hash": payload_hash,
            "tenant_id": tenant_id,
            "region_id": region_id,
            "network": network,
        }
    )
    anchor_id = f"anchor-{commitment_hash[:12]}"
    return ExternalAnchorCommitment(
        anchor_id=anchor_id,
        network=network,
        tenant_id=tenant_id,
        region_id=region_id,
        trace_hash=trace_hash,
        replay_hash=replay_hash,
        receipt_hash=receipt_hash,
        authority_hash=authority_hash,
        execution_fingerprint=execution_fingerprint,
        commitment_hash=commitment_hash,
        payload_hash=payload_hash,
    )
