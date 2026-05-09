import hashlib
import json
from pathlib import Path
from datetime import datetime


class TranscriptPersistenceError(Exception):
    """Raised when transcript persistence fails"""
    pass


# -----------------------------------------------------------------
# TRANSCRIPT STORE (IMMUTABLE LEDGER)
# -----------------------------------------------------------------

class TranscriptStore:

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.store_path = self.base_path / "evaluation/persistence/store"

        # ✅ Ensure directory exists
        self.store_path.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # CANONICAL SERIALIZATION (DETERMINISTIC)
    # -----------------------------------------------------------------

    def canonical_json(self, data):
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")  # ✅ eliminates whitespace variation
        )

    def hash_data(self, data):
        return hashlib.sha256(
            self.canonical_json(data).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # FILE SAFETY
    # -----------------------------------------------------------------

    def assert_exists(self, path: Path):
        if not path.exists():
            raise TranscriptPersistenceError(f"File not found: {path}")

    # -----------------------------------------------------------------
    # CHAINING (IMMUTABLE AUDIT STRUCTURE)
    # -----------------------------------------------------------------

    def get_latest_entry(self):
        files = sorted(self.store_path.glob("*.json"))
        if not files:
            return None

        latest_file = files[-1]
        self.assert_exists(latest_file)

        with open(latest_file, "r") as f:
            return json.load(f)

    def compute_previous_hash(self):
        latest = self.get_latest_entry()

        # ✅ Canonical genesis definition
        if not latest:
            return "GENESIS"

        return latest.get("entry_hash")

    # -----------------------------------------------------------------
    # STORE TRANSCRIPT
    # -----------------------------------------------------------------

    def store_transcript(self, transcript):

        transcript_data = transcript.to_dict()

        previous_hash = self.compute_previous_hash()

        # ✅ Construct entry (canonical fields only)
        entry = {
            "transcript": transcript_data,
            "transcript_hash": transcript.hash(),
            "previous_hash": previous_hash,
            "stored_at": datetime.utcnow().isoformat() + "Z"
        }

        # ✅ Compute entry hash BEFORE writing
        entry_hash = self.hash_data(entry)
        entry["entry_hash"] = entry_hash

        file_name = f"{entry_hash}.json"
        file_path = self.store_path / file_name

        # ✅ Canonical write (NOT pretty JSON)
        with open(file_path, "w") as f:
            f.write(self.canonical_json(entry))

        return entry

    # -----------------------------------------------------------------
    # LOAD & VERIFY SINGLE ENTRY
    # -----------------------------------------------------------------

    def load_entry(self, entry_hash):

        file_path = self.store_path / f"{entry_hash}.json"
        self.assert_exists(file_path)

        with open(file_path, "r") as f:
            return json.load(f)

    def verify_entry(self, entry):

        expected_hash = entry.get("entry_hash")

        # ✅ Rebuild canonical hash input (EXCLUDING entry_hash)
        recalculated = self.hash_data({
            "transcript": entry["transcript"],
            "transcript_hash": entry["transcript_hash"],
            "previous_hash": entry["previous_hash"],
            "stored_at": entry["stored_at"]
        })

        if expected_hash != recalculated:
            raise TranscriptPersistenceError("Entry hash mismatch")

        return True

    # -----------------------------------------------------------------
    # FULL CHAIN VERIFICATION
    # -----------------------------------------------------------------

    def verify_chain(self):

        files = sorted(self.store_path.glob("*.json"))

        previous_hash = "GENESIS"

        for file in files:

            self.assert_exists(file)

            with open(file, "r") as f:
                entry = json.load(f)

            # ✅ Verify entry integrity
            self.verify_entry(entry)

            # ✅ Verify chain continuity
            if entry["previous_hash"] != previous_hash:
                raise TranscriptPersistenceError(
                    f"Chain integrity violation at {file.name}"
                )

            previous_hash = entry["entry_hash"]

        return True

    # -----------------------------------------------------------------
    # QUERY INTERFACE
    # -----------------------------------------------------------------

    def list_entries(self):
        return sorted([f.name for f in self.store_path.glob("*.json")])

    def get_all_entries(self):
        entries = []

        for file in sorted(self.store_path.glob("*.json")):
            self.assert_exists(file)

            with open(file, "r") as f:
                entries.append(json.load(f))

        return entries

    # -----------------------------------------------------------------
    # OPTIONAL: GET LATEST HASH (FAST ACCESS)
    # -----------------------------------------------------------------

    def get_latest_hash(self):
        latest = self.get_latest_entry()
        if not latest:
            return "GENESIS"
        return latest.get("entry_hash")
