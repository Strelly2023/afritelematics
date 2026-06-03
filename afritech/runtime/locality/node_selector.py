"""
AfriTech Node Selector

PURPOSE:
--------
Determines the exact execution node for an event.

Responsibilities:
- combine region + partition into node identity
- apply node selection strategy
- support deterministic placement
- remain purely functional (no side effects)

CRITICAL LAW:
-------------
Node Selector MAY:
- choose execution node

Node Selector may NOT:
- modify event content
- influence execution semantics
"""

# ============================================================
# ✅ MAIN NODE SELECTION FUNCTION
# ============================================================

def select_node(region: str, partition: str, context):
    """
    Selects execution node.

    Default strategy:
    - region + partition + transport mode

    Output format:
    <region>.<partition>.<mode>
    """

    if not isinstance(region, str):
        raise TypeError("Region must be a string")

    if not isinstance(partition, str):
        raise TypeError("Partition must be a string")

    mode = context.policy.get("transport_mode", "default")

    return f"{region}.{partition}.{mode}"


# ============================================================
# ✅ ADVANCED STRATEGY (OPTIONAL)
# ============================================================

def select_node_with_strategy(region: str, partition: str, context):
    """
    Policy-driven node selection.

    Supports:
    - default
    - regional-only
    - partition-only
    """

    strategy = context.policy.get("node_selection_strategy", "default")

    if strategy == "regional":
        return f"{region}.{context.policy.get('transport_mode', 'default')}"

    if strategy == "partition":
        return f"{partition}.{context.policy.get('transport_mode', 'default')}"

    # fallback to default behavior
    return select_node(region, partition, context)


# ============================================================
# ✅ NODE VALIDATION
# ============================================================

def validate_node(node: str):
    """
    Ensures node format is valid and non-empty.
    """

    if not isinstance(node, str):
        raise TypeError("Node must be a string")

    if not node:
        raise Exception("[LOCALITY ERROR] Empty node identifier")

    parts = node.split(".")

    if len(parts) < 2:
        raise Exception(
            "[LOCALITY ERROR] Node format invalid (expected region.partition...)"
        )

    return True


# ============================================================
# ✅ BULK NODE RESOLUTION
# ============================================================

def select_nodes_bulk(regions: list, partitions: list, context):
    """
    Resolve multiple nodes (vectorized computation).

    Ensures deterministic mapping.
    """

    if len(regions) != len(partitions):
        raise ValueError("Regions and partitions must have same length")

    nodes = []

    for region, partition in zip(regions, partitions):
        node = select_node(region, partition, context)
        nodes.append(node)

    return nodes


# ============================================================
# ✅ NODE TRACE (OBSERVABILITY)
# ============================================================

def trace_node(region: str, partition: str, context):
    """
    Debug helper — shows node decision.
    """

    node = select_node(region, partition, context)

    return {
        "region": region,
        "partition": partition,
        "node": node,
        "mode": context.policy.get("transport_mode"),
    }


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_node_determinism(region: str, partition: str, context):
    """
    Ensures node selection is deterministic.
    """

    node1 = select_node(region, partition, context)
    node2 = select_node(region, partition, context)

    if node1 != node2:
        raise Exception(
            "[LOCALITY ERROR] Non-deterministic node selection"
        )

    return True