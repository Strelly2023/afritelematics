"""
AfriTech Partition Router

PURPOSE:
--------
Determines which partition an event belongs to.

Responsibilities:
- compute deterministic partition assignment
- ensure stable mapping (important for replay)
- distribute load evenly across partitions
- support pluggable partition strategies

CRITICAL LAW:
-------------
Partition Router MAY:
- assign partitions
- distribute load

Partition Router may NOT:
- modify event content
- alter execution semantics
"""

import hashlib


# ============================================================
# ✅ CONFIGURATION
# ============================================================

DEFAULT_PARTITION_COUNT = 10


# ============================================================
# ✅ MAIN PARTITION RESOLUTION
# ============================================================

def resolve_partition(event: dict, context):
    """
    Determines partition for an event.

    Strategy:
    - hash(event_id) → partition index
    - ensures consistent distribution
    """

    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")

    event_id = event.get("event_id")

    if not event_id:
        return "p_default"

    partition_count = context.policy.get(
        "partition_count",
        DEFAULT_PARTITION_COUNT
    )

    index = _stable_hash(event_id) % partition_count

    return f"p{index}"


# ============================================================
# ✅ STABLE HASH FUNCTION (CRITICAL)
# ============================================================

def _stable_hash(value: str) -> int:
    """
    Stable hashing function (REQUIRED for determinism).

    Uses SHA-256 to ensure:
    - consistent output across runs
    - Python version independence (unlike built-in hash())
    """

    if not isinstance(value, str):
        value = str(value)

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()

    return int(digest, 16)


# ============================================================
# ✅ ALTERNATIVE STRATEGY (KEY-BASED)
# ============================================================

def resolve_partition_by_key(event: dict, key: str, context):
    """
    Partition based on a specific key inside payload.

    Example:
    partition by 'user_id'
    """

    payload = event.get("payload", {})

    if key not in payload:
        return resolve_partition(event, context)

    partition_count = context.policy.get(
        "partition_count",
        DEFAULT_PARTITION_COUNT
    )

    value = str(payload[key])

    index = _stable_hash(value) % partition_count

    return f"p{index}"


# ============================================================
# ✅ ROUND-ROBIN STRATEGY (OPTIONAL)
# ============================================================

_round_robin_counter = 0


def resolve_partition_round_robin(context):
    """
    Non-deterministic distribution.

    ⚠️ WARNING:
    Not replay-safe.
    Use ONLY for non-critical workloads.
    """

    global _round_robin_counter

    partition_count = context.policy.get(
        "partition_count",
        DEFAULT_PARTITION_COUNT
    )

    index = _round_robin_counter % partition_count
    _round_robin_counter += 1

    return f"p{index}"


# ============================================================
# ✅ BATCH PARTITIONING
# ============================================================

def resolve_partitions_bulk(events: list, context):
    """
    Resolve partitions for multiple events.

    Guarantees:
    - consistent mapping
    - independent computation
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    partitions = []

    for event in events:
        partition = resolve_partition(event, context)
        partitions.append(partition)

    return partitions


# ============================================================
# ✅ PARTITION VALIDATION
# ============================================================

def validate_partition(partition: str):
    """
    Ensures partition format is valid.
    """

    if not isinstance(partition, str):
        raise TypeError("Partition must be a string")

    if not partition.startswith("p"):
        raise Exception(
            "[PARTITION ERROR] Partition must start with 'p'"
        )

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_partition_determinism(event: dict, context):
    """
    Ensures same event always maps to same partition.
    """

    p1 = resolve_partition(event, context)
    p2 = resolve_partition(event, context)

    if p1 != p2:
        raise Exception(
            "[PARTITION ERROR] Non-deterministic partition mapping"
        )

    return True


# ============================================================
# ✅ LOAD DISTRIBUTION ANALYSIS (DEBUG TOOL)
# ============================================================

def analyze_partition_distribution(events: list, context):
    """
    Analyze how events are distributed across partitions.

    Useful for:
    - tuning partition count
    - identifying skew
    """

    distribution = {}

    for event in events:
        partition = resolve_partition(event, context)

        distribution[partition] = distribution.get(partition, 0) + 1

    return distribution


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_partition(event: dict, context):
    """
    Debug function — does not affect execution.
    """

    partition = resolve_partition(event, context)

    return {
        "event_id": event.get("event_id"),
        "partition": partition,
    }
