import logging
from typing import Dict

from afritech.crypto.key_registry import get_public_key
from afritech.crypto.signature_utils import verify_signature
from afritech.crypto.merkle import compute_merkle_root
from afritech.guards.guard_cross_proof import (
    guard_validate_proof_structure,
    guard_validate_merkle,
    guard_validate_signature,
)

logger = logging.getLogger(__name__)


def verify_cross_system_proof(proof: Dict) -> bool:
    """
    Cross-system proof verification service.

    Executes full verification pipeline:
    1. Structure validation
    2. Merkle root recomputation
    3. Integrity verification
    4. Public key resolution
    5. Signature verification
    6. Guard enforcement

    Returns:
        bool: True if valid, False otherwise
    """

    try:
        # =====================================================
        # ✅ STEP 1: STRUCTURE VALIDATION
        # =====================================================
        if not guard_validate_proof_structure(proof):
            logger.warning("[VERIFY] Invalid proof structure")
            return False

        # =====================================================
        # ✅ STEP 2: EXTRACT DATA
        # =====================================================
        logs = proof["data"]["logs"]
        provided_root = proof.get("merkle_root")
        key_id = proof.get("public_key_id")
        signature = proof.get("signature")

        # =====================================================
        # ✅ STEP 3: COMPUTE MERKLE ROOT
        # =====================================================
        computed_root = compute_merkle_root(logs)

        if not guard_validate_merkle(proof, computed_root):
            logger.error("[VERIFY] Merkle root mismatch")
            return False

        # =====================================================
        # ✅ STEP 4: LOAD PUBLIC KEY
        # =====================================================
        public_key = get_public_key(key_id)

        if not public_key:
            logger.error(f"[VERIFY] Public key not found: {key_id}")
            return False

        # =====================================================
        # ✅ STEP 5: VERIFY SIGNATURE
        # =====================================================
        valid_signature = verify_signature(
            provided_root,
            signature,
            public_key
        )

        if not guard_validate_signature(valid_signature):
            logger.error("[VERIFY] Signature verification failed")
            return False

        # =====================================================
        # ✅ STEP 6: OPTIONAL CONTEXT VALIDATION
        # =====================================================
        version = proof.get("version")
        if version and version != "v1":
            logger.warning(f"[VERIFY] Unsupported version: {version}")

        timestamp = proof.get("timestamp")
        if not timestamp:
            logger.warning("[VERIFY] Missing timestamp (non-critical)")

        # =====================================================
        # ✅ SUCCESS
        # =====================================================
        logger.info(
            f"[VERIFY_SUCCESS] key_id={key_id} "
            f"root={provided_root[:10]}..."
        )

        return True

    except Exception:
        logger.exception("[VERIFY_ERROR] Cross-system verification failure")
        return False