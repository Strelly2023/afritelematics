# ecosystems/afriride/core/infrastructure/persistence/replay_hasher.py

"""
REPLAY HASHER

Provides deterministic hashing for event sequences.

Used for:
- replay verification
- determinism checks
- failure demo validation

Strict requirements:
- stable serialization
- deterministic ordering
- no runtime entropy
"""

import hashlib
import json
from typing import List, Any


def _serialize_event(event: Any) -> Any:
    """
    Convert events into stable string/dict representation.
    """

    # If already primitive
    if isinstance(event, (str, int, float, bool)):
        return event

    # If dict → sort keys
    if isinstance(event, dict):
        return {k: _serialize_event(v) for k, v in sorted(event.items())}

    # If list → keep order
    if isinstance(event, list):
        return [_serialize_event(e) for e in event]

    # Fallback → string
    return str(event)


def hash_events(events: List[Any]) -> str:
    """
    Compute deterministic hash of an event list.
    """

    normalized = [_serialize_event(e) for e in events]

    serialized = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":")  # strict consistency
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()