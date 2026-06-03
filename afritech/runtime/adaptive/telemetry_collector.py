"""
AfriTech Telemetry Collector

PURPOSE:
--------
Collect runtime metrics for adaptive decision-making.

Responsibilities:
- gather queue metrics
- measure system load
- provide structured telemetry data
- remain read-only (no side effects)

CRITICAL LAW:
-------------
Telemetry Collector MAY:
- observe system state
- report metrics

Telemetry Collector may NOT:
- modify system behavior
- mutate events
- influence execution directly
"""

# ============================================================
# ✅ MAIN TELEMETRY COLLECTION
# ============================================================

def collect_telemetry(context):
    """
    Main telemetry entry point.

    Collects:
    - queue sizes
    - total events
    - active queues
    - policy snapshot
    """

    queue_runtime = _get_queue_runtime(context)

    snapshot = queue_runtime.snapshot()

    return {
        "queue_sizes": snapshot,
        "total_events": _compute_total_events(snapshot),
        "max_queue_depth": _compute_max_depth(snapshot),
        "active_queues": len(snapshot),
        "policy": dict(context.policy),  # ✅ copy (read-only)
    }


# ============================================================
# ✅ HELPER FUNCTIONS
# ============================================================

def _get_queue_runtime(context):
    """
    Safely retrieve queue runtime from context.
    """

    if not hasattr(context, "queue_runtime"):
        raise Exception(
            "[TELEMETRY ERROR] context.queue_runtime is required"
        )

    return context.queue_runtime


def _compute_total_events(snapshot: dict):
    """
    Total number of events in system.
    """

    return sum(snapshot.values()) if snapshot else 0


def _compute_max_depth(snapshot: dict):
    """
    Largest queue size (pressure indicator).
    """

    if not snapshot:
        return 0

    return max(snapshot.values())


# ============================================================
# ✅ DETAILED TELEMETRY (EXTENDED MODE)
# ============================================================

def collect_detailed_telemetry(context):
    """
    More granular telemetry.

    Includes:
    - per-queue statistics
    - average queue depth
    """

    queue_runtime = _get_queue_runtime(context)

    snapshot = queue_runtime.snapshot()

    total = _compute_total_events(snapshot)
    count = len(snapshot)

    avg_depth = (total / count) if count > 0 else 0

    return {
        "queue_sizes": snapshot,
        "total_events": total,
        "max_queue_depth": _compute_max_depth(snapshot),
        "average_queue_depth": avg_depth,
        "active_queues": count,
        "policy": dict(context.policy),
    }


# ============================================================
# ✅ QUEUE PRESSURE MAP
# ============================================================

def get_pressure_map(context, threshold=100):
    """
    Identify queues under pressure.

    Returns:
        dict of queues exceeding threshold
    """

    queue_runtime = _get_queue_runtime(context)

    snapshot = queue_runtime.snapshot()

    pressure = {}

    for queue_name, size in snapshot.items():
        if size >= threshold:
            pressure[queue_name] = size

    return pressure


# ============================================================
# ✅ TELEMETRY SNAPSHOT (LIGHTWEIGHT)
# ============================================================

def get_lightweight_telemetry(context):
    """
    Minimal telemetry for fast evaluation.
    """

    queue_runtime = _get_queue_runtime(context)

    return {
        "total_events": queue_runtime.total_size(),
    }


# ============================================================
# ✅ TELEMETRY VALIDATION
# ============================================================

def validate_telemetry(telemetry: dict):
    """
    Ensures telemetry structure is valid.
    """

    required_fields = [
        "queue_sizes",
        "total_events",
    ]

    for field in required_fields:
        if field not in telemetry:
            raise Exception(
                f"[TELEMETRY ERROR] Missing field: {field}"
            )

    if not isinstance(telemetry["queue_sizes"], dict):
        raise TypeError("queue_sizes must be a dictionary")

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_telemetry_determinism(context):
    """
    Ensures telemetry is stable (no unexpected fluctuation).
    """

    t1 = collect_telemetry(context)
    t2 = collect_telemetry(context)

    if t1 != t2:
        raise Exception(
            "[TELEMETRY ERROR] Non-deterministic telemetry detected"
        )

    return True


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_telemetry(context):
    """
    Debug-friendly telemetry output.

    Does NOT modify system.
    """

    telemetry = collect_telemetry(context)

    return {
        "total_events": telemetry["total_events"],
        "max_queue_depth": telemetry["max_queue_depth"],
        "active_queues": telemetry["active_queues"],
    }