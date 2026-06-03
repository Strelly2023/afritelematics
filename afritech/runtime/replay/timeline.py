"""
AfriTech Timeline

PURPOSE:
--------
Provides deterministic ordering and filtering utilities for events and snapshots.

Responsibilities:
- sort events by timestamp
- filter events by time or id
- ensure stable ordering
- support replay engine logic

CRITICAL LAW:
-------------
Timeline MAY:
- order events
- filter events

Timeline may NOT:
- mutate events
- introduce non-deterministic behavior
"""

from typing import List, Dict, Callable


# ============================================================
# ✅ SORT EVENTS (DETERMINISTIC ORDER)
# ============================================================

def sort_events(events: List[dict]) -> List[dict]:
    """
    Sort events by timestamp (stable).

    Guarantees:
    - deterministic ordering
    - stable sort (preserves insertion for equal timestamps)
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    return sorted(events, key=lambda e: (e.get("timestamp"), e.get("event_id")))


# ============================================================
# ✅ FILTER BY EVENT ID
# ============================================================

def filter_by_event_id(events: List[dict], event_id: str) -> List[dict]:
    """
    Return events matching event_id.
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    return [
        e for e in events
        if e.get("event_id") == event_id
    ]


# ============================================================
# ✅ FILTER BY TIME RANGE
# ============================================================

def filter_by_time_range(events: List[dict], start_ts, end_ts) -> List[dict]:
    """
    Return events within [start_ts, end_ts].
    """

    if start_ts > end_ts:
        raise ValueError("start_ts must be <= end_ts")

    return [
        e for e in events
        if start_ts <= e.get("timestamp") <= end_ts
    ]


# ============================================================
# ✅ FILTER AFTER TIMESTAMP
# ============================================================

def filter_after(events: List[dict], timestamp) -> List[dict]:
    """
    Return events strictly after timestamp.
    """

    return [
        e for e in events
        if e.get("timestamp") > timestamp
    ]


# ============================================================
# ✅ FILTER BEFORE TIMESTAMP
# ============================================================

def filter_before(events: List[dict], timestamp) -> List[dict]:
    """
    Return events strictly before timestamp.
    """

    return [
        e for e in events
        if e.get("timestamp") < timestamp
    ]


# ============================================================
# ✅ MAP EVENTS (NON-MUTATING TRANSFORMATION)
# ============================================================

def map_events(events: List[dict], fn: Callable) -> List[dict]:
    """
    Apply function to each event (returns new list).

    Guarantees:
    - original events NOT modified
    """

    if not callable(fn):
        raise TypeError("fn must be callable")

    return [fn(dict(e)) for e in events]


# ============================================================
# ✅ GROUP BY EVENT ID
# ============================================================

def group_by_event_id(events: List[dict]) -> Dict[str, List[dict]]:
    """
    Group events by event_id.
    """

    grouped = {}

    for event in events:
        eid = event.get("event_id")
        grouped.setdefault(eid, []).append(dict(event))

    return grouped


# ============================================================
# ✅ DEDUPLICATE EVENTS
# ============================================================

def deduplicate(events: List[dict]) -> List[dict]:
    """
    Remove duplicate events based on (event_id, timestamp).
    """

    seen = set()
    unique = []

    for event in events:
        key = (event.get("event_id"), event.get("timestamp"))

        if key not in seen:
            seen.add(key)
            unique.append(dict(event))

    return unique


# ============================================================
# ✅ MERGE TIMELINES
# ============================================================

def merge_timelines(*event_lists: List[dict]) -> List[dict]:
    """
    Merge multiple event lists into a single ordered timeline.
    """

    merged = []

    for events in event_lists:
        if not isinstance(events, list):
            raise TypeError("All inputs must be lists")

        merged.extend(events)

    return sort_events(deduplicate(merged))


# ============================================================
# ✅ TIMELINE WINDOW (PAGINATION)
# ============================================================

def window(events: List[dict], offset: int, limit: int) -> List[dict]:
    """
    Return a slice of the timeline.

    Useful for pagination or partial replay.
    """

    if offset < 0 or limit < 0:
        raise ValueError("offset and limit must be >= 0")

    return [dict(e) for e in events[offset: offset + limit]]


# ============================================================
# ✅ TIMELINE SUMMARY
# ============================================================

def summarize(events: List[dict]) -> dict:
    """
    Provide high-level summary of timeline.
    """

    if not events:
        return {
            "count": 0,
            "start": None,
            "end": None,
            "unique_events": 0,
        }

    event_ids = {e.get("event_id") for e in events}

    timestamps = [e.get("timestamp") for e in events]

    return {
        "count": len(events),
        "start": min(timestamps),
        "end": max(timestamps),
        "unique_events": len(event_ids),
    }


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate(events: List[dict]):
    """
    Ensure timeline structure is valid.
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    for i, event in enumerate(events):
        if not isinstance(event, dict):
            raise Exception(f"[TIMELINE ERROR] Invalid event at index {i}")

        if "event_id" not in event or "timestamp" not in event:
            raise Exception(f"[TIMELINE ERROR] Missing required fields at index {i}")

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_determinism(events: List[dict]):
    """
    Ensure deterministic ordering.
    """

    s1 = sort_events(events)
    s2 = sort_events(events)

    if s1 != s2:
        raise Exception("[TIMELINE ERROR] Non-deterministic sorting")

    return True