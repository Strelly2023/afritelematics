import json
from typing import Dict, Any, List

from afritech.audit.merkle import MerkleTree
from afritech.audit.hash_engine import HashEngine
from afritech.crypto.signature import verify_signature


# =====================================================
# ✅ NORMALIZE LOG ENTRY
# =====================================================

def _normalize_log(log: Dict[str, Any]) -> Dict[str, Any]:
    required_fields = ["payload", "previous_hash", "entry_hash"]

    for field in required_fields:
        if field not in log:
            raise ValueError(f"MISSING_FIELD_{field.upper()}")

    payload = log["payload"]

    # ✅ normalize payload
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not isinstance(payload, dict):
        raise ValueError("PAYLOAD_MUST_BE_DICT")

    return {
        "payload": payload,
        "previous_hash": log["previous_hash"],
        "entry_hash": log["entry_hash"],
    }


# =====================================================
# ✅ VERIFY FULL AUDIT PROOF
# =====================================================

def verify_audit_proof(proof: Dict[str, Any]) -> bool:
    if not isinstance(proof, dict):
        return False

    logs: List[Dict[str, Any]] = proof.get("logs", [])
    root: str | None = proof.get("merkle_root")
    signature: str | None = proof.get("signature")

    if not logs or not isinstance(logs, list):
        return False

    if not root or not isinstance(root, str):
        return False

    if not signature or not isinstance(signature, str):
        return False

    try:
        leaf_hashes: List[str] = []
        previous_hash_expected = None

        for i, raw_log in enumerate(logs):
            log = _normalize_log(raw_log)

            # ✅ recompute hash
            computed_hash = HashEngine.compute_hash(
                previous_hash=log["previous_hash"],
                payload=log["payload"],
            )

            if computed_hash != log["entry_hash"]:
                return False

            # ✅ chain validation
            if i == 0:
                # genesis entry
                if log["previous_hash"] not in (None, "", "null"):
                    return False
            else:
                if log["previous_hash"] != previous_hash_expected:
                    return False

            previous_hash_expected = log["entry_hash"]

            leaf_hashes.append(log["entry_hash"])

        # ✅ merkle verification
        tree = MerkleTree(leaf_hashes)
        computed_root = tree.get_root()

        if computed_root != root:
            return False

        # ✅ signature verification
        return verify_signature(root, signature)

    except Exception:
        return False


# =====================================================
# ✅ VERIFY SINGLE LOG PROOF
# =====================================================

def verify_log_proof(proof_package: Dict[str, Any]) -> bool:
    if not isinstance(proof_package, dict):
        return False

    try:
        log = proof_package.get("log")
        proof = proof_package.get("proof")
        root = proof_package.get("merkle_root")
        signature = proof_package.get("signature")

        if not log or not proof or not root or not signature:
            return False

        if not isinstance(proof, list):
            return False

        # ✅ normalize log
        normalized = _normalize_log(log)

        # ✅ recompute hash
        computed_hash = HashEngine.compute_hash(
            previous_hash=normalized["previous_hash"],
            payload=normalized["payload"],
        )

        if computed_hash != normalized["entry_hash"]:
            return False

        # ✅ verify merkle proof
        if not MerkleTree.verify_proof(computed_hash, proof, root):
            return False

        # ✅ verify signature
        return verify_signature(root, signature)

    except Exception:
        return False