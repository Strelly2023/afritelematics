# afritech/trace/trace_hash.py

"""
AfriTech Trace Hashing Module

Purpose:
Provide canonical hashing for:
- events (atomic execution steps)
- trace roots (global execution commitment)

Guarantees:
- deterministic hashing
- replay invariance
- structural integrity
- tamper detection
"""

import hashlib
import json
from typing import Dict, Any, List


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class TraceHashError(Exception):
    """Raised when hashing or canonicalization fails"""
    pass


# -----------------------------------------------------------------
# CANONICAL JSON (CRITICAL)
# -----------------------------------------------------------------

def canonical_json(data: Dict[str, Any]) -> str:
    """
    Deterministic JSON serialization

    RULES:
    - keys sorted
    - compact separators
    - UTF-8 safe
    """

    try:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except Exception as e:
        raise TraceHashError(f"canonicalization_failed: {e}")


# -----------------------------------------------------------------
# GENERIC HASH
# -----------------------------------------------------------------

def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(data: Dict[str, Any]) -> str:
    return hash_bytes(canonical_json(data).encode())


# -----------------------------------------------------------------
# EVENT HASHING
# -----------------------------------------------------------------

def compute_event_hash(event: Dict[str, Any]) -> str:
    """
    Compute deterministic event hash

    REQUIRED FIELDS:
    - index
    - step
    - parent_event_hash
    - depends_on
    - authority_context_hash
    - input_hash
    - output_hash
    """

    required_fields = [
        "index",
        "step",
        "parent_event_hash",
        "depends_on",
        "authority_context_hash",
        "input_hash",
        "output_hash",
    ]

    for field in required_fields:
        if field not in event:
            raise TraceHashError(f"missing_event_field: {field}")

    base = {
        "index": event["index"],
        "step": event["step"],
        "parent_event_hash": event["parent_event_hash"],
        "depends_on": sorted(event["depends_on"]),
        "authority_context_hash": event["authority_context_hash"],
        "input_hash": event["input_hash"],
        "output_hash": event["output_hash"],
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# EVENT VALIDATION
# -----------------------------------------------------------------

def validate_event(event: Dict[str, Any]) -> bool:
    """
    Ensure event hash is correct
    """

    expected = compute_event_hash(event)

    if event.get("event_hash") != expected:
        raise TraceHashError("event_hash_mismatch")

    return True


# -----------------------------------------------------------------
# TRACE ROOT HASH
# -----------------------------------------------------------------

def compute_trace_root(events: List[Dict[str, Any]]) -> str:
    """
    Compute global trace commitment

    Strategy:
    - ordered list of event_hash
    - canonical aggregation
    """

    if not isinstance(events, list):
        raise TraceHashError("events_must_be_list")

    event_hashes = []

    for e in events:
        if "event_hash" not in e:
            raise TraceHashError("missing_event_hash")

        event_hashes.append(e["event_hash"])

    root_payload = {
        "event_hashes": event_hashes
    }

    return hash_obj(root_payload)


# -----------------------------------------------------------------
# FULL TRACE HASH
# -----------------------------------------------------------------

def compute_trace_hash(trace: Dict[str, Any]) -> str:
    """
    Compute full trace commitment (stronger than root)

    Includes:
    - header fields
    - root hash
    """

    base = {
        "trace_id": trace["trace_id"],
        "request_hash": trace["request_hash"],
        "authority_profile": trace["authority_profile"],
        "epoch_id": trace["epoch_id"],
        "trace_root_hash": trace["trace_root_hash"],
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# TRACE VALIDATION (STRICT)
# -----------------------------------------------------------------

def validate_trace(trace: Dict[str, Any]) -> bool:
    """
    Full trace validation (cryptographic + structural)
    """

    if "events" not in trace:
        raise TraceHashError("missing_events")

    events = trace["events"]

    if not isinstance(events, list) or len(events) == 0:
        raise TraceHashError("invalid_events_structure")

    # -------------------------------------------------------------
    # INDEX CONTIGUITY
    # -------------------------------------------------------------

    for i, e in enumerate(events):
        if e.get("index") != i:
            raise TraceHashError("index_contiguity_violation")

    # -------------------------------------------------------------
    # EVENT VALIDATION
    # -------------------------------------------------------------

    for e in events:
        validate_event(e)

    # -------------------------------------------------------------
    # PARENT CHAIN VALIDATION
    # -------------------------------------------------------------

    for i in range(1, len(events)):
        if events[i]["parent_event_hash"] != events[i-1]["event_hash"]:
            raise TraceHashError("parent_chain_invalid")

    # -------------------------------------------------------------
    # DEPENDENCY VALIDATION (DAG)
    # -------------------------------------------------------------

    for e in events:
        idx = e["index"]

        for dep in e.get("depends_on", []):
            if not isinstance(dep, int) or dep >= idx:
                raise TraceHashError("invalid_dependency_reference")

    # -------------------------------------------------------------
    # ROOT HASH VALIDATION
    # -------------------------------------------------------------

    expected_root = compute_trace_root(events)

    if trace.get("trace_root_hash") != expected_root:
        raise TraceHashError("trace_root_mismatch")

    return True


# -----------------------------------------------------------------
# REPLAY EQUALITY CHECK
# -----------------------------------------------------------------

def compare_traces(trace_a: Dict[str, Any], trace_b: Dict[str, Any]) -> bool:
    """
    Strict equality check between traces

    Used for replay verification
    """

    return canonical_json(trace_a) == canonical_json(trace_b)


# -----------------------------------------------------------------
# IMMUTABILITY CHECK
# -----------------------------------------------------------------

def is_tampered(trace: Dict[str, Any]) -> bool:
    """
    Detect if trace has been corrupted
    """

    try:
        return not validate_trace(trace)
    except TraceHashError:
        return True