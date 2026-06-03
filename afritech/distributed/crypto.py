from __future__ import annotations

import json
from typing import Any, Dict

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


class NodeIdentity:
    """
    Cryptographic identity for a sovereign node.

    Capabilities:
    - Sign execution results
    - Verify signatures
    - Export public key for network sharing
    - Deterministic message encoding
    """

    def __init__(self, private_key: Ed25519PrivateKey | None = None) -> None:
        """
        Initialize identity.

        If no private key is provided, a new one is generated.
        """

        if private_key is None:
            self._private_key: Ed25519PrivateKey = Ed25519PrivateKey.generate()
        else:
            if not isinstance(private_key, Ed25519PrivateKey):
                raise TypeError("Invalid private key")
            self._private_key = private_key

        self.public_key: Ed25519PublicKey = self._private_key.public_key()

    # -----------------------------------------------------
    # Signing
    # -----------------------------------------------------

    def sign(self, data: Dict[str, Any]) -> bytes:
        """
        Sign structured data deterministically.
        """

        message = self._serialize(data)
        return self._private_key.sign(message)

    # -----------------------------------------------------
    # Verification (self)
    # -----------------------------------------------------

    def verify(self, signature: bytes, data: Dict[str, Any]) -> bool:
        """
        Verify signature using this node's public key.
        """

        try:
            message = self._serialize(data)
            self.public_key.verify(signature, message)
            return True

        except Exception:
            return False

    # -----------------------------------------------------
    # Verification (external key)
    # -----------------------------------------------------

    @staticmethod
    def verify_with_public_key(
        public_key: Ed25519PublicKey,
        signature: bytes,
        data: Dict[str, Any],
    ) -> bool:
        """
        Verify signature using an external public key.
        """

        try:
            message = json.dumps(
                data,
                sort_keys=True,
                default=str
            ).encode("utf-8")

            public_key.verify(signature, message)
            return True

        except Exception:
            return False

    # -----------------------------------------------------
    # Serialization (deterministic)
    # -----------------------------------------------------

    def _serialize(self, data: Dict[str, Any]) -> bytes:
        """
        Deterministic JSON serialization for signing.
        """

        try:
            serialized = json.dumps(
                data,
                sort_keys=True,   # ✅ deterministic ordering
                separators=(",", ":"),  # ✅ no whitespace differences
                default=str       # ✅ fallback for non-serializable data
            )
        except Exception:
            # fallback safety
            serialized = str(data)

        return serialized.encode("utf-8")

    # -----------------------------------------------------
    # Public key export
    # -----------------------------------------------------

    def serialize_public_key(self) -> bytes:
        """
        Export public key (raw bytes).
        """

        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    # -----------------------------------------------------
    # Public key import
    # -----------------------------------------------------

    @staticmethod
    def load_public_key(data: bytes) -> Ed25519PublicKey:
        """
        Load public key from raw bytes.
        """

        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Public key must be bytes")

        return Ed25519PublicKey.from_public_bytes(data)

    # -----------------------------------------------------
    # Private key export (secure use only)
    # -----------------------------------------------------

    def export_private_key(self) -> bytes:
        """
        Export private key (raw bytes).

        ⚠️ WARNING: Store securely.
        """

        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    # -----------------------------------------------------
    # Private key import
    # -----------------------------------------------------

    @staticmethod
    def load_private_key(data: bytes) -> Ed25519PrivateKey:
        """
        Load private key from raw bytes.
        """

        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Private key must be bytes")

        return Ed25519PrivateKey.from_private_bytes(data)