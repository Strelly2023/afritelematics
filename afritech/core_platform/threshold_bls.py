"""Optional threshold BLS helpers for portable cryptographic proofs."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Iterable

try:  # pragma: no cover - optional dependency
    from py_ecc.bls import G2ProofOfPossession as _bls  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _bls = None  # type: ignore[assignment]


BLS_AVAILABLE = _bls is not None


def _hash_message(message: str) -> bytes:
    return sha256(message.encode("utf-8")).digest()


def bls_sign(secret_key: int, message: str) -> bytes:
    if _bls is None:  # pragma: no cover - optional dependency
        raise RuntimeError("py_ecc_required_for_bls_signing")
    return _bls.Sign(secret_key, _hash_message(message))


def bls_verify(public_key: bytes, message: str, signature: bytes) -> bool:
    if _bls is None:  # pragma: no cover - optional dependency
        return False
    return bool(_bls.Verify(public_key, _hash_message(message), signature))


def bls_aggregate(signatures: Iterable[bytes]) -> bytes:
    if _bls is None:  # pragma: no cover - optional dependency
        raise RuntimeError("py_ecc_required_for_bls_aggregation")
    signature_list = list(signatures)
    if not signature_list:
        raise ValueError("signatures_required")
    return _bls.Aggregate(signature_list)


def bls_verify_aggregate(
    public_keys: Iterable[bytes],
    message: str,
    aggregate_signature: bytes,
) -> bool:
    if _bls is None:  # pragma: no cover - optional dependency
        return False
    keys = list(public_keys)
    if not keys:
        return False
    try:
        return bool(_bls.FastAggregateVerify(keys, _hash_message(message), aggregate_signature))
    except Exception:
        return False


def bls_pop_verify(public_key: bytes, proof: bytes | None) -> bool:
    if _bls is None:  # pragma: no cover - optional dependency
        return False
    if proof is None:
        return False
    try:
        return bool(_bls.PopVerify(public_key, proof))
    except Exception:
        return False


def bls_threshold_verify(
    public_keys: Iterable[bytes],
    signatures: Iterable[bytes],
    message: str,
    threshold: int,
) -> dict[str, Any]:
    key_list = list(public_keys)
    signature_list = list(signatures)
    if threshold <= 0:
        raise ValueError("threshold_must_be_positive")
    if len(signature_list) < threshold:
        return {
            "valid": False,
            "reason": "threshold_not_met",
            "threshold": threshold,
            "signatures": len(signature_list),
        }
    if not BLS_AVAILABLE:
        return {
            "valid": None,
            "reason": "py_ecc_unavailable",
            "threshold": threshold,
            "signatures": len(signature_list),
        }
    aggregate_signature = bls_aggregate(signature_list)
    valid = bls_verify_aggregate(key_list, message, aggregate_signature)
    return {
        "valid": valid,
        "reason": "bls_threshold_verified" if valid else "bls_threshold_invalid",
        "threshold": threshold,
        "signatures": len(signature_list),
    }


__all__ = [
    "BLS_AVAILABLE",
    "bls_aggregate",
    "bls_pop_verify",
    "bls_sign",
    "bls_threshold_verify",
    "bls_verify",
    "bls_verify_aggregate",
]
