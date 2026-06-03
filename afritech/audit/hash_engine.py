from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Optional


class HashEngine:
    """
    Deterministic cryptographic hash engine for audit entries.

    Guarantees:
    - stable serialization
    - canonical data normalization
    - consistent replay results
    - collision-resistant hashing (SHA-256)
    """

    # =====================================================
    # ✅ PAYLOAD NORMALIZATION
    # =====================================================

    @staticmethod
    def _normalize(value: Any) -> Any:
        """
        Recursively normalize payload into JSON-safe deterministic structure.

        Handles:
        - dict → sorted
        - list/tuple → normalized list
        - bool/int/str → unchanged
        - None → null
        - everything else → string representation
        """

        if isinstance(value, dict):
            return {k: HashEngine._normalize(v) for k, v in sorted(value.items())}

        if isinstance(value, (list, tuple)):
            return [HashEngine._normalize(v) for v in value]

        if isinstance(value, (str, int, bool)) or value is None:
            return value

        # ✅ fallback → deterministic string representation
        return str(value)

    # =====================================================
    # ✅ PAYLOAD SERIALIZATION
    # =====================================================

    @staticmethod
    def serialize_payload(payload: Dict[str, Any]) -> str:
        """
        Deterministic JSON serialization.

        Ensures:
        - sorted keys
        - normalized values
        - no whitespace noise
        """

        if not isinstance(payload, dict):
            raise ValueError("PAYLOAD_MUST_BE_DICT")

        try:
            normalized = HashEngine._normalize(payload)

            return json.dumps(
                normalized,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )

        except Exception as e:
            raise ValueError("INVALID_PAYLOAD_SERIALIZATION") from e

    # =====================================================
    # ✅ HASH COMPUTATION
    # =====================================================

    @staticmethod
    def compute_hash(previous_hash: Optional[str], payload: Dict[str, Any]) -> str:
        """
        Computes SHA-256 hash of:

            previous_hash + ":" + serialized_payload
        """

        serialized = HashEngine.serialize_payload(payload)

        previous_hash_str = previous_hash or ""

        base_string = f"{previous_hash_str}:{serialized}"

        return HashEngine._sha256(base_string)

    # =====================================================
    # ✅ ENTRY HASH GENERATOR
    # =====================================================

    @staticmethod
    def generate_entry_hash(entry) -> str:
        """
        Generates a hash from an audit entry object.
        """

        if not hasattr(entry, "payload"):
            raise ValueError("ENTRY_MISSING_PAYLOAD")

        if not hasattr(entry, "previous_hash"):
            raise ValueError("ENTRY_MISSING_PREVIOUS_HASH")

        return HashEngine.compute_hash(
            previous_hash=entry.previous_hash,
            payload=entry.payload,
        )

    # =====================================================
    # ✅ INTERNAL HASH FUNCTION
    # =====================================================

    @staticmethod
    def _sha256(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    # =====================================================
    # ✅ DEBUG / TRACE FUNCTION
    # =====================================================

    @staticmethod
    def debug_hash_components(
        previous_hash: Optional[str],
        payload: Dict[str, Any],
    ) -> dict:
        """
        Returns internal components used in hashing.
        """

        serialized = HashEngine.serialize_payload(payload)

        return {
            "previous_hash": previous_hash or "",
            "serialized_payload": serialized,
            "base_string": f"{previous_hash or ''}:{serialized}",
        }