# ecosystems/afriride/core/constitutional/decision_trace.py

"""
AFRIRIDE DECISION TRACE

This module constructs and hashes deterministic decision traces.

A decision trace is the canonical, replayable record of:
- the command issued
- guard evaluations
- state transition
- emitted events

REQUIREMENTS:
- Deterministic structure
- Stable serialization
- No runtime entropy
- Replay-safe

Used by:
- runtime_adapter
- proof generation
- replay validation
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List
import hashlib
import json


# =========================================================
# ✅ SAFE SERIALIZATION (CRITICAL)
# =========================================================

def _serialize(obj: Any) -> Any:
    """
    Convert objects into deterministic, JSON-safe structures.
    """

    if obj is None:
        return None

    # ✅ dataclass → dict
    if is_dataclass(obj):
        return _serialize(asdict(obj))

    # ✅ dict → recursively sort keys
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in sorted(obj.items())}

    # ✅ list / tuple → ordered serialization
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]

    # ✅ primitive types
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # ✅ fallback: string representation (stable requirement)
    return str(obj)


# =========================================================
# ✅ DECISION TRACE BUILDER
# =========================================================

def build_decision_trace(
    trace_id: str,
    command: Any,
    guards: List[Dict],
    before: Dict,
    after: Dict,
    events: List[Any]
) -> Dict:
    """
    Builds a normalized decision trace.

    All fields are serialized into deterministic structures.
    """

    trace = {
        "trace_id": trace_id,

        "command": _serialize(
            asdict(command)
            if hasattr(command, "__dataclass_fields__")
            else command
        ),

        "guards": _serialize(guards),

        "state_transition": {
            "before": _serialize(before),
            "after": _serialize(after),
        },

        "events": _serialize(
            [str(e) for e in events]  # enforce stable event representation
        ),
    }

    return trace


# =========================================================
# ✅ HASH FUNCTION (CRYPTOGRAPHIC PROOF)
# =========================================================

def hash_trace(trace: Dict) -> str:
    """
    Computes SHA256 hash of the decision trace.

    Guarantees:
    - stable ordering (sort_keys=True)
    - deterministic output
    """

    serialized = json.dumps(
        trace,
        sort_keys=True,
        separators=(",", ":"),  # remove whitespace for strict consistency
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# =========================================================
# ✅ TRACE VERIFY (REPLAY CHECK)
# =========================================================

def verify_trace(original_trace: Dict, replay_trace: Dict) -> bool:
    """
    Verifies that two traces are identical (deterministic replay check).
    """

    return hash_trace(original_trace) == hash_trace(replay_trace)


# =========================================================
# ✅ TRACE SUMMARY (OBSERVABILITY HELPER)
# =========================================================

def summarize_trace(trace: Dict) -> Dict:
    """
    Lightweight summary for logging / metrics.
    """

    return {
        "trace_id": trace.get("trace_id"),
        "command": trace.get("command", {}).get("type")
        if isinstance(trace.get("command"), dict)
        else str(trace.get("command")),
        "event_count": len(trace.get("events", [])),
        "guard_count": len(trace.get("guards", [])),
    }