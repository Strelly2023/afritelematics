"""
AfriTech Replay Executor

PURPOSE:
--------
Acts as the execution bridge between the async runtime and the
future constitutional replay engine.

Responsibilities:
- Execute events deterministically
- Preserve event integrity
- Enforce execution boundaries
- Prepare integration with replay validators

CRITICAL LAW:
-------------
ReplayExecutor MAY:
- execute event logic
- return results

ReplayExecutor may NOT:
- modify event semantics
- alter identity
- bypass replay validation (future)
"""

from afritech.runtime.guards import (
    enforce_event_integrity,
    enforce_semantic_consistency,
)


# ============================================================
# ✅ MAIN EXECUTION FUNCTION
# ============================================================

def execute_event(event: dict, context):
    """
    Primary execution entry point.

    Steps:
    1. Validate event structure
    2. Preserve original state
    3. Execute deterministic logic (pure, no mutation)
    4. Enforce guards
    5. Return result
    """

    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")

    # --------------------------------------------------------
    # Preserve original for deterministic safety
    # --------------------------------------------------------

    original_event = dict(event)

    # --------------------------------------------------------
    # Deterministic execution (STRICT: NO MUTATION)
    # --------------------------------------------------------

    result = _deterministic_execute(event, context)

    # --------------------------------------------------------
    # Guard enforcement
    # --------------------------------------------------------

    enforce_event_integrity(original_event, result)
    enforce_semantic_consistency(original_event, result)

    return result


# ============================================================
# ✅ DETERMINISTIC EXECUTION CORE
# ============================================================

def _deterministic_execute(event: dict, context):
    """
    Deterministic execution core.

    CRITICAL RULES:
    - MUST NOT mutate the event
    - MUST be pure (same input -> same output)
    - MUST be replay-safe

    Current behavior:
    - identity transformation (safe baseline)

    Future:
    - replaced by replay engine
    """

    # ✅ STRICT: return a shallow copy (no mutation allowed)
    return dict(event)


# ============================================================
# ✅ EXECUTION WITH VALIDATION HOOK (FUTURE CORE BRIDGE)
# ============================================================

def execute_with_validation(event: dict, context, validator=None):
    """
    Future-ready execution pipeline.

    validator:
        optional validation hook (future constitutional validator)
    """

    result = execute_event(event, context)

    if validator:
        validator.validate(result)

    return result


# ============================================================
# ✅ BULK EXECUTION (SAFE, ORDER PRESERVED)
# ============================================================

def execute_batch(events: list, context):
    """
    Executes multiple events deterministically.

    Guarantees:
    - order preserved
    - independent execution
    - no shared mutation
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    results = []

    for event in events:
        result = execute_event(event, context)
        results.append(result)

    return results


# ============================================================
# ✅ SAFE RETRY EXECUTION
# ============================================================

def execute_with_retry(event: dict, context):
    """
    Retry wrapper for execution.

    NOTE:
    - Retries improve reliability
    - MUST NOT change output
    """

    max_attempts = context.policy.get("retry_limit", 1)
    attempt = 0

    while attempt < max_attempts:
        try:
            return execute_event(event, context)

        except Exception as e:
            attempt += 1

            if attempt >= max_attempts:
                raise Exception(
                    f"[REPLAY EXECUTION FAILED] after {attempt} attempts: {str(e)}"
                )


# ============================================================
# ✅ EXECUTION TRACE (OBSERVABILITY ONLY)
# ============================================================

def trace_execution(event: dict, context):
    """
    Lightweight tracing (non-intrusive).

    Does NOT modify event.
    """

    return {
        "event_id": event.get("event_id"),
        "timestamp": event.get("timestamp"),
        "transport_mode": context.policy.get("transport_mode"),
    }


# ============================================================
# ✅ REPLAY SIGNATURE (FUTURE USE)
# ============================================================

def generate_replay_signature(result: dict):
    """
    Generates a deterministic signature of execution result.

    Used for:
    - replay verification
    - audit integrity
    """

    if not isinstance(result, dict):
        raise TypeError("Result must be a dictionary")

    # ✅ Stable deterministic representation
    return str(sorted(result.items()))