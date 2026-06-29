"""Signing helpers for NovaRide architecture publications."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from afritech.core_platform.signing import (
    AuditSignature,
    canonical_bytes,
    sign_packet,
    signing_key_status,
    verify_packet_signature,
)


def sign_architecture_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Sign a canonical NovaRide architecture contract payload."""

    signature = sign_packet(contract)
    status = signing_key_status()
    signed_at = datetime.now(UTC).isoformat()
    return {
        "signature_status": "signed",
        "signature_version": 1,
        "signed_at": signed_at,
        "algorithm": signature.scheme,
        "key_id": signature.key_id,
        "provider": status.provider,
        "signature": signature.canonical(),
    }


def verify_architecture_signature(
    contract: Mapping[str, Any],
    signature: Mapping[str, Any] | AuditSignature,
) -> bool:
    """Verify a canonical NovaRide architecture contract signature."""

    return verify_packet_signature(contract, signature)


def canonical_architecture_bytes(contract: Mapping[str, Any]) -> bytes:
    """Return the canonical serialized bytes used for architecture signing."""

    return canonical_bytes(contract)


__all__ = [
    "canonical_architecture_bytes",
    "sign_architecture_contract",
    "verify_architecture_signature",
]
