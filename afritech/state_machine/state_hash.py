# afritech/state_machine/state_hash.py

"""
AfriTech State Hashing Module

Purpose:
Provide canonical hashing for:
- state identity
- transitions
- transition sequences
- replay validation
- proof binding

Guarantees:
- deterministic hashing
- replay invariance
- structural consistency
- tamper detection

Used by:
- state_engine
- state_validator
- trace integration
- proof system
"""

import hashlib
import json
from typing import Dict, Any, List


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class StateHashError(Exception):
    """Raised when hashing fails or inputs are invalid"""
    pass


# -----------------------------------------------------------------
# CANONICAL JSON
# -----------------------------------------------------------------

def canonical_json(data: Dict[str, Any]) -> str:
    """
    Deterministic JSON serialization
    """

    try:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    except Exception as e:
        raise StateHashError(f"canonicalization_failed: {e}")


# -----------------------------------------------------------------
# GENERIC HASH
# -----------------------------------------------------------------

def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_obj(data: Dict[str, Any]) -> str:
    return hash_bytes(canonical_json(data).encode())


# -----------------------------------------------------------------
# STATE HASH
# -----------------------------------------------------------------

def hash_state(state: str) -> str:
    """
    Hash state identity
    """

    if not isinstance(state, str):
        raise StateHashError("invalid_state")

    return hashlib.sha256(state.encode()).hexdigest()


# -----------------------------------------------------------------
# TRANSITION HASH
# -----------------------------------------------------------------

def hash_transition(transition: Dict[str, Any]) -> str:
    """
    Hash a transition record

    REQUIRED FIELDS:
    - id
    - from
    - to
    """

    required = ["id", "from", "to"]

    for field in required:
        if field not in transition:
            raise StateHashError(f"missing_transition_field: {field}")

    base = {
        "id": transition["id"],
        "from": transition["from"],
        "to": transition["to"],
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# TRANSITION RECORD HASH (WITH CONTEXT)
# -----------------------------------------------------------------

def hash_transition_record(record: Dict[str, Any]) -> str:
    """
    Hash full transition record including state progression

    REQUIRED:
    - id
    - from
    - to
    - index
    - previous_hash
    """

    required = ["id", "from", "to", "index", "previous_hash"]

    for f in required:
        if f not in record:
            raise StateHashError(f"missing_record_field: {f}")

    base = {
        "index": record["index"],
        "id": record["id"],
        "from": record["from"],
        "to": record["to"],
        "previous_hash": record["previous_hash"],
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# TRANSITION SEQUENCE HASH
# -----------------------------------------------------------------

def hash_transition_sequence(sequence: List[Dict[str, Any]]) -> str:
    """
    Hash entire transition history

    Guarantees:
    - sequence identity
    - replay determinism
    """

    if not isinstance(sequence, list) or not sequence:
        raise StateHashError("invalid_sequence")

    hashes = []

    for record in sequence:

        if "transition_hash" not in record:
            raise StateHashError("missing_transition_hash")

        hashes.append(record["transition_hash"])

    payload = {
        "sequence": hashes
    }

    return hash_obj(payload)


# -----------------------------------------------------------------
# STATE MACHINE SNAPSHOT HASH
# -----------------------------------------------------------------

def hash_state_snapshot(current_state: str, history: List[Dict[str, Any]]) -> str:
    """
    Hash entire state machine snapshot

    Used for:
    - checkpointing
    - replay comparison
    """

    base = {
        "current_state": current_state,
        "history_hash": hash_transition_sequence(history),
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# VERIFY SEQUENCE CONSISTENCY
# -----------------------------------------------------------------

def validate_transition_sequence(sequence: List[Dict[str, Any]]) -> bool:
    """
    Ensure transition hashes match recomputed values
    """

    previous_hash = "GENESIS"

    for i, record in enumerate(sequence):

        expected = hash_transition(record)

        if record.get("transition_hash") != expected:
            raise StateHashError("transition_hash_mismatch")

        # Optional chain validation
        if record.get("previous_hash") != previous_hash:
            raise StateHashError("chain_integrity_broken")

        previous_hash = expected

    return True


# -----------------------------------------------------------------
# REPLAY HASH (FINAL STATE COMMITMENT)
# -----------------------------------------------------------------

def compute_replay_hash(final_state: str, sequence: List[Dict[str, Any]]) -> str:
    """
    Compute replay commitment hash

    Binds:
    - final state
    - execution path
    """

    base = {
        "final_state": final_state,
        "transition_sequence_hash": hash_transition_sequence(sequence),
    }

    return hash_obj(base)


# -----------------------------------------------------------------
# TAMPER DETECTION
# -----------------------------------------------------------------

def is_tampered(sequence: List[Dict[str, Any]]) -> bool:
    """
    Detect if transition sequence has been altered
    """

    try:
        validate_transition_sequence(sequence)
        return False
    except Exception:
        return True


# -----------------------------------------------------------------
# DEBUG
# -----------------------------------------------------------------

def __repr__():
    return "<StateHash deterministic>"