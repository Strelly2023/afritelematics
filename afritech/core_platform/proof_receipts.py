"""Portable proof receipts for canonical trust seals."""

from __future__ import annotations

from datetime import datetime, timezone
import base64
from typing import Any, Mapping, Sequence

from afritech.core_platform.cryptographic_consensus import _canonicalize_seal, _hash
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.core_platform.threshold_bls import (
    BLS_AVAILABLE,
    bls_pop_verify,
    bls_verify_aggregate,
)


def _canonical_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return _canonicalize_seal(receipt)


def _signer_set_hash(signers: list[str]) -> str:
    normalized = sorted(str(item).strip() for item in signers if str(item).strip())
    return _hash({"signers": normalized}, domain=HASH_DOMAINS["SIGNER_SET"])


def _decode_public_key(value: str) -> bytes:
    text = str(value).strip()
    if not text:
        raise ValueError("empty_public_key")
    try:
        return bytes.fromhex(text)
    except ValueError:
        try:
            return base64.b64decode(text, validate=True)
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("invalid_public_key_encoding") from exc


def _decode_signature(value: str) -> bytes:
    text = str(value).strip()
    if not text:
        raise ValueError("empty_signature")
    try:
        return bytes.fromhex(text)
    except ValueError:
        try:
            return base64.b64decode(text, validate=True)
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError("invalid_signature_encoding") from exc


def build_proof_receipt(
    trust_seal: Mapping[str, Any],
    *,
    issuer: str = "novatrust-proof-service",
    issued_at: str | None = None,
) -> dict[str, Any]:
    if not isinstance(trust_seal, Mapping) or not trust_seal:
        raise ValueError("trust_seal_required")

    receipt = {
        "type": "novatrust-proof-receipt",
        "version": "1.0",
        "issuer": issuer,
        "issued_at": issued_at or datetime.now(timezone.utc).isoformat(),
        "seal_id": str(trust_seal.get("seal_id", "")).strip(),
        "seal_hash": str(trust_seal.get("seal_hash", "")).strip(),
        "trust_id": str(trust_seal.get("trust_id", "")).strip(),
        "packet_hash": str(trust_seal.get("packet_hash", "")).strip(),
        "consensus_root": str(trust_seal.get("consensus_root", "")).strip(),
        "validator_root": str(trust_seal.get("validator_root", "")).strip(),
        "aggregate_signature": str(trust_seal.get("aggregate_signature", "")).strip(),
        "aggregate_scheme": str(trust_seal.get("aggregate_signature_scheme", "")).strip(),
        "signature_threshold": trust_seal.get("signature_threshold"),
        "accepted_validators": list(trust_seal.get("accepted_validators", [])),
        "rejected_validators": list(trust_seal.get("rejected_validators", [])),
        "violations_hash": str(trust_seal.get("violations_hash", "")).strip(),
        "consensus_reached": bool(trust_seal.get("cryptographic_consensus", False)),
        "total_votes_raw": int(trust_seal.get("total_votes_raw", 0)),
        "total_votes_effective": int(trust_seal.get("total_votes_effective", 0)),
        "node_health_hash": str(trust_seal.get("node_health_hash", "")).strip(),
        "node_health_status": str(trust_seal.get("node_health_status", "unknown")).strip(),
        "signer_set": list(trust_seal.get("signer_set", [])),
        "signer_pop_proofs": list(trust_seal.get("signer_pop_proofs", [])),
        "signer_set_hash": _signer_set_hash(list(trust_seal.get("signer_set", []))),
    }
    receipt_hash = _hash(_canonical_receipt(receipt), domain=HASH_DOMAINS["PROOF_RECEIPT"])
    receipt["receipt_hash"] = receipt_hash
    receipt["receipt_id"] = f"receipt-{receipt_hash[:16]}"
    return receipt


def verify_proof_receipt(
    receipt: Mapping[str, Any],
    *,
    group_public_keys: Sequence[str | bytes] | None = None,
) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or not receipt:
        raise ValueError("receipt_required")

    unsigned = dict(receipt)
    expected_hash = str(unsigned.pop("receipt_hash", "")).strip()
    unsigned.pop("receipt_id", None)
    if not expected_hash:
        return {
            "valid": False,
            "reason": "missing_receipt_hash",
            "receipt_hash": None,
            "expected_hash": None,
        }
    computed_hash = _hash(_canonical_receipt(unsigned), domain=HASH_DOMAINS["PROOF_RECEIPT"])
    if computed_hash != expected_hash:
        return {
            "valid": False,
            "reason": "receipt_hash_mismatch",
            "receipt_hash": expected_hash,
            "expected_hash": computed_hash,
        }

    aggregate_scheme = str(unsigned.get("aggregate_scheme", "")).strip()
    if aggregate_scheme == "bls-threshold":
        signer_set = list(unsigned.get("signer_set", []))
        signer_pop_proofs = list(unsigned.get("signer_pop_proofs", []))
        signer_set_hash = str(unsigned.get("signer_set_hash", "")).strip()
        aggregate_signature = str(unsigned.get("aggregate_signature", "")).strip()
        consensus_root = str(unsigned.get("consensus_root", "")).strip()
        threshold = int(unsigned.get("signature_threshold") or 0)
        if not signer_set:
            return {
                "valid": False,
                "reason": "empty_signer_set",
                "receipt_hash": expected_hash,
            }
        if not aggregate_signature or not consensus_root:
            return {
                "valid": False,
                "reason": "missing_bls_receipt_fields",
                "receipt_hash": expected_hash,
            }
        if threshold > 0 and len(signer_set) < threshold:
            return {
                "valid": False,
                "reason": "threshold_not_met",
                "receipt_hash": expected_hash,
            }
        if not signer_set_hash:
            return {
                "valid": False,
                "reason": "missing_signer_set_hash",
                "receipt_hash": expected_hash,
            }
        if not BLS_AVAILABLE:
            return {
                "valid": None,
                "reason": "py_ecc_unavailable",
                "receipt_hash": expected_hash,
            }
        try:
            public_keys = [_decode_public_key(public_key) for public_key in signer_set]
            signature_bytes = _decode_signature(aggregate_signature)
        except ValueError as exc:
            return {
                "valid": False,
                "reason": str(exc),
                "receipt_hash": expected_hash,
            }
        if _signer_set_hash(signer_set) != signer_set_hash:
            return {
                "valid": False,
                "reason": "signer_set_hash_mismatch",
                "receipt_hash": expected_hash,
            }
        if not signer_pop_proofs:
            return {
                "valid": False,
                "reason": "proof_of_possession_required",
                "receipt_hash": expected_hash,
            }
        if len(signer_pop_proofs) != len(public_keys):
            return {
                "valid": False,
                "reason": "proof_of_possession_mismatch",
                "receipt_hash": expected_hash,
            }
        for public_key, proof in zip(public_keys, signer_pop_proofs, strict=True):
            try:
                proof_bytes = _decode_signature(proof)
            except ValueError as exc:
                return {
                    "valid": False,
                    "reason": str(exc),
                    "receipt_hash": expected_hash,
                }
            if not bls_pop_verify(public_key, proof_bytes):
                return {
                    "valid": False,
                    "reason": "invalid_proof_of_possession",
                    "receipt_hash": expected_hash,
                }
        if group_public_keys:
            normalized_group_keys = []
            for public_key in group_public_keys:
                if isinstance(public_key, (bytes, bytearray)):
                    normalized_group_keys.append(bytes(public_key))
                else:
                    try:
                        normalized_group_keys.append(_decode_public_key(str(public_key)))
                    except ValueError:
                        return {
                            "valid": False,
                            "reason": "invalid_group_public_key_encoding",
                            "receipt_hash": expected_hash,
                        }
            if sorted(key.hex() for key in normalized_group_keys) != sorted(
                key.hex() for key in public_keys
            ):
                return {
                    "valid": False,
                    "reason": "signer_set_mismatch",
                    "receipt_hash": expected_hash,
                }
        valid = bls_verify_aggregate(
            public_keys,
            consensus_root,
            signature_bytes,
        )
        return {
            "valid": bool(valid),
            "reason": "bls_threshold_verified" if valid else "bls_threshold_invalid",
            "receipt_hash": expected_hash,
        }

    return {
        "valid": True,
        "reason": "receipt_verified",
        "receipt_hash": expected_hash,
    }


__all__ = ["build_proof_receipt", "verify_proof_receipt"]
