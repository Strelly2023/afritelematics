from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from afritech.models.audit_log import AuditLog
from afritech.models.audit_seal import AuditSeal


# =====================================================
# ✅ INTERNAL — NORMALIZE LOG RECORD
# =====================================================

def _normalize_log_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures exported log data is JSON-safe and canonical.

    - Converts payload to dict if needed
    - Converts UUID/id to string
    - Ensures required fields exist
    """

    payload = row.get("payload")

    # ✅ Normalize payload
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            raise ValueError("INVALID_PAYLOAD_IN_DB")

    if not isinstance(payload, dict):
        raise ValueError("PAYLOAD_MUST_BE_DICT")

    return {
        "id": str(row.get("id")),
        "epoch": row.get("epoch"),
        "payload": payload,
        "entry_hash": row.get("entry_hash"),
        "previous_hash": row.get("previous_hash"),
    }


# =====================================================
# ✅ GENERATE AUDIT PROOF
# =====================================================

def export_audit_proof(epoch: int) -> Dict[str, Any]:
    """
    Export a complete cryptographic audit proof.

    Includes:
    - ordered logs (deterministic)
    - Merkle root
    - signature
    - metadata

    Guarantees:
    - JSON-safe output
    - deterministic ordering
    - externally verifiable

    Raises:
        ValueError:
            - SEAL_NOT_FOUND
            - SEAL_NOT_SIGNED
    """

    try:
        seal = (
            AuditSeal.objects
            .only("merkle_root", "signature")
            .get(epoch=epoch)
        )
    except AuditSeal.DoesNotExist:
        raise ValueError("SEAL_NOT_FOUND")

    # ✅ enforce signature presence (critical for external trust)
    if not seal.signature:
        raise ValueError("SEAL_NOT_SIGNED")

    logs_qs = (
        AuditLog.objects
        .filter(status="VALID", epoch__lte=epoch)
        .order_by("timestamp", "id")
        .values("id", "epoch", "payload", "entry_hash", "previous_hash")
    )

    logs: List[Dict[str, Any]] = [
        _normalize_log_record(row) for row in logs_qs
    ]

    return {
        "epoch": epoch,
        "merkle_root": seal.merkle_root,
        "signature": seal.signature,
        "algorithm": "RSA-SHA256",
        "log_count": len(logs),
        "logs": logs,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# =====================================================
# ✅ EXPORT AS JSON FILE
# =====================================================

def export_audit_proof_json(epoch: int, filepath: str) -> None:
    """
    Writes audit proof to a JSON file.

    Output is:
    - human readable
    - deterministic
    - portable across systems

    Raises:
        ValueError if proof cannot be generated
        IOError if file writing fails
    """

    proof = export_audit_proof(epoch)

    # ✅ deterministic JSON output
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            proof,
            f,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,   # ✅ stable output ordering
        )