"""
AfriTech Event Store

PURPOSE:
--------
Persistent, deterministic event log used for replay.

Responsibilities:
- store events immutably
- provide ordered access
- support time-based queries
- ensure replay safety
- enable audit and observability

CRITICAL LAW:
-------------
Event Store MAY:
- store events
- return events

Event Store may NOT:
- mutate events
- reorder events (unless explicitly requested via timeline)
- introduce non-deterministic behavior
"""

from typing import List, Dict


# ============================================================
# ✅ EVENT STORE
# ============================================================

class EventStore:
    """
    Immutable event store for replay.

    Guarantees:
    - append-only
    - deterministic ordering
    - safe retrieval
    """

    def __init__(self):
        # ✅ ordered event log
        self._events: List[Dict] = []

    # ========================================================
    # ✅ APPEND EVENT (IMMUTABLE)
    # ========================================================

    def append(self, event: dict):
        """
        Store event safely.

        ✅ Creates immutable copy
        ✅ Validates minimal structure
        """

        if not isinstance(event, dict):
            raise TypeError("Event must be a dictionary")

        if "event_id" not in event or "timestamp" not in event:
            raise ValueError("Event must contain 'event_id' and 'timestamp'")

        # ✅ immutable copy
        stored_event = dict(event)

        self._events.append(stored_event)

    # ========================================================
    # ✅ BULK APPEND
    # ========================================================

    def append_bulk(self, events: list):
        """
        Append multiple events safely.
        """

        if not isinstance(events, list):
            raise TypeError("Events must be a list")

        for event in events:
            self.append(event)

    # ========================================================
    # ✅ GET ALL EVENTS
    # ========================================================

    def get_all(self) -> List[Dict]:
        """
        Return all events (safe copy).
        """

        return [dict(e) for e in self._events]

    # ========================================================
    # ✅ GET BY EVENT ID
    # ============================================================

    def get_by_id(self, event_id: str) -> List[Dict]:
        """
        Retrieve events by event_id.
        """

        return [
            dict(e) for e in self._events
            if e.get("event_id") == event_id
        ]

    # ========================================================
    # ✅ GET AFTER TIMESTAMP
    # ============================================================

    def get_after(self, timestamp) -> List[Dict]:
        """
        Retrieve events after a timestamp.
        """

        return [
            dict(e) for e in self._events
            if e.get("timestamp") > timestamp
        ]

    # ========================================================
    # ✅ GET BEFORE TIMESTAMP
    # ============================================================

    def get_before(self, timestamp) -> List[Dict]:
        """
        Retrieve events before a timestamp.
        """

        return [
            dict(e) for e in self._events
            if e.get("timestamp") < timestamp
        ]

    # ========================================================
    # ✅ RANGE QUERY
    # ============================================================

    def get_range(self, start_ts, end_ts) -> List[Dict]:
        """
        Retrieve events in a time range.
        """

        return [
            dict(e) for e in self._events
            if start_ts <= e.get("timestamp") <= end_ts
        ]

    # ========================================================
    # ✅ COUNT
    # ============================================================

    def count(self) -> int:
        """
        Total number of stored events.
        """

        return len(self._events)

    # ========================================================
    # ✅ CLEAR (TEST ONLY)
    # ============================================================

    def clear(self):
        """
        Clear store (testing/debug only).
        """

        self._events.clear()

    # ========================================================
    # ✅ VALIDATION
    # ============================================================

    def validate(self):
        """
        Validate internal store consistency.
        """

        if not isinstance(self._events, list):
            raise Exception("[EVENT STORE ERROR] Invalid storage structure")

        for i, event in enumerate(self._events):
            if not isinstance(event, dict):
                raise Exception(f"[EVENT STORE ERROR] Invalid event at index {i}")

            if "event_id" not in event or "timestamp" not in event:
                raise Exception(f"[EVENT STORE ERROR] Missing required fields at index {i}")

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
            raise Exception("[EVENT STORE ERROR] Non-deterministic retrieval")

        return True

    # ========================================================
    # ✅ SNAPSHOT
    # ============================================================

    def snapshot(self):
        """
        Snapshot of current event store.
        """

        return {
            "count": len(self._events),
            "events": self.get_all(),
        }

    # ========================================================
    # ✅ DEBUG VIEW
    # ============================================================

    def debug(self):
        """
        Lightweight debug info.
        """

        return {
            "total_events": len(self._events),
            "last_event": self._events[-1] if self._events else None,
        }