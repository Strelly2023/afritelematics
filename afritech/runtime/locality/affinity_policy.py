"""
AfriTech Affinity Policy

PURPOSE:
--------
Refines execution placement after initial locality resolution.

Responsibilities:
- apply policy-driven overrides to location
- enforce affinity strategies (regional, partition, node)
- remain deterministic and side-effect free

CRITICAL LAW:
-------------
Affinity Policy MAY:
- adjust node placement
- optimize routing strategy

Affinity Policy may NOT:
- modify event content
- introduce randomness (must be deterministic)
- affect execution truth
"""

# ============================================================
# ✅ MAIN AFFINITY POLICY
# ============================================================

def apply_affinity_policy(location: dict, context):
    """
    Applies policy-based affinity decisions.

    Input:
        location = {
            "region": str,
            "partition": str,
            "node": str
        }

    Output:
        final node (string)
    """

    if not isinstance(location, dict):
        raise TypeError("Location must be a dictionary")

    strategy = context.policy.get("locality_mode", "default")

    # --------------------------------------------------------
    # ✅ DEFAULT (FULL NODE)
    # --------------------------------------------------------
    if strategy == "default":
        return location["node"]

    # --------------------------------------------------------
    # ✅ REGION-AFFINITY (coarse placement)
    # --------------------------------------------------------
    if strategy == "regional":
        return f"{location['region']}.{context.policy.get('transport_mode', 'default')}"

    # --------------------------------------------------------
    # ✅ PARTITION-AFFINITY (scale-focused)
    # --------------------------------------------------------
    if strategy == "partition":
        return f"{location['partition']}.{context.policy.get('transport_mode', 'default')}"

    # --------------------------------------------------------
    # ✅ HYBRID (region + partition preserved)
    # --------------------------------------------------------
    if strategy == "hybrid":
        return f"{location['region']}.{location['partition']}.{context.policy.get('transport_mode', 'default')}"

    # --------------------------------------------------------
    # ✅ FALLBACK SAFETY
    # --------------------------------------------------------
    return location["node"]


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_affinity(location: dict, node: str):
    """
    Ensures affinity output is valid.
    """

    if not isinstance(node, str):
        raise TypeError("Affinity node must be a string")

    if not node:
        raise Exception("[AFFINITY ERROR] Empty node result")

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_affinity_determinism(location: dict, context):
    """
    Ensures policy produces deterministic output.
    """

    n1 = apply_affinity_policy(location, context)
    n2 = apply_affinity_policy(location, context)

    if n1 != n2:
        raise Exception(
            "[AFFINITY ERROR] Non-deterministic affinity resolution"
        )

    return True


# ============================================================
# ✅ BULK AFFINITY RESOLUTION
# ============================================================

def apply_affinity_bulk(locations: list, context):
    """
    Applies affinity to multiple location objects.
    """

    if not isinstance(locations, list):
        raise TypeError("Locations must be a list")

    nodes = []

    for loc in locations:
        node = apply_affinity_policy(loc, context)
        nodes.append(node)

    return nodes


# ============================================================
# ✅ POLICY INTROSPECTION (DEBUG)
# ============================================================

def trace_affinity(location: dict, context):
    """
    Debug tool — shows how affinity modified location.
    """

    strategy = context.policy.get("locality_mode", "default")

    selected = apply_affinity_policy(location, context)

    return {
        "strategy": strategy,
        "input_location": location,
        "selected_node": selected,
    }