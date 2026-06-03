"""
AfriTech Locality Manager

PURPOSE:
--------
Central decision engine for execution placement (WHERE).

Responsibilities:
- resolve region for event execution
- determine partition ownership
- select appropriate execution node
- apply affinity policies
- enforce locality safety (no mutation)

CRITICAL LAW:
-------------
Locality MAY:
- choose execution location
- optimize placement

Locality may NOT:
- modify event content
- alter payload
- impact execution truth
"""

from afritech.runtime.locality.node_selector import select_node
from afritech.runtime.locality.partition_router import resolve_partition
from afritech.runtime.locality.region_strategy import resolve_region
from afritech.runtime.locality.affinity_policy import apply_affinity_policy
from afritech.runtime.guards import enforce_locality_safety


# ============================================================
# ✅ MAIN ENTRY POINT
# ============================================================

def resolve_execution_location(event: dict, context):
    """
    Determines WHERE an event should be executed.

    Pipeline:
    1. Resolve region
    2. Resolve partition
    3. Select node
    4. Apply affinity policy
    5. Safety enforcement
    """

    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")

    # --------------------------------------------------------
    # 1. Region resolution
    # --------------------------------------------------------
    region = resolve_region(event, context)

    # --------------------------------------------------------
    # 2. Partition resolution
    # --------------------------------------------------------
    partition = resolve_partition(event, context)

    # --------------------------------------------------------
    # 3. Node selection
    # --------------------------------------------------------
    node = select_node(region, partition, context)

    # --------------------------------------------------------
    # 4. Raw location object
    # --------------------------------------------------------
    location = {
        "region": region,
        "partition": partition,
        "node": node,
    }

    # --------------------------------------------------------
    # 5. Apply affinity policy (may override node choice)
    # --------------------------------------------------------
    final_node = apply_affinity_policy(location, context)

    # --------------------------------------------------------
    # 6. Safety enforcement (critical)
    # --------------------------------------------------------
    enforce_locality_safety(event, final_node)

    return {
        "region": region,
        "partition": partition,
        "node": final_node,
    }


# ============================================================
# ✅ QUEUE NAME RESOLVER (INTEGRATION HELPER)
# ============================================================

def resolve_queue_name(event: dict, context):
    """
    Produces queue name used by async dispatcher.

    Convention:
    events.<node>
    """

    location = resolve_execution_location(event, context)

    return f"events.{location['node']}"


# ============================================================
# ✅ REPLAY LOCALITY (BRIDGE)
# ============================================================

def resolve_replay_location(event: dict, context):
    """
    Determines WHERE replay should occur.

    Principle:
    Replay runs near where data/logs exist.
    """

    region = resolve_region(event, context)

    return {
        "region": region,
        "node": f"{region}.replay",
    }


# ============================================================
# ✅ LOCALITY TRACE (OBSERVABILITY)
# ============================================================

def trace_locality(event: dict, context):
    """
    Debug / observability helper.

    Does NOT affect execution.
    """

    location = resolve_execution_location(event, context)

    return {
        "event_id": event.get("event_id"),
        "region": location["region"],
        "partition": location["partition"],
        "node": location["node"],
    }


# ============================================================
# ✅ BULK LOCALITY RESOLUTION
# ============================================================

def resolve_bulk_locations(events: list, context):
    """
    Resolves location for multiple events.

    Guarantees:
    - independent computation
    - no shared mutation
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    results = []

    for event in events:
        location = resolve_execution_location(event, context)
        results.append(location)

    return results


# ============================================================
# ✅ CONSISTENCY CHECK (OPTIONAL GUARD)
# ============================================================

def validate_locality_consistency(event: dict, context):
    """
    Ensures repeated locality resolution is stable.

    Deterministic guarantee test.
    """

    loc1 = resolve_execution_location(event, context)
    loc2 = resolve_execution_location(event, context)

    if loc1 != loc2:
        raise Exception(
            "[LOCALITY ERROR] Non-deterministic locality resolution"
        )

    return True