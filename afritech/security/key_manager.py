"""Signing-provider abstraction for governed trust-root signatures."""

from __future__ import annotations

import hashlib
import os
from typing import Protocol

from nacl.signing import SigningKey


class SigningProvider(Protocol):
    signer_id: str

    def sign(self, payload: bytes) -> bytes: ...

    def public_key(self) -> bytes: ...


class DeterministicLocalSigningProvider:
    """Deterministic local provider for reproducible CI and dev verification."""

    def __init__(self, signer_id: str = "AFRITECH_CORE", seed: bytes | None = None) -> None:
        self.signer_id = signer_id
        resolved_seed = seed or hashlib.sha256(
            f"afritech-{signer_id.lower()}-trust-root-v1".encode("utf-8")
        ).digest()
        self._key = SigningKey(resolved_seed)

    def sign(self, payload: bytes) -> bytes:
        return self._key.sign(payload).signature

    def public_key(self) -> bytes:
        return self._key.verify_key.encode()


class EnvironmentSigningProvider(DeterministicLocalSigningProvider):
    """Provider using a hex seed from the environment for controlled deployments."""

    def __init__(
        self,
        signer_id: str = "AFRITECH_CORE",
        env_var: str = "AFRITECH_REGISTRY_SIGNING_SEED_HEX",
    ) -> None:
        seed_hex = os.environ.get(env_var)
        seed = bytes.fromhex(seed_hex) if seed_hex else None
        super().__init__(signer_id=signer_id, seed=seed)


def default_signing_provider() -> SigningProvider:
    return EnvironmentSigningProvider()


__all__ = [
    "DeterministicLocalSigningProvider",
    "EnvironmentSigningProvider",
    "SigningProvider",
    "default_signing_provider",
]
