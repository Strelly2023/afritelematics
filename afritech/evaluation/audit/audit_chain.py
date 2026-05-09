import hashlib
import json
from datetime import datetime


class AuditChainError(Exception):
    """Raised when audit chain validation fails"""
    pass


# -----------------------------------------------------------------
# AUDIT REPORT (FINAL VERIFICATION ARTIFACT)
# -----------------------------------------------------------------

class AuditReport:

    def __init__(self, total_entries, valid, details):
        self.total_entries = total_entries
        self.valid = valid
        self.details = details
        self.generated_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "total_entries": self.total_entries,
            "valid": self.valid,
            "details": self.details,
            "generated_at": self.generated_at
        }

    def canonical(self):
        return json.dumps(
            self.to_dict(),
            sort_keys=True,
            separators=(",", ":")
        )

    def hash(self):
        return hashlib.sha256(self.canonical().encode()).hexdigest()


# -----------------------------------------------------------------
# AUDIT CHAIN ENGINE
# -----------------------------------------------------------------

class AuditChain:

    def __init__(self, transcript_store):
        self.store = transcript_store

    # -----------------------------------------------------------------
    # CANONICAL HASH
    # -----------------------------------------------------------------

    def canonical_json(self, data):
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )

    def hash_data(self, data):
        return hashlib.sha256(
            self.canonical_json(data).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # FULL AUDIT VERIFICATION
    # -----------------------------------------------------------------

    def verify_full_chain(self):

        entries = self.store.get_all_entries()

        if not entries:
            return AuditReport(
                total_entries=0,
                valid=True,
                details={"message": "Empty chain"}
            )

        previous_hash = "GENESIS"
        issues = []

        for index, entry in enumerate(entries):

            # ✅ Step 1: Verify entry integrity
            recalculated_hash = self.hash_data({
                "transcript": entry["transcript"],
                "transcript_hash": entry["transcript_hash"],
                "previous_hash": entry["previous_hash"],
                "stored_at": entry["stored_at"]
            })

            if entry["entry_hash"] != recalculated_hash:
                issues.append({
                    "index": index,
                    "error": "ENTRY_HASH_MISMATCH"
                })

            # ✅ Step 2: Verify chain linkage
            if entry["previous_hash"] != previous_hash:
                issues.append({
                    "index": index,
                    "error": "CHAIN_LINK_BROKEN",
                    "expected": previous_hash,
                    "found": entry["previous_hash"]
                })

            # ✅ Step 3: Verify transcript consistency
            transcript_hash = entry["transcript_hash"]
            recalculated_transcript_hash = self.hash_data(
                entry["transcript"]
            )

            if transcript_hash != recalculated_transcript_hash:
                issues.append({
                    "index": index,
                    "error": "TRANSCRIPT_HASH_MISMATCH"
                })

            previous_hash = entry["entry_hash"]

        valid = len(issues) == 0

        details = {
            "issues": issues,
            "final_chain_hash": previous_hash
        }

        return AuditReport(
            total_entries=len(entries),
            valid=valid,
            details=details
        )

    # -----------------------------------------------------------------
    # VERIFY SINGLE ENTRY WITH CONTEXT
    # -----------------------------------------------------------------

    def verify_entry_with_context(self, entry_hash):

        entry = self.store.load_entry(entry_hash)

        # Verify entry integrity
        recalculated = self.hash_data({
            "transcript": entry["transcript"],
            "transcript_hash": entry["transcript_hash"],
            "previous_hash": entry["previous_hash"],
            "stored_at": entry["stored_at"]
        })

        if entry["entry_hash"] != recalculated:
            raise AuditChainError("Entry integrity failed")

        return {
            "entry_hash": entry_hash,
            "valid": True,
            "previous_hash": entry["previous_hash"]
        }

    # -----------------------------------------------------------------
    # GENERATE CHAIN FINGERPRINT
    # -----------------------------------------------------------------

    def compute_chain_fingerprint(self):
        """
        Produces a single hash representing the entire audit chain.
        """

        entries = self.store.get_all_entries()

        if not entries:
            return "GENESIS"

        combined = []

        for entry in entries:
            combined.append(entry["entry_hash"])

        joined = "".join(combined)

        return hashlib.sha256(joined.encode()).hexdigest()

    # -----------------------------------------------------------------
    # EXPORT AUDIT SNAPSHOT
    # -----------------------------------------------------------------

    def export_audit_snapshot(self):

        report = self.verify_full_chain()

        snapshot = {
            "audit_report": report.to_dict(),
            "audit_hash": report.hash(),
            "chain_fingerprint": self.compute_chain_fingerprint(),
            "exported_at": datetime.utcnow().isoformat() + "Z"
        }

        snapshot_hash = self.hash_data(snapshot)
        snapshot["snapshot_hash"] = snapshot_hash

        return snapshot
    def verify_audit_snapshot(self, snapshot):

        # Step 1: Verify snapshot integrity
        recalculated_snapshot_hash = self.hash_data({
            "audit_report": snapshot["audit_report"],
            "audit_hash": snapshot["audit_hash"],
            "chain_fingerprint": snapshot["chain_fingerprint"],
            "exported_at": snapshot["exported_at"]
        })

        if snapshot["snapshot_hash"] != recalculated_snapshot_hash:
            raise AuditChainError("Snapshot integrity failed")

        # Step 2: Verify audit report consistency
        report = AuditReport(
            total_entries=snapshot["audit_report"]["total_entries"],
            valid=snapshot["audit_report"]["valid"],
            details=snapshot["audit_report"]["details"]
        )

        if report.hash() != snapshot["audit_report"]["audit_hash"]:
            raise AuditChainError("Audit report hash mismatch")

        # Step 3: Verify chain fingerprint matches current state
        current_fingerprint = self.compute_chain_fingerprint()

        if snapshot["chain_fingerprint"] != current_fingerprint:
            raise AuditChainError("Chain fingerprint mismatch")

        return True 