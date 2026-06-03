"""
AfriTech Backpressure Controller

PURPOSE:
--------
Prevents system overload and stabilizes execution under high load.

Responsibilities:
- detect queue pressure
- signal adaptive layer
- adjust runtime behavior (batch size, scheduling hints)
- protect system from collapse

CRITICAL LAW:
-------------
Backpressure controller MAY:
- influence execution rate
- adjust batching behavior
- signal prioritization

Backpressure controller may NOT:
- alter event content
- change execution meaning
- interfere with replay determinism
"""

from afritech.runtime.guards import enforce_policy_boundary


# ============================================================
# ✅ PRESSURE DETECTION
# ============================================================

def detect_pressure(queue_runtime, threshold: int = 1000):
    """
    Detect queues under pressure.

    Returns:
        dict {queue_name: queue_size}
    """

    pressure_map = {}

    for queue_name in queue_runtime.list_queues():
        size = queue_runtime.get_queue_length(queue_name)

        if size >= threshold:
            pressure_map[queue_name] = size

    return pressure_map


# ============================================================
# ✅ GLOBAL PRESSURE METRICS
# ============================================================

def compute_pressure_metrics(queue_runtime):
    """
    Compute global pressure signals.

    Returns:
        dict with metrics for adaptive layer
    """

    snapshot = queue_runtime.snapshot()

    total_events = sum(snapshot.values())
    max_queue = max(snapshot.values()) if snapshot else 0
    active_queues = len(snapshot)

    return {
        "total_events": total_events,
        "max_queue_depth": max_queue,
        "active_queues": active_queues,
    }


# ============================================================
# ✅ APPLY BACKPRESSURE POLICY
# ============================================================

def apply_backpressure(context, pressure_map: dict):
    """
    Adjust runtime policy based on pressure.

    NOTE:
    - Only modifies operational parameters
    - Must pass guard enforcement
    """

    if not pressure_map:
        return context.policy

    policy = context.policy

    # Example adjustments
    policy["batch_size"] = min(policy.get("batch_size", 1) * 2, 1000)
    policy["retry_limit"] = max(policy.get("retry_limit", 1), 1)

    # Ensure we did not violate boundaries
    enforce_policy_boundary(policy)

    return policy


# ============================================================
# ✅ PRIORITY QUEUE ORDERING
# ============================================================

def prioritize_queues(queue_runtime, pressure_map: dict):
    """
    Reorder queues based on load.

    Heavily loaded queues first.
    """

    snapshot = queue_runtime.snapshot()

    # Sort queues by size descending
    sorted_queues = sorted(
        snapshot.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return [queue_name for queue_name, _ in sorted_queues]


# ============================================================
# ✅ BACKPRESSURE-AWARE SCHEDULING INPUT
# ============================================================

def get_scheduling_order(queue_runtime, threshold=1000):
    """
    Provides scheduler with optimal queue execution order.

    Combines:
    - normal queues
    - pressured queues (prioritized)
    """

    pressure_map = detect_pressure(queue_runtime, threshold)

    if not pressure_map:
        return queue_runtime.list_queues()

    return prioritize_queues(queue_runtime, pressure_map)


# ============================================================
# ✅ LOAD SHEDDING (FUTURE SAFE)
# ============================================================

def should_throttle(queue_runtime, max_global_events=10000):
    """
    Determines if system should reduce intake rate.

    Returns:
        True if system overloaded
    """

    total = queue_runtime.total_size()

    return total >= max_global_events


# ============================================================
# ✅ ADAPTATION SIGNAL GENERATOR
# ============================================================

def generate_adaptive_signal(queue_runtime):
    """
    Converts pressure into signals for adaptive layer.

    Output example:
    {
        "queue_pressure": 85,
        "high_load": True
    }
    """

    total = queue_runtime.total_size()
    snapshot = queue_runtime.snapshot()

    if not snapshot:
        return {
            "queue_pressure": 0,
            "high_load": False,
        }

    max_depth = max(snapshot.values())

    return {
        "queue_pressure": max_depth,
        "high_load": max_depth > 1000,
    }


# ============================================================
# ✅ SAFE BACKPRESSURE LOOP HOOK
# ============================================================

def manage_backpressure(queue_runtime, context, threshold=1000):
    """
    Main backpressure hook.

    Steps:
    1. Detect pressure
    2. Adjust policy
    3. Provide scheduling order
    """

    pressure_map = detect_pressure(queue_runtime, threshold)

    # Apply policy updates safely
    apply_backpressure(context, pressure_map)

    # Determine scheduling order
    scheduling_order = get_scheduling_order(queue_runtime, threshold)

    return {
        "pressure_detected": bool(pressure_map),
        "pressure_map": pressure_map,
        "scheduling_order": scheduling_order,
    }


# ============================================================
# ✅ DEBUG / TRACE
# ============================================================

def trace_backpressure(queue_runtime):
    """
    Debug output for system monitoring
    """

    return {
        "queues": queue_runtime.snapshot(),
        "total_events": queue_runtime.total_size(),
    }