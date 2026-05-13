# ecosystems/afriride/core/observability/decision_metrics.py

"""
AFRIRIDE DECISION METRICS

This module provides observability metrics for:
- decision determinism
- replay validation
- execution tracing

This is intentionally minimal and focused.

Primary KPI:
    Decision Determinism Rate (DDR)

All metrics must remain:
- deterministic
- replay-safe
- computation-only (no external I/O)
"""

from typing import Dict


# =========================================================
# ✅ CORE KPI: DECISION DETERMINISM RATE (DDR)
# =========================================================

def compute_ddr(original_hash: str, replay_hash: str) -> float:
    """
    Computes Decision Determinism Rate.

    Returns:
        1.0 → deterministic (perfect match)
        0.0 → nondeterministic (mismatch)
    """
    return 1.0 if original_hash == replay_hash else 0.0


# =========================================================
# ✅ TRACE COMPARISON
# =========================================================

def compare_hashes(original_hash: str, replay_hash: str) -> Dict:
    """
    Compares two hashes and returns structured output.
    """
    match = (original_hash == replay_hash)

    return {
        "match": match,
        "original": original_hash,
        "replay": replay_hash,
        "delta": None if match else {
            "reason": "hash_mismatch_detected"
        }
    }


# =========================================================
# ✅ METRIC RECORD BUILDER
# =========================================================

def build_decision_metric(
    trace_id: str,
    original_hash: str,
    replay_hash: str
) -> Dict:
    """
    Builds a structured decision metric record.

    This can be logged, stored, or exported.
    """

    ddr = compute_ddr(original_hash, replay_hash)

    return {
        "trace_id": trace_id,
        "decision_hash": original_hash,
        "replay_hash": replay_hash,
        "determinism_match": original_hash == replay_hash,
        "ddr": ddr,
    }


# =========================================================
# ✅ AGGREGATED METRICS
# =========================================================

def aggregate_ddr(records: list) -> float:
    """
    Computes overall determinism rate across multiple executions.
    """

    if not records:
        return 1.0  # neutral (no failures)

    matches = sum(1 for r in records if r.get("determinism_match"))
    total = len(records)

    return matches / total


# =========================================================
# ✅ VALIDATION (STRICT CHECK)
# =========================================================

def assert_deterministic(original_hash: str, replay_hash: str):
    """
    Enforces strict determinism (raises exception if violated).
    """

    if original_hash != replay_hash:
        raise Exception(
            "Determinism violation: original and replay hashes differ"
        )


# =========================================================
# ✅ LIGHTWEIGHT SUMMARY (LOGGING)
# =========================================================

def summarize_metric(record: Dict) -> Dict:
    """
    Produces compact summary for logs/observability.
    """

    return {
        "trace_id": record.get("trace_id"),
        "ddr": record.get("ddr"),
        "match": record.get("determinism_match"),
    }
