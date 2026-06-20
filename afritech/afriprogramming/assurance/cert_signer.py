from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any


DEFAULT_CERTIFICATION_KEY_ID = os.environ.get("NOVAPROGRAMMING_CERT_KEY_ID", "nova-cert-key-1")
_CERT_SECRET = os.environ.get("NOVAPROGRAMMING_CERT_SECRET", "nova-cert-secret").encode("utf-8")


def now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def canonicalize(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonicalize(payload).encode("utf-8")).hexdigest()


def sign_payload_hash(payload_hash: str) -> str:
    return hmac.new(_CERT_SECRET, payload_hash.encode("utf-8"), hashlib.sha256).hexdigest()


def issue_signed_certification(payload: dict[str, Any]) -> dict[str, Any]:
    payload_hash = hash_payload(payload)
    signature = sign_payload_hash(payload_hash)
    return {
        "payload": payload,
        "certification_hash": payload_hash,
        "signature": signature,
        "public_key_id": DEFAULT_CERTIFICATION_KEY_ID,
        "issued_at": now(),
    }


def verify_signed_certification(certification: dict[str, Any]) -> dict[str, Any]:
    payload = certification.get("payload")
    if not isinstance(payload, dict):
        return {"valid": False, "reason": "payload required"}
    certification_hash = str(certification.get("certification_hash", ""))
    signature = str(certification.get("signature", ""))
    if not certification_hash or not signature:
        return {"valid": False, "reason": "certification_hash and signature required"}
    expected_hash = hash_payload(payload)
    if expected_hash != certification_hash:
        return {"valid": False, "reason": "certification hash mismatch"}
    expected_signature = sign_payload_hash(expected_hash)
    if not hmac.compare_digest(expected_signature, signature):
        return {"valid": False, "reason": "invalid signature"}
    return {"valid": True, "certification_hash": certification_hash}
