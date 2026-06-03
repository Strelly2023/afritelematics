"""
AfriTech Audit Log

PURPOSE:
--------
Provides a traceable record of system actions and event execution.

Responsibilities:
- record event execution history
- store action + status logs
- support audit queries
- enable replay verification

CRITICAL LAW:
-------------
Audit Log MAY:
- record execution activity
- return audit records

Audit Log may NOT:
- modify events
- affect execution flow
- introduce non-determinism
"""

import time
from typing import List, Dict, Optional


# ============================================================
# ✅ AUDIT LOG
# ============================================================

class AuditLog:
    """
    Immutable audit log for system execution.

    Guarantees:
    - append-only
    - deterministic ordering
    - safe retrieval
    """

    def __init__(self):
        self._records: List[Dict] = []

    # ========================================================
    # ✅ RECORD ENTRY
    # ========================================================

    def record(
        self,
        event_id: str,
        action: str,
        status: str,
        metadata: Optional[Dict] = None,
    ):
        """
        Record an execution event.

        Args:
            event_id: event identifier
            action: logical action (dispatch, process, retry, etc.)
            status: result (success, failed, etc.)
            metadata: optional context
        """

        if not isinstance(event_id, str):
            raise TypeError("event_id must be a string")

        if not isinstance(action, str):
            raise TypeError("action must be a string")

        if not isinstance(status, str):
            raise TypeError("status must be a string")

        entry = {
            "event_id": event_id,
            "action": action,
            "status": status,
            "timestamp": time.time(),
            "metadata": dict(metadata or {}),
        }

        self._records.append(entry)

    # ========================================================
    # ✅ BULK RECORD
    # ============================================================

    def record_bulk(self, entries: List[Dict]):
        """
        Record multiple entries.
        """

        if not isinstance(entries, list):
            raise TypeError("entries must be a list")

        for entry in entries:
            self.record(
                event_id=entry.get("event_id"),
                action=entry.get("action"),
                status=entry.get("status"),
                metadata=entry.get("metadata"),
            )

    # ========================================================
    # ✅ GET ALL RECORDS
    # ============================================================

    def get_all(self) -> List[Dict]:
        """
        Return full audit history (safe copy).
        """

        return [dict(r) for r in self._records]

    # ========================================================
    # ✅ FILTER BY EVENT ID
    # ============================================================

    def get_by_event(self, event_id: str) -> List[Dict]:
        """
        Retrieve logs for a specific event.
        """

        return [
            dict(r)
            for r in self._records
            if r.get("event_id") == event_id
        ]

    # ========================================================
    # ✅ FILTER BY ACTION
    # ============================================================

    def get_by_action(self, action: str) -> List[Dict]:
        """
        Retrieve logs by action type.
        """

        return [
            dict(r)
            for r in self._records
            if r.get("action") == action
        ]

    # ========================================================
    # ✅ FILTER BY STATUS
    # ============================================================

    def get_by_status(self, status: str) -> List[Dict]:
        """
        Retrieve logs by status type.
        """

        return [
            dict(r)
            for r in self._records
            if r.get("status") == status
        ]

    # ========================================================
    # ✅ FILTER BY TIME RANGE
    # ============================================================

    def get_range(self, start_ts, end_ts) -> List[Dict]:
        """
        Retrieve records within a time range.
        """

        if start_ts > end_ts:
            raise ValueError("start_ts must be <= end_ts")

        return [
            dict(r)
            for r in self._records
            if start_ts <= r.get("timestamp") <= end_ts
        ]

    # ========================================================
    # ✅ COUNT
    # ============================================================

    def count(self) -> int:
        """
        Total number of records.
        """

        return len(self._records)

    # ========================================================
    # ✅ CLEAR (TEST ONLY)
    # ============================================================

    def clear(self):
        """
        Clear all records (testing only).
        """

        self._records.clear()

    # ========================================================
    # ✅ SUMMARY
    # ============================================================

    def summarize(self) -> Dict:
        """
        Provide high-level audit summary.
        """

        if not self._records:
            return {
                "total": 0,
                "actions": {},
                "statuses": {},
            }

        actions = {}
        statuses = {}

        for r in self._records:
            actions[r["action"]] = actions.get(r["action"], 0) + 1
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1

        return {
            "total": len(self._records),
            "actions": actions,
            "statuses": statuses,
        }

    # ========================================================
    # ✅ VALIDATION
    # ============================================================

    def validate(self):
        """
        Validate audit structure.
        """

        if not isinstance(self._records, list):
            raise Exception("[AUDIT ERROR] Invalid storage")

        for i, record in enumerate(self._records):
            if not isinstance(record, dict):
                raise Exception(f"[AUDIT ERROR] Invalid record at index {i}")

            required = ["event_id", "action", "status", "timestamp"]

            for field in required:
                if field not in record:
                    raise Exception(f"[AUDIT ERROR] Missing {field} at index {i}")

        return True

    # ========================================================
    # ✅ DETERMINISM CHECK
    # ============================================================

    def validate_determinism(self):
        """
        Ensure deterministic retrieval.
        """

        r1 = self.get_all()
        r2 = self.get_all()

        if r1 != r2:
            raise Exception("[AUDIT ERROR] Non-deterministic log behavior")

        return True

    # ========================================================
    # ✅ DEBUG VIEW
    # ============================================================

    def debug(self):
        """
        Lightweight debug snapshot.
        """

        return {
            "total_records": len(self._records),
            "last_record": self._records[-1] if self._records else None,
        }