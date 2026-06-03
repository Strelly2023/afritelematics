import logging
from typing import Dict

logger = logging.getLogger(__name__)


# =====================================================
# ✅ CONFIG
# =====================================================

REQUIRED_FIELDS = [
    "merkle_root",
    "signature",
    "public_key_id",
    "data",
]

REQUIRED_DATA_FIELDS = ["logs"]


# =====================================================
# ✅ STRUCTURE VALIDATION
# =====================================================

def guard_validate_proof_structure(proof: Dict) -> bool:
    """
    Validate proof structure according to RULE‑014.

    Ensures:
    - required top-level fields
    - nested data.logs existence
    - correct types
    """

    try:
        if not isinstance(proof, dict):
            logger.warning("[GUARD] Proof is not a dict")
            return False

        # ✅ top-level fields
        for field in REQUIRED_FIELDS:
            if field not in proof:
                logger.warning(f"[GUARD] Missing field: {field}")
                return False

        # ✅ nested data
        data = proof.get("data")
        if not isinstance(data, dict):
            logger.warning("[GUARD] Invalid data field")
            return False

        for field in REQUIRED_DATA_FIELDS:
            if field not in data:
                logger.warning(f"[GUARD] Missing data field: {field}")
                return False

        # ✅ logs must be list
        logs = data.get("logs")
        if not isinstance(logs, list):
            logger.warning("[GUARD] logs must be a list")
            return False

        return True

    except Exception:
        logger.exception("[GUARD] Structure validation failed")
        return False


# =====================================================
# ✅ MERKLE VALIDATION
# =====================================================

def guard_validate_merkle(proof: Dict, computed_root: str) -> bool:
    """
    Validate Merkle root integrity.
    """

    try:
        expected_root = proof.get("merkle_root")

        if not expected_root:
            logger.warning("[GUARD] Missing merkle_root")
            return False

        if computed_root != expected_root:
            logger.error(
                f"[GUARD] Merkle mismatch: expected={expected_root} "
                f"computed={computed_root}"
            )
            return False

        return True

    except Exception:
        logger.exception("[GUARD] Merkle validation failed")
        return False


# =====================================================
# ✅ SIGNATURE VALIDATION
# =====================================================

def guard_validate_signature(valid: bool) -> bool:
    """
    Validate signature result from crypto layer.
    """

    try:
        if not valid:
            logger.error("[GUARD] Invalid signature detected")
            return False

        return True

    except Exception:
        logger.exception("[GUARD] Signature validation failed")
        return False


# =====================================================
# ✅ OPTIONAL: STRICT MODE (ADVANCED)
# =====================================================

def guard_enforce_strict_schema(proof: Dict) -> bool:
    """
    Optional strict schema guard (future use).

    Ensures:
    - version present
    - hash_algorithm present
    - no unexpected structural deviations
    """

    try:
        required = ["version", "hash_algorithm", "timestamp"]

        for field in required:
            if field not in proof:
                logger.warning(f"[STRICT] Missing field: {field}")
                return False

        return True

    except Exception:
        logger.exception("[STRICT] Schema enforcement failed")
        return False