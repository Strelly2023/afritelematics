"""
afritech/network/node_identity.py

Node Identity
=============

Defines the identity of a sovereign AfriTech node.

Responsibilities:
- Provide deterministic node identity
- Enable cryptographic fingerprinting
- Support trust verification in distributed network
- Prepare for signing / secure communication
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json


# -----------------------------------------------------------------
# IDENTITY ERROR
# -----------------------------------------------------------------

class NodeIdentityError(Exception):
    pass


# -----------------------------------------------------------------
# NODE IDENTITY
# -----------------------------------------------------------------

class NodeIdentity:

    def __init__(
        self,
        node_id: str,
        public_key: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        :param node_id: unique node identifier
        :param public_key: node public key (string form)
        :param metadata: optional node metadata
        """

        if not node_id:
            raise NodeIdentityError("node_id is required")

        if not public_key:
            raise NodeIdentityError("public_key is required")

        self.node_id = node_id
        self.public_key = public_key
        self.metadata = metadata or {}

        self.registered_at = datetime.utcnow().isoformat() + "Z"

        # deterministic identity
        self.identity_hash = self._compute_identity_hash()

    # -----------------------------------------------------------------
    # CANONICAL JSON
    # -----------------------------------------------------------------

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        )

    # -----------------------------------------------------------------
    # IDENTITY HASH (FINGERPRINT)
    # -----------------------------------------------------------------

    def _compute_identity_hash(self) -> str:
        """
        Generates a deterministic fingerprint for the node.
        """

        payload = {
            "node_id": self.node_id,
            "public_key": self.public_key,
        }

        return hashlib.sha256(
            self._canonical_json(payload).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # VERIFY INTEGRITY
    # -----------------------------------------------------------------

    def verify(self) -> bool:
        """
        Ensure identity has not been tampered
        """
        return self.identity_hash == self._compute_identity_hash()

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "public_key": self.public_key,
            "metadata": self.metadata,
            "registered_at": self.registered_at,
            "identity_hash": self.identity_hash,
        }

    # -----------------------------------------------------------------
    # IMPORT / REBUILD
    # -----------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeIdentity":

        if not isinstance(data, dict):
            raise NodeIdentityError("Invalid input data")

        node = cls(
            node_id=data.get("node_id"),
            public_key=data.get("public_key"),
            metadata=data.get("metadata", {})
        )

        # optional integrity check if hash provided
        stored_hash = data.get("identity_hash")
        if stored_hash and stored_hash != node.identity_hash:
            raise NodeIdentityError("Identity hash mismatch")

        return node

    # -----------------------------------------------------------------
    # SIGNATURE PLACEHOLDER (EXTENSION READY)
    # -----------------------------------------------------------------

    def sign(self, private_key: str) -> Dict[str, Any]:
        """
        Placeholder for signing identity.

        Future:
        - RSA/ECDSA signing
        - certificate chain
        """

        signature_payload = f"{self.identity_hash}:{private_key}"

        signature = hashlib.sha256(signature_payload.encode()).hexdigest()

        return {
            "node_id": self.node_id,
            "identity_hash": self.identity_hash,
            "signature": signature,
            "signed_at": datetime.utcnow().isoformat() + "Z"
        }

    # -----------------------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<NodeIdentity id={self.node_id} hash={self.identity_hash[:10]}...>"
