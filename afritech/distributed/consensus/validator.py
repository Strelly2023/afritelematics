from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from afritech.distributed.proof import validate_proof_structure


class ProofValidator:
    def __init__(
        self,
        public_keys: Optional[Mapping[str, Ed25519PublicKey | bytes | str]] = None,
    ) -> None:
        self.public_keys = dict(public_keys or {})

    def validate(self, proof: Dict[str, Any]) -> bool:
        if not validate_proof_structure(proof):
            return False

        if not self.public_keys:
            return True

        node_id = proof.get("node")
        if not isinstance(node_id, str):
            return False

        public_key = self.public_keys.get(node_id)
        if public_key is None:
            return False

        try:
            if isinstance(public_key, str):
                public_key = Ed25519PublicKey.from_public_bytes(
                    bytes.fromhex(public_key)
                )
            elif isinstance(public_key, bytes):
                public_key = Ed25519PublicKey.from_public_bytes(public_key)

            payload = {
                "node": proof["node"],
                "result": proof["result"],
                "metadata": proof.get("metadata", {}),
            }
            message = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
            public_key.verify(bytes.fromhex(proof["signature"]), message)
            return True
        except Exception:
            return False
