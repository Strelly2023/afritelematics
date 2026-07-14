"""Production-capable API contract signing and verification."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


class SigningBackend(Protocol):
    @property
    def key_id(self) -> str:
        ...

    @property
    def provider(self) -> str:
        ...

    def sign(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def verify(self, payload: dict[str, Any], signature: dict[str, Any]) -> bool:
        ...


@dataclass(frozen=True, slots=True)
class Ed25519SigningBackend:
    private_key: Ed25519PrivateKey
    public_key: Ed25519PublicKey
    _key_id: str
    _provider: str = "local_ed25519"

    @property
    def key_id(self) -> str:
        return self._key_id

    @property
    def provider(self) -> str:
        return self._provider

    def sign(self, payload: dict[str, Any]) -> dict[str, Any]:
        signature = self.private_key.sign(_canonical_json(payload))
        public_key_bytes = self.public_key.public_bytes_raw()
        return {
            "scheme": "ed25519",
            "provider": self.provider,
            "key_id": self.key_id,
            "value": base64.b64encode(signature).decode("ascii"),
            "public_key": base64.b64encode(public_key_bytes).decode("ascii"),
        }

    def verify(self, payload: dict[str, Any], signature: dict[str, Any]) -> bool:
        try:
            public_key_bytes = base64.b64decode(signature["public_key"])
            signature_bytes = base64.b64decode(signature["value"])
            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature_bytes, _canonical_json(payload))
            return True
        except Exception:
            return False


def _decode_private_key(value: str) -> Ed25519PrivateKey:
    raw = base64.b64decode(value)
    if len(raw) != 32:
        raise ValueError("API contract signing key must contain 32 raw Ed25519 bytes.")
    return Ed25519PrivateKey.from_private_bytes(raw)


@lru_cache(maxsize=1)
def get_signing_backend() -> SigningBackend:
    encoded_key = os.getenv("NOVATECH_API_CONTRACT_SIGNING_PRIVATE_KEY_B64")
    key_id = os.getenv("NOVATECH_API_CONTRACT_SIGNING_KEY_ID", "novatrust-api-contract-dev-01")
    environment = os.getenv("NOVATECH_ENVIRONMENT", "development").lower()
    if encoded_key:
        private_key = _decode_private_key(encoded_key)
        provider = "configured_ed25519"
    else:
        if environment == "production":
            raise RuntimeError("Production API contract signing key is not configured.")
        private_key = Ed25519PrivateKey.generate()
        provider = "ephemeral_development_ed25519"
    return Ed25519SigningBackend(private_key=private_key, public_key=private_key.public_key(), _key_id=key_id, _provider=provider)


def verify_signed_publication(publication: dict[str, Any]) -> bool:
    signature = publication.get("signature")
    if not isinstance(signature, dict):
        return False
    payload = {key: value for key, value in publication.items() if key != "signature"}
    return Ed25519SigningBackend(
        private_key=Ed25519PrivateKey.generate(),
        public_key=Ed25519PrivateKey.generate().public_key(),
        _key_id=str(signature.get("key_id") or "verification-only"),
    ).verify(payload, signature)
