import hashlib
import json
from datetime import datetime


class ProofExportError(Exception):
    """Raised when proof export fails"""
    pass


# -----------------------------------------------------------------
# PROOF EXPORT API
# -----------------------------------------------------------------

class ProofExportAPI:

    def __init__(self, transcript_store):
        self.transcript_store = transcript_store

    # -----------------------------------------------------------------
    # CANONICAL JSON
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
    # EXPORT SINGLE PROOF
    # -----------------------------------------------------------------

    def export_proof(self, entry_hash):

        entry = self.transcript_store.load_entry(entry_hash)

        proof = {
            "proof_type": "AFRITECH_EXECUTION_PROOF",
            "entry_hash": entry_hash,
            "transcript": entry["transcript"],
            "transcript_hash": entry["transcript_hash"],
            "previous_hash": entry["previous_hash"],
            "chain_anchor": self.transcript_store.get_latest_hash(),
            "exported_at": datetime.utcnow().isoformat() + "Z"
        }

        proof_hash = self.hash_data(proof)
        proof["proof_hash"] = proof_hash

        return proof

    # -----------------------------------------------------------------
    # EXPORT CHAIN SEGMENT
    # -----------------------------------------------------------------

    def export_chain(self, from_hash=None):

        entries = self.transcript_store.get_all_entries()

        chain = []

        for entry in entries:

            if from_hash and entry["entry_hash"] == from_hash:
                chain = []

            chain.append(entry)

        export = {
            "proof_type": "AFRITECH_CHAIN_PROOF",
            "entries": chain,
            "chain_length": len(chain),
            "exported_at": datetime.utcnow().isoformat() + "Z"
        }

        export_hash = self.hash_data(export)
        export["export_hash"] = export_hash

        return export

    # -----------------------------------------------------------------
    # VERIFY EXPORTED PROOF
    # -----------------------------------------------------------------

    def verify_proof(self, proof):

        expected_hash = proof.get("proof_hash")

        recomputed = self.hash_data({
            "proof_type": proof["proof_type"],
            "entry_hash": proof["entry_hash"],
            "transcript": proof["transcript"],
            "transcript_hash": proof["transcript_hash"],
            "previous_hash": proof["previous_hash"],
            "chain_anchor": proof["chain_anchor"],
            "exported_at": proof["exported_at"]
        })

        if expected_hash != recomputed:
            raise ProofExportError("Proof hash mismatch")

        return True

    # -----------------------------------------------------------------
    # VERIFY EXPORTED CHAIN
    # -----------------------------------------------------------------

    def verify_chain_export(self, export):

        entries = export["entries"]

        previous_hash = "GENESIS"

        for entry in entries:

            recalculated = self.hash_data({
                "transcript": entry["transcript"],
                "transcript_hash": entry["transcript_hash"],
                "previous_hash": entry["previous_hash"],
                "stored_at": entry["stored_at"]
            })

            if entry["entry_hash"] != recalculated:
                raise ProofExportError("Chain entry hash mismatch")

            if entry["previous_hash"] != previous_hash:
                raise ProofExportError("Chain linkage violation")

            previous_hash = entry["entry_hash"]

        recomputed_export_hash = self.hash_data({
            "proof_type": export["proof_type"],
            "entries": export["entries"],
            "chain_length": export["chain_length"],
            "exported_at": export["exported_at"]
        })

        if export["export_hash"] != recomputed_export_hash:
            raise ProofExportError("Export hash mismatch")

        return True
