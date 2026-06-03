"""
AfriTech Replay Locality

PURPOSE:
--------
Determines where replay execution should occur.

Replay MUST:
- run near the source of truth (logs, partitions, storage)
- remain deterministic
- avoid remote data movement when possible

Responsibilities:
- resolve replay region
- determine replay node
- align replay location with execution locality
- ensure replay consistency

CRITICAL LAW:
-------------
Replay Locality MAY:
- choose optimal replay node
- optimize data proximity

Replay Locality may NOT:
- alter event structure
- influence replay outcome
- introduce randomness
"""

from afritech.runtime.locality.region_strategy import resolve_region
from afritech.runtime.locality.partition_router import resolve_partition


# ============================================================
# ✅ MAIN REPLAY LOCATION RESOLUTION
# ============================================================

def resolve_replay_location(event: dict, context):
    """
    Determines WHERE replay should be executed.

    Strategy:
    - same region as event
    - same partition for data locality
    """

    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")

    region = resolve_region(event, context)
    partition = resolve_partition(event, context)

    node = _build_replay_node(region, partition, context)

    return {
        "region": region,
        "partition": partition,
        "node": node,
    }


# ============================================================
# ✅ NODE CONSTRUCTION
# ============================================================

def _build_replay_node(region: str, partition: str, context):
    """
    Builds replay node identifier.

    Keeps replay logically separate from execution nodes.
    """

    mode = context.policy.get("transport_mode", "default")

    return f"{region}.{partition}.replay.{mode}"


# ============================================================
# ✅ STRICT REPLAY LOCALITY (CONSISTENCY MODE)
# ============================================================

def resolve_strict_replay_location(event: dict, context):
    """
    Enforces strict replay locality.

    Guarantees:
    - replay happens EXACTLY where original execution occurred
    """

    execution_node = context.resolve_node(event)

    return {
        "node": execution_node,
        "mode": "strict",
    }


# ============================================================
# ✅ BULK REPLAY RESOLUTION
# ============================================================

def resolve_replay_locations_bulk(events: list, context):
    """
    Resolve replay location for multiple events.

    Deterministic:
    - same input → same output
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    locations = []

    for event in events:
        loc = resolve_replay_location(event, context)
        locations.append(loc)

    return locations


# ============================================================
# ✅ REPLAY CONSISTENCY CHECK
# ============================================================

def validate_replay_locality_determinism(event: dict, context):
    """
    Ensures replay locality decisions are deterministic.
    """

    loc1 = resolve_replay_location(event, context)
    loc2 = resolve_replay_location(event, context)

    if loc1 != loc2:
        raise Exception(
            "[REPLAY LOCALITY ERROR] Non-deterministic replay location"
        )

    return True


# ============================================================
# ✅ ALIGNMENT CHECK (EXECUTION vs REPLAY)
# ============================================================

def validate_execution_replay_alignment(event: dict, context):
    """
    Ensures replay location aligns with execution locality when required.
    """

    execution_node = context.resolve_node(event)
    replay_location = resolve_replay_location(event, context)

    if execution_node.split(".")[0:2] != replay_location["node"].split(".")[0:2]:
        raise Exception(
            "[REPLAY LOCALITY ERROR] Execution and replay locality mismatch"
        )

    return True


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_replay_locality(event: dict, context):
    """
    Debug helper (non-intrusive).
    """

    loc = resolve_replay_location(event, context)

    return {
        "event_id": event.get("event_id"),
        "replay_region": loc["region"],
        "replay_partition": loc["partition"],
        "replay_node": loc["node"],
    }