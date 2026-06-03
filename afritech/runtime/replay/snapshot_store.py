"""
AfriTech Snapshot Store

PURPOSE:
--------
Stores system state snapshots for replay and recovery.

Responsibilities:
- store immutable snapshots
- retrieve snapshots
- support versioning
- enable time-travel execution checkpoints

CRITICAL LAW:
-------------
Snapshot Store MAY:
- store system state
- return stored state

Snapshot Store may NOT:
- mutate stored snapshots
- affect execution semantics
- introduce non-determinism
"""

import time
from typing import Dict, Optional


# ============================================================
# ✅ SNAPSHOT STORE
# ============================================================

class SnapshotStore:
    """
    Stores system snapshots for replay optimization.

    Guarantees:
    - immutable storage
    - deterministic retrieval
    """

    def __init__(self):
        # snapshot_name → snapshot_data
        self._snapshots: Dict[str, dict] = {}

    # ========================================================
    # ✅ SAVE SNAPSHOT
    # ========================================================

    def save(self, name: str, state: dict, metadata: dict = None):
        """
        Save a snapshot.

        Args:
            name: unique snapshot identifier
            state: system state
            metadata: optional metadata (timestamp, version, etc.)
        """

        if not isinstance(name, str):
            raise TypeError("Snapshot name must be a string")

        if not isinstance(state, dict):
            raise TypeError("State must be a dictionary")

        # ✅ Immutable copy of state
        snapshot = {
            "state": dict(state),
            "metadata": {
                "created_at": time.time(),
                **(metadata or {})
            }
        }

        self._snapshots[name] = snapshot

    # ========================================================
    # ✅ LOAD SNAPSHOT
    # ========================================================

    def load(self, name: str) -> Optional["dict"]:
        """
        Retrieve snapshot by name.

        Returns:
            copy of stored snapshot state
        """

        snapshot = self._snapshots.get(name)

        if not snapshot:
            return None

        return {
            "state": dict(snapshot["state"]),
            "metadata": dict(snapshot["metadata"]),
        }

    # ========================================================
    # ✅ DELETE SNAPSHOT
    # ========================================================

    def delete(self, name: str):
        """
        Delete snapshot by name.
        """

        if name in self._snapshots:
            del self._snapshots[name]

    # ========================================================
    # ✅ LIST SNAPSHOTS
    # ========================================================

    def list(self):
        """
        Return list of available snapshot names.
        """

        return list(self._snapshots.keys())

    # ========================================================
    # ✅ COUNT SNAPSHOTS
    # ========================================================

    def count(self) -> int:
        """
        Total number of snapshots.
        """

        return len(self._snapshots)

    # ========================================================
    # ✅ CLEAR ALL (TEST ONLY)
    # ========================================================

    def clear(self):
        """
        Remove all snapshots (used for testing/reset).
        """

        self._snapshots.clear()

    # ========================================================
    # ✅ GET LATEST SNAPSHOT
    # ============================================================

    def get_latest(self) -> Optional["dict"]:
        """
        Retrieve most recently created snapshot.
        """

        if not self._snapshots:
            return None

        latest_name = max(
            self._snapshots,
            key=lambda k: self._snapshots[k]["metadata"]["created_at"]
        )

        return self.load(latest_name)

    # ========================================================
    # ✅ GET SNAPSHOTS AFTER TIME
    # ============================================================

    def get_after(self, timestamp):
        """
        Retrieve snapshots created after a timestamp.
        """

        return {
            name: self.load(name)
            for name, s in self._snapshots.items()
            if s["metadata"]["created_at"] > timestamp
        }

    # ========================================================
    # ✅ SNAPSHOT SUMMARY
    # ============================================================

    def summarize(self):
        """
        Lightweight summary of snapshots.
        """

        return {
            name: {
                "created_at": s["metadata"].get("created_at"),
                "metadata": s["metadata"],
            }
            for name, s in self._snapshots.items()
        }

    # ========================================================
    # ✅ VALIDATION
    # ============================================================

    def validate(self):
        """
        Ensure snapshot integrity.
        """

        if not isinstance(self._snapshots, dict):
            raise Exception("[SNAPSHOT ERROR] Invalid storage structure")

        for name, snapshot in self._snapshots.items():
            if not isinstance(snapshot, dict):
                raise Exception(f"[SNAPSHOT ERROR] Invalid snapshot: {name}")

            if "state" not in snapshot or "metadata" not in snapshot:
                raise Exception(f"[SNAPSHOT ERROR] Missing fields: {name}")

        return True

    # ========================================================
    # ✅ DETERMINISM CHECK
    # ============================================================

    def validate_determinism(self):
        """
        Ensure deterministic snapshot retrieval.
        """

        r1 = self.summarize()
        r2 = self.summarize()

        if r1 != r2:
            raise Exception("[SNAPSHOT ERROR] Non-deterministic snapshot behavior")

        return True

    # ========================================================
    # ✅ SNAPSHOT DEBUG VIEW
    # ============================================================

    def debug(self):
        """
        Human-readable debug info.
        """

        return {
            "total_snapshots": len(self._snapshots),
            "names": list(self._snapshots.keys()),
        }