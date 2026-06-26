"""Privacy-preserving receipt bundles backed by deterministic ZK-style commitments."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from afritech.core_platform.cryptographic_consensus import _canonicalize_seal, _hash
from afritech.core_platform.hash_domains import HASH_DOMAINS


def _normalized_hidden_fields(hidden_fields: Sequence[str] | None) -> list[str]:
    if not hidden_fields:
        return []
    return sorted({str(field).strip() for field in hidden_fields if str(field).strip()})


def _hidden_commitment(receipt: Mapping[str, Any], hidden_fields: Sequence[str]) -> str:
    return _hash(
        {field: receipt.get(field) for field in hidden_fields},
        domain=HASH_DOMAINS["ZK_RECEIPT_HIDDEN"],
    )


def _redacted_receipt(
    receipt: Mapping[str, Any],
    hidden_fields: Sequence[str],
) -> dict[str, Any]:
    return _canonicalize_seal(
        {
            key: value
            for key, value in receipt.items()
            if key not in hidden_fields
        }
    )


def build_zk_receipt(
    receipt: Mapping[str, Any],
    *,
    hidden_fields: Sequence[str] | None = None,
    chain_id: str | None = None,
    epoch: int | None = None,
    scheme: str = "mock-zk-receipt-v1",
) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or not receipt:
        raise ValueError("receipt_required")

    normalized_hidden_fields = _normalized_hidden_fields(hidden_fields)
    redacted = _redacted_receipt(receipt, normalized_hidden_fields)
    public_inputs = {
        "receipt_hash": _hash(redacted, domain=HASH_DOMAINS["ZK_RECEIPT_PUBLIC"]),
        "hidden_commitment": _hidden_commitment(receipt, normalized_hidden_fields),
        "issued_at": str(receipt.get("issued_at", "")).strip(),
        "chain_id": str(chain_id or receipt.get("chain_id", "")).strip(),
        "epoch": int(epoch if epoch is not None else receipt.get("epoch", 0) or 0),
    }
    commitment = _hash(
        {
            "public_inputs": public_inputs,
            "redacted_receipt": redacted,
            "hidden_fields": normalized_hidden_fields,
        },
        domain=HASH_DOMAINS["ZK_RECEIPT_COMMITMENT"],
    )
    proof_hash = _hash(
        {
            "scheme": scheme,
            "commitment": commitment,
            "public_inputs": public_inputs,
        },
        domain=HASH_DOMAINS["ZK_RECEIPT_PROOF"],
    )

    return {
        "type": "zk_receipt",
        "version": "1.0",
        "scheme": scheme,
        "hidden_fields": normalized_hidden_fields,
        "public_inputs": public_inputs,
        "redacted_receipt": redacted,
        "commitment": commitment,
        "proof": proof_hash,
        "proof_hash": _hash(
            {
                "scheme": scheme,
                "commitment": commitment,
                "proof": proof_hash,
                "public_inputs": public_inputs,
            },
            domain=HASH_DOMAINS["ZK_RECEIPT_ARTIFACT"],
        ),
    }


def verify_zk_receipt(
    bundle: Mapping[str, Any],
    *,
    expected_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(bundle, Mapping) or not bundle:
        raise ValueError("zk_receipt_required")

    scheme = str(bundle.get("scheme", "")).strip()
    public_inputs = bundle.get("public_inputs")
    redacted_receipt = bundle.get("redacted_receipt")
    commitment = str(bundle.get("commitment", "")).strip()
    proof = str(bundle.get("proof", "")).strip()
    proof_hash = str(bundle.get("proof_hash", "")).strip()
    hidden_fields = _normalized_hidden_fields(bundle.get("hidden_fields"))

    if not scheme:
        return {"valid": False, "reason": "zk_scheme_missing"}
    if not isinstance(public_inputs, Mapping):
        return {"valid": False, "reason": "zk_public_inputs_missing"}
    if not isinstance(redacted_receipt, Mapping):
        return {"valid": False, "reason": "zk_redacted_receipt_missing"}
    if not commitment or not proof or not proof_hash:
        return {"valid": False, "reason": "zk_artifact_incomplete"}

    expected_commitment = _hash(
        {
            "public_inputs": _canonicalize_seal(public_inputs),
            "redacted_receipt": _canonicalize_seal(redacted_receipt),
            "hidden_fields": hidden_fields,
        },
        domain=HASH_DOMAINS["ZK_RECEIPT_COMMITMENT"],
    )
    if commitment != expected_commitment:
        return {"valid": False, "reason": "zk_commitment_mismatch"}

    expected_proof = _hash(
        {
            "scheme": scheme,
            "commitment": commitment,
            "public_inputs": _canonicalize_seal(public_inputs),
        },
        domain=HASH_DOMAINS["ZK_RECEIPT_PROOF"],
    )
    if proof != expected_proof:
        return {"valid": False, "reason": "zk_proof_mismatch"}

    expected_proof_hash = _hash(
        {
            "scheme": scheme,
            "commitment": commitment,
            "proof": proof,
            "public_inputs": _canonicalize_seal(public_inputs),
        },
        domain=HASH_DOMAINS["ZK_RECEIPT_ARTIFACT"],
    )
    if proof_hash != expected_proof_hash:
        return {"valid": False, "reason": "zk_proof_hash_mismatch"}

    if expected_receipt is not None:
        hidden_commitment = _hidden_commitment(expected_receipt, hidden_fields)
        if public_inputs.get("hidden_commitment") != hidden_commitment:
            return {"valid": False, "reason": "zk_hidden_commitment_mismatch"}

        expected_public_receipt_hash = _hash(
            _redacted_receipt(expected_receipt, hidden_fields),
            domain=HASH_DOMAINS["ZK_RECEIPT_PUBLIC"],
        )
        if public_inputs.get("receipt_hash") != expected_public_receipt_hash:
            return {"valid": False, "reason": "zk_public_receipt_hash_mismatch"}

    return {
        "valid": True,
        "reason": "zk_receipt_verified",
        "scheme": scheme,
        "commitment": commitment,
        "proof_hash": proof_hash,
    }


def build_zk_receipt_qr_bundle(
    receipt: Mapping[str, Any],
    *,
    hidden_fields: Sequence[str] | None = None,
    chain_id: str | None = None,
    epoch: int | None = None,
    bridge: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    zk_receipt = build_zk_receipt(
        receipt,
        hidden_fields=hidden_fields,
        chain_id=chain_id,
        epoch=epoch,
    )
    bundle = {
        "type": "novatrust-zk-qr",
        "version": "1.0",
        "issued_at": str(receipt.get("issued_at", "")).strip(),
        "zk_receipt": zk_receipt,
    }
    if bridge is not None:
        bundle["bridge"] = bridge
    bundle["qr_hash"] = _hash(
        {key: value for key, value in bundle.items() if key != "qr_hash"},
        domain=HASH_DOMAINS["ZK_QR_PAYLOAD"],
    )
    return bundle


__all__ = [
    "build_zk_receipt",
    "build_zk_receipt_qr_bundle",
    "verify_zk_receipt",
]
