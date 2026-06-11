"""Deterministic Merkle batching for published anchor envelopes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from afritech.crypto.anchor_publication import AnchorPublicationEnvelope
from afritech.crypto.merkle import compute_merkle_root


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class AnchorMerkleBatch:
    batch_id: str
    batch_root: str
    batch_size: int
    anchor_ids: tuple[str, ...]
    publication_ids: tuple[str, ...]
    publication_target: str
    manifest_hash: str
    authority_boundary: str = "batching_proves_membership_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.anchor_merkle_batch.v1",
            "batch_id": self.batch_id,
            "batch_root": self.batch_root,
            "batch_size": self.batch_size,
            "anchor_ids": list(self.anchor_ids),
            "publication_ids": list(self.publication_ids),
            "publication_target": self.publication_target,
            "manifest_hash": self.manifest_hash,
            "authority_boundary": self.authority_boundary,
        }


def build_anchor_merkle_batch(
    envelopes: tuple[AnchorPublicationEnvelope, ...],
    *,
    publication_target: str,
) -> AnchorMerkleBatch:
    if not envelopes:
        raise ValueError("at least one envelope is required")
    if not publication_target:
        raise ValueError("publication_target is required")

    ordered = tuple(sorted(envelopes, key=lambda item: item.anchor_id))
    leaves = [
        {
            "anchor_id": envelope.anchor_id,
            "publication_id": envelope.publication_id,
            "commitment_hash": envelope.commitment_hash,
            "publication_hash": envelope.publication_hash,
            "receipt_commitment": envelope.receipt_commitment,
            "tenant_id": envelope.tenant_id,
            "region_id": envelope.region_id,
        }
        for envelope in ordered
    ]
    batch_root = compute_merkle_root(leaves)
    manifest_hash = _canonical_hash(
        {
            "publication_target": publication_target,
            "leaves": leaves,
            "batch_root": batch_root,
        }
    )
    batch_id = f"batch-{batch_root[:12]}"
    return AnchorMerkleBatch(
        batch_id=batch_id,
        batch_root=batch_root,
        batch_size=len(ordered),
        anchor_ids=tuple(item.anchor_id for item in ordered),
        publication_ids=tuple(item.publication_id for item in ordered),
        publication_target=publication_target,
        manifest_hash=manifest_hash,
    )


__all__ = ["AnchorMerkleBatch", "build_anchor_merkle_batch"]
