from __future__ import annotations

import json
from typing import Any, Dict, Union

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


class NodeIdentity:
    """
    🔐 GA-Elite Sovereign Node Identity

    Capabilities:
    - Deterministic signing (dict + bytes)
    - Signature verification (local + external)
    - Network-safe public key encoding (hex)
    - Compatible with handshake + zero-trust layer
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(self, private_key: Ed25519PrivateKey | None = None) -> None:

        if private_key is None:
            self._private_key = Ed25519PrivateKey.generate()
        else:
            if not isinstance(private_key, Ed25519PrivateKey):
                raise TypeError("Invalid private key")
            self._private_key = private_key

        self.public_key: Ed25519PublicKey = self._private_key.public_key()

    # =====================================================
    # ✅ SIGNING
    # =====================================================

    def sign(self, data: Union[Dict[str, Any], bytes]) -> bytes:
        """
        Sign structured or raw data deterministically.
        """

        if isinstance(data, bytes):
            message = data
        else:
            message = self._serialize(data)

        return self._private_key.sign(message)

    # =====================================================
    # ✅ VERIFY (SELF)
    # =====================================================

    def verify(
        self,
        signature: bytes,
        data: Union[Dict[str, Any], bytes],
    ) -> bool:
        """
        Verify using own public key.
        """

        try:
            message = data if isinstance(data, bytes) else self._serialize(data)
            self.public_key.verify(signature, message)
            return True
        except Exception:
            return False

    # =====================================================
    # ✅ VERIFY (EXTERNAL - HEX KEY)
    # =====================================================

    @staticmethod
    def verify_hex(
        public_key_hex: str,
        signature: bytes,
        data: Union[Dict[str, Any], bytes],
    ) -> bool:
        """
        Verify signature using public key in hex format.
        """

        try:
            if not isinstance(public_key_hex, str):
                return False

            public_key_bytes = bytes.fromhex(public_key_hex)
            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

            if isinstance(data, bytes):
                message = data
            else:
                message = NodeIdentity._serialize_static(data)

            public_key.verify(signature, message)
            return True

        except Exception:
            return False

    # =====================================================
    # ✅ SERIALIZATION (DETERMINISTIC)
    # =====================================================

    def _serialize(self, data: Dict[str, Any]) -> bytes:
        return self._serialize_static(data)

    @staticmethod
    def _serialize_static(data: Dict[str, Any]) -> bytes:
        """
        Canonical JSON encoding.
        """

        try:
            serialized = json.dumps(
                data,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
        except Exception:
            serialized = str(data)

        return serialized.encode("utf-8")

    # =====================================================
    # ✅ PUBLIC KEY EXPORT (NETWORK FRIENDLY)
    # =====================================================

    def get_public_key_bytes(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    def get_public_key_hex(self) -> str:
        """
        ✅ Used as node_id in network layer
        """
        return self.get_public_key_bytes().hex()

    def serialize_public_key(self) -> bytes:
        """
        Backward-compatible public key export used by zero-trust nodes.
        """
        return self.get_public_key_bytes()

    # =====================================================
    # ✅ PUBLIC KEY IMPORT
    # =====================================================

    @staticmethod
    def load_public_key(data: bytes) -> Ed25519PublicKey:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Public key must be bytes")

        return Ed25519PublicKey.from_public_bytes(data)

    # =====================================================
    # ✅ PRIVATE KEY EXPORT
    # =====================================================

    def export_private_key(self) -> bytes:
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    # =====================================================
    # ✅ PRIVATE KEY IMPORT
    # =====================================================

    @staticmethod
    def load_private_key(data: bytes) -> Ed25519PrivateKey:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Private key must be bytes")

        return Ed25519PrivateKey.from_private_bytes(data)
