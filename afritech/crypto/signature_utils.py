"""Compatibility signature utilities for cross-system proof verification."""

from __future__ import annotations

from afritech.crypto.signature import verify_signature as verify_root_signature


def verify_signature(data: str, signature: str, public_key: str | None = None) -> bool:
    """Verify a signature.

    The current canonical verifier loads the repository public key internally.
    The public_key argument is accepted for ADR-0014 compatibility.
    """

    _ = public_key
    return verify_root_signature(data, signature)
