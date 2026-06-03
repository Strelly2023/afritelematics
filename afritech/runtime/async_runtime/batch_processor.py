"""
AfriTech Batch Processor

PURPOSE:
--------
Executes events in batches WITHOUT altering:
- event ordering (within queue constraints)
- event semantics
- replay determinism

CRITICAL LAW:
-------------
Batching MAY:
- improve throughput
- reduce overhead

Batching MAY NOT:
- change event meaning
- reorder events improperly
- merge semantics across events
"""

from afritech.runtime.async_runtime.replay_executor import execute_event
from afritech.runtime.guards import (
    enforce_event_integrity,
    enforce_semantic_consistency,
)


# ============================================================
# ✅ MAIN BATCH PROCESSOR
# ============================================================

def process_batch(events: list, context):
    """
    Process a batch of events safely.

    Guarantees:
    - order preserved
    - independent execution per event
    - no shared mutation
    """

    if not isinstance(events, list):
        raise TypeError("Batch must be a list of events")

    results = []

    for event in events:
        result = process_single_event(event, context)
        results.append(result)

    return results


# ============================================================
# ✅ SINGLE EVENT EXECUTION (BATCH-SAFE)
# ============================================================

def process_single_event(event: dict, context):
    """
    Executes a single event within a batch.

    Ensures:
    - full guard enforcement
    - independent processing
    """

    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")

    # Preserve original state
    original_event = dict(event)

    # Execute event (delegates to replay executor)
    result = execute_event(event, context)

    # Enforce integrity
    enforce_event_integrity(original_event, result)
    enforce_semantic_consistency(original_event, result)

    return result


# ============================================================
# ✅ PARALLEL-SAFE BATCH (FUTURE EXTENSION)
# ============================================================

def process_batch_parallel(events: list, context, executor=None):
    """
    OPTIONAL: Parallel batch execution

    IMPORTANT:
    - Must preserve deterministic ordering
    - Use only if execution is safe
    """

    if executor is None:
        # fallback to sequential
        return process_batch(events, context)

    futures = []

    for event in events:
        futures.append(
            executor.submit(process_single_event, event, context)
        )

    results = []

    for future in futures:
        results.append(future.result())

    return results


# ============================================================
# ✅ SAFE BATCH SPLITTING
# ============================================================

def split_into_batches(events: list, batch_size: int):
    """
    Split events into deterministic chunks.

    Does NOT reorder events.
    """

    if batch_size <= 0:
        raise ValueError("Batch size must be > 0")

    batches = []

    for i in range(0, len(events), batch_size):
        batches.append(events[i:i + batch_size])

    return batches


# ============================================================
# ✅ CONDITIONAL BATCH EXECUTION
# ============================================================

def process_with_dynamic_batching(events: list, context):
    """
    Applies runtime batch size dynamically.

    Uses:
    - context.policy["batch_size"]
    """

    batch_size = context.policy.get("batch_size", 1)

    if batch_size <= 1:
        return process_batch(events, context)

    batches = split_into_batches(events, batch_size)

    results = []

    for batch in batches:
        batch_results = process_batch(batch, context)
        results.extend(batch_results)

    return results


# ============================================================
# ✅ BATCH INTEGRITY CHECK
# ============================================================

def validate_batch_integrity(events: list):
    """
    Ensures batch is safe before execution.

    Checks:
    - no None values
    - correct structure
    """

    for event in events:
        if event is None:
            raise Exception(
                "[BATCH ERROR] Null event detected in batch"
            )

        if not isinstance(event, dict):
            raise Exception(
                "[BATCH ERROR] Invalid event type"
            )


# ============================================================
# ✅ DEBUG / TRACE SUPPORT
# ============================================================

def trace_batch(events: list):
    """
    Lightweight trace of batch content.
    Does NOT modify anything.
    """

    return {
        "batch_size": len(events),
        "event_ids": [e.get("event_id") for e in events],
    }