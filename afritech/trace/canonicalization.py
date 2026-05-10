# afritech/trace/canonicalization.py

"""
AfriTech Trace Canonicalization
===============================

Canonicalizes execution traces so that
SEMANTIC EQUIVALENCE produces IDENTICAL hashes.

This module defines the ONLY legal pathway for
trace canonicalization and hashing.

All replay, receipt, and verification logic MUST
use this module exclusively.
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Dict, List


# ---------------------------------------------------------------------
# CANONICALIZATION
# ---------------------------------------------------------------------

def canonicalize_trace(trace) -> List[Dict[str, Any]]:
    """
    Canonicalize a trace into a deterministic list of events.

    Canonicalization guarantees:
    - deterministic event ordering
    - deterministic field ordering
    - no Python-version-dependent serialization
    - no implicit defaults
    """

    trace_dict = trace.to_dict()

    if "events" not in trace_dict:
        raise ValueError("Trace missing 'events' field")

    events = trace_dict["events"]

    if not isinstance(events, list):
        raise ValueError("Trace 'events' must be a list")

    canonical_events: List[Dict[str, Any]] = []

    for event in events:
        if not isinstance(event, dict):
            raise ValueError("Trace event must be a dict")

        # Sort event fields deterministically
        canonical_event = {
            key: event[key]
            for key in sorted(event.keys())
        }

        canonical_events.append(canonical_event)

    # Sort events deterministically by stable semantic keys
    canonical_events.sort(
        key=lambda e: (
            e.get("step", ""),
            e.get("input_hash", ""),
            e.get("output_hash", ""),
        )
    )

    return canonical_events


# ---------------------------------------------------------------------
# HASHING
# ---------------------------------------------------------------------

def hash_canonical_trace(
    canonical_events: List[Dict[str, Any]]
) -> str:
    """
    Compute the canonical trace hash.

    Uses:
    - JSON canonical serialization
    - UTF-8 encoding
    - SHA-256 hashing

    This hash is:
    - deterministic
    - replay-stable
    - cryptographically strong
    """

    payload = json.dumps(
        canonical_events,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return sha256(payload).hexdigest()
