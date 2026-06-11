"""Deterministic receipt signing for bounded external verification."""

from __future__ import annotations

import hashlib
import hmac
import os


SIGNATURE_MODE = "hmac_sha256_receipt_v1"


def sign_receipt_hash(receipt_hash: str) -> str:
    secret = _secret()
    return hmac.new(secret, receipt_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_receipt_signature(receipt_hash: str, signature: str) -> bool:
    expected = sign_receipt_hash(receipt_hash)
    return hmac.compare_digest(expected, signature)


def _secret() -> bytes:
    return os.environ.get(
        "AFRIRIDE_RECEIPT_SIGNING_SECRET",
        "afriride-receipt-signing-secret",
    ).encode("utf-8")
