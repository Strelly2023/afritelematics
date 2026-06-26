"""Helpers for exporting proof receipts into on-chain verification commitments."""

from __future__ import annotations

from textwrap import dedent
from typing import Any, Mapping

from afritech.core_platform.cryptographic_consensus import _hash
from afritech.core_platform.hash_domains import HASH_DOMAINS


def build_signer_set_hash(receipt: Mapping[str, Any]) -> str:
    signer_set = sorted(str(item).strip() for item in receipt.get("signer_set", []) if str(item).strip())
    return _hash({"signers": signer_set}, domain=HASH_DOMAINS["SIGNER_SET"])


def build_onchain_verification_bundle(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or not receipt:
        raise ValueError("receipt_required")

    signer_set_hash = build_signer_set_hash(receipt)
    bundle = {
        "receipt_hash": str(receipt.get("receipt_hash", "")).strip(),
        "seal_hash": str(receipt.get("seal_hash", "")).strip(),
        "consensus_root": str(receipt.get("consensus_root", "")).strip(),
        "validator_root": str(receipt.get("validator_root", "")).strip(),
        "signer_set_hash": signer_set_hash,
        "aggregate_signature": str(receipt.get("aggregate_signature", "")).strip(),
        "aggregate_scheme": str(receipt.get("aggregate_scheme", "")).strip(),
        "signature_threshold": int(receipt.get("signature_threshold") or 0),
        "anchor_reference": str(receipt.get("seal_id", "")).strip(),
        "domain": "novatrust.onchain.verification.v1",
    }
    bundle["bundle_hash"] = _hash(bundle, domain=HASH_DOMAINS["ONCHAIN_BUNDLE"])
    return bundle


def solidity_verifier_source() -> str:
    return dedent(
        """
        // SPDX-License-Identifier: MIT
        pragma solidity ^0.8.20;

        contract NovaTrustVerifier {
            mapping(bytes32 => bool) public verifiedReceipts;
            event ReceiptVerified(bytes32 receiptHash, bytes32 sealHash, bytes32 consensusRoot);

            function verifyReceipt(
                bytes32 receiptHash,
                bytes32 sealHash,
                bytes32 consensusRoot,
                bytes32 signerSetHash
            ) external returns (bool) {
                require(receiptHash != bytes32(0), "Invalid receipt");
                require(sealHash != bytes32(0), "Invalid seal");
                require(consensusRoot != bytes32(0), "Invalid consensus root");
                require(signerSetHash != bytes32(0), "Invalid signer set");
                verifiedReceipts[receiptHash] = true;
                emit ReceiptVerified(receiptHash, sealHash, consensusRoot);
                return true;
            }
        }
        """
    ).strip()


__all__ = ["build_onchain_verification_bundle", "build_signer_set_hash", "solidity_verifier_source"]
