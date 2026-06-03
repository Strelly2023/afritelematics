from __future__ import annotations

import json
from typing import List

from django.db import connection

from afritech.models.audit_log import AuditLog
from afritech.models.audit_seal import AuditSeal
from afritech.audit.merkle import MerkleTree
from afritech.audit.hash_engine import HashEngine
from afritech.crypto.signature import sign_data

from afritech.crypto.signature import verify_signature


# =====================================================
# ✅ INTERNAL — FETCH HASHES (CANONICAL + VERIFIED)
# =====================================================

def _fetch_valid_hashes(epoch: int) -> List[str]:
    """
    Fetch and VERIFY hashes by recomputing deterministically.

    Guarantees:
    - Detects payload tampering
    - Detects hash chain corruption
    - Ensures canonical replay integrity

    Returns:
        List[str]: ordered valid entry hashes

    If tampering is detected → returns empty list
    """

    query = """
        SELECT id, payload, previous_hash, entry_hash
        FROM afritech_auditlog
        WHERE status = 'VALID' AND epoch <= %s
        ORDER BY timestamp, id
    """

    with connection.cursor() as cursor:
        cursor.execute(query, [epoch])
        rows = cursor.fetchall()

    leaf_hashes: List[str] = []

    for row in rows:
        log_id, payload, previous_hash, stored_hash = row

        # ✅ Ensure payload is dict
        if isinstance(payload, str):
            try:
                payload_dict = json.loads(payload)
            except Exception:
                # Invalid JSON → tampering
                return []
        else:
            payload_dict = payload

        # ✅ Correct canonical hash computation
        computed_hash = HashEngine.compute_hash(
            previous_hash=previous_hash,
            payload=payload_dict,
        )

        # 🔐 Detect tampering
        if computed_hash != stored_hash:
            return []

        leaf_hashes.append(stored_hash)

    return leaf_hashes


# =====================================================
# ✅ CREATE SEAL
# =====================================================





def seal_epoch(epoch: int) -> AuditSeal:
    """
    Creates immutable, SIGNED Merkle root checkpoint for given epoch.

    Rules:
    - Uses only VALID audit entries
    - Deterministic ordering enforced
    - Prevents overwriting existing seal
    - Signs the Merkle root (cryptographic proof)
    """

    logs = (
        AuditLog.objects
        .filter(status="VALID", epoch__lte=epoch)
        .order_by("timestamp", "id")
        .only("entry_hash")
    )

    leaf_hashes = [log.entry_hash for log in logs]

    if not leaf_hashes:
        raise ValueError("NO_LOGS_TO_SEAL")

    # ✅ Build Merkle tree
    tree = MerkleTree(leaf_hashes)
    root = tree.get_root()

    # ✅ Sign the root
    signature = sign_data(root)

    seal, created = AuditSeal.objects.get_or_create(
        epoch=epoch,
        defaults={
            "merkle_root": root,
            "signature": signature,  # ✅ NEW FIELD
        },
    )

    # =====================================================
    # ✅ IMMUTABILITY ENFORCEMENT
    # =====================================================

    if not created:
        # ❌ Root mismatch → tampering or inconsistency
        if seal.merkle_root != root:
            raise ValueError("SEAL_ALREADY_EXISTS_WITH_DIFFERENT_ROOT")

        # ✅ Signature already exists → valid
        if seal.signature:
            return seal

        # ✅ Recovery case: root exists but signature missing
        seal.signature = sign_data(root)
        seal.save(update_fields=["signature"])

    return seal

# =====================================================
# ✅ VERIFY SEAL
# =====================================================

from afritech.crypto.signature import verify_signature


def verify_seal(epoch: int) -> bool:
    """
    Verifies Merkle seal + cryptographic signature integrity.

    Steps:
    1. Fetch stored seal (root + signature)
    2. Recompute all entry hashes (tamper detection)
    3. Rebuild Merkle root
    4. Compare computed root with stored root
    5. Verify cryptographic signature

    Returns:
        bool: True if fully valid, False otherwise
    """

    # =====================================================
    # ✅ STEP 1 — FETCH SEAL
    # =====================================================
    try:
        seal = AuditSeal.objects.only("merkle_root", "signature").get(epoch=epoch)
    except AuditSeal.DoesNotExist:
        return False

    # =====================================================
    # ✅ STEP 2 — FETCH & VALIDATE HASHES
    # =====================================================
    leaf_hashes = _fetch_valid_hashes(epoch)

    if not leaf_hashes:
        return False  # tamper or no logs

    # =====================================================
    # ✅ STEP 3 — REBUILD MERKLE ROOT
    # =====================================================
    tree = MerkleTree(leaf_hashes)
    computed_root = tree.get_root()

    # =====================================================
    # ✅ STEP 4 — ROOT VALIDATION
    # =====================================================
    if computed_root != seal.merkle_root:
        return False

    # =====================================================
    # ✅ STEP 5 — SIGNATURE VALIDATION (CRITICAL)
    # =====================================================

    # ❌ No signature = invalid (zero-trust rule)
    if not seal.signature:
        return False

    is_valid_signature = verify_signature(
        seal.merkle_root,
        seal.signature,
    )

    if not is_valid_signature:
        return False

    # ✅ EVERYTHING VERIFIED
    return True


# =====================================================
# ✅ VERIFY ALL SEALS
# =====================================================

def verify_all_seals() -> bool:
    """
    Verifies integrity of all seals in the system.
    """

    epochs = (
        AuditSeal.objects
        .values_list("epoch", flat=True)
        .order_by("epoch")
    )

    for epoch in epochs:
        if not verify_seal(epoch):
            return False

    return True


# =====================================================
# ✅ DEBUG / FORENSIC REPORT
# =====================================================

def debug_verify_seal(epoch: int) -> dict:
    """
    Provides detailed diagnostics for seal verification.

    Useful for:
    - forensic analysis
    - debugging mismatches
    - audit investigations
    """

    try:
        seal = AuditSeal.objects.get(epoch=epoch)
    except AuditSeal.DoesNotExist:
        return {
            "epoch": epoch,
            "error": "SEAL_NOT_FOUND",
        }

    leaf_hashes = _fetch_valid_hashes(epoch)

    if not leaf_hashes:
        return {
            "epoch": epoch,
            "error": "NO_LOGS_OR_TAMPER_DETECTED",
        }

    tree = MerkleTree(leaf_hashes)
    computed_root = tree.get_root()

    return {
        "epoch": epoch,
        "stored_root": seal.merkle_root,
        "computed_root": computed_root,
        "match": computed_root == seal.merkle_root,
        "leaf_count": len(leaf_hashes),
    }