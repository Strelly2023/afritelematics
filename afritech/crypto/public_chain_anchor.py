"""Deterministic public-chain style receipts for externally published proof anchors."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PublicChainAnchorReceipt:
    chain_receipt_id: str
    chain_name: str
    network: str
    anchor_id: str
    publication_id: str
    commitment_hash: str
    publication_hash: str
    proof_hash: str
    transaction_hash: str
    block_number: int
    merkle_root: str
    chain_proof_hash: str
    contract_reference: str
    explorer_url: str
    authority_boundary: str = "public_chain_receipt_proves_publication_not_runtime_truth"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.public_chain_anchor_receipt.v1",
            "chain_receipt_id": self.chain_receipt_id,
            "chain_name": self.chain_name,
            "network": self.network,
            "anchor_id": self.anchor_id,
            "publication_id": self.publication_id,
            "commitment_hash": self.commitment_hash,
            "publication_hash": self.publication_hash,
            "proof_hash": self.proof_hash,
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
            "merkle_root": self.merkle_root,
            "chain_proof_hash": self.chain_proof_hash,
            "contract_reference": self.contract_reference,
            "explorer_url": self.explorer_url,
            "authority_boundary": self.authority_boundary,
        }


def build_public_chain_anchor_receipt(
    *,
    anchor_id: str,
    publication_id: str,
    commitment_hash: str,
    publication_hash: str,
    proof_hash: str,
    chain_name: str = "Public Transparency Chain",
    network: str = "ptc-testnet",
) -> PublicChainAnchorReceipt:
    payload = {
        "anchor_id": anchor_id,
        "publication_id": publication_id,
        "commitment_hash": commitment_hash,
        "publication_hash": publication_hash,
        "proof_hash": proof_hash,
        "chain_name": chain_name,
        "network": network,
    }
    chain_proof_hash = _canonical_hash(payload)
    transaction_hash = _canonical_hash(
        {
            "chain_proof_hash": chain_proof_hash,
            "commitment_hash": commitment_hash,
            "publication_hash": publication_hash,
        }
    )
    merkle_root = _canonical_hash(
        {
            "transaction_hash": transaction_hash,
            "proof_hash": proof_hash,
            "anchor_id": anchor_id,
        }
    )
    block_number = int(transaction_hash[:8], 16)
    contract_reference = f"contract-{chain_proof_hash[:16]}"
    return PublicChainAnchorReceipt(
        chain_receipt_id=f"chain-{chain_proof_hash[:12]}",
        chain_name=chain_name,
        network=network,
        anchor_id=anchor_id,
        publication_id=publication_id,
        commitment_hash=commitment_hash,
        publication_hash=publication_hash,
        proof_hash=proof_hash,
        transaction_hash=f"0x{transaction_hash}",
        block_number=block_number,
        merkle_root=merkle_root,
        chain_proof_hash=chain_proof_hash,
        contract_reference=contract_reference,
        explorer_url=f"https://explorer.afritech.invalid/{network}/tx/{transaction_hash}",
    )


__all__ = ["PublicChainAnchorReceipt", "build_public_chain_anchor_receipt"]
