"""
AfriTech Region Strategy

PURPOSE:
--------
Determines the region where an event should execute.

Responsibilities:
- resolve region from event or context
- support policy-driven overrides
- ensure deterministic region assignment
- prepare for multi-region deployments

CRITICAL LAW:
-------------
Region Strategy MAY:
- determine execution region
- optimize placement geographically

Region Strategy may NOT:
- modify event content
- alter payload semantics
- introduce randomness
"""

# ============================================================
# ✅ DEFAULTS
# ============================================================

DEFAULT_REGION = "global"


# ============================================================
# ✅ MAIN REGION RESOLUTION
# ============================================================

def resolve_region(event: dict, context):
    """
    Determines the execution region for an event.

    Priority order:
    1. Event-defined region
    2. Policy-defined default region
    3. System fallback (global)
    """

    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")

    # --------------------------------------------------------
    # 1. Event-defined region (highest priority)
    # --------------------------------------------------------
    region = event.get("region")
    if region:
        return _normalize_region(region)

    # --------------------------------------------------------
    # 2. Policy-defined region
    # --------------------------------------------------------
    policy_region = context.policy.get("default_region")
    if policy_region:
        return _normalize_region(policy_region)

    # --------------------------------------------------------
    # 3. Fallback
    # --------------------------------------------------------
    return DEFAULT_REGION


# ============================================================
# ✅ NORMALIZATION
# ============================================================

def _normalize_region(region: str):
    """
    Ensures consistent region formatting.

    Example:
    "AU " → "au"
    """

    if not isinstance(region, str):
        raise TypeError("Region must be a string")

    return region.strip().lower()


# ============================================================
# ✅ ADVANCED STRATEGY (POLICY-DRIVEN)
# ============================================================

def resolve_region_with_strategy(event: dict, context):
    """
    Allows override strategies.

    Supported strategies:
    - event: use event region
    - policy: force policy region
    - hybrid: prefer event, fallback to policy
    """

    strategy = context.policy.get("region_strategy", "default")

    event_region = event.get("region")
    policy_region = context.policy.get("default_region")

    if strategy == "event":
        return _normalize_region(event_region or DEFAULT_REGION)

    if strategy == "policy":
        return _normalize_region(policy_region or DEFAULT_REGION)

    if strategy == "hybrid":
        return _normalize_region(event_region or policy_region or DEFAULT_REGION)

    # default behavior
    return resolve_region(event, context)


# ============================================================
# ✅ BULK RESOLUTION
# ============================================================

def resolve_regions_bulk(events: list, context):
    """
    Resolve region for multiple events.

    Guarantees:
    - independent evaluation
    - deterministic results
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    regions = []

    for event in events:
        region = resolve_region(event, context)
        regions.append(region)

    return regions


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_region(region: str):
    """
    Ensures region is valid format.
    """

    if not isinstance(region, str):
        raise TypeError("Region must be a string")

    if not region:
        raise Exception("[REGION ERROR] Region cannot be empty")

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_region_determinism(event: dict, context):
    """
    Ensures region resolution is deterministic.
    """

    r1 = resolve_region(event, context)
    r2 = resolve_region(event, context)

    if r1 != r2:
        raise Exception(
            "[REGION ERROR] Non-deterministic region resolution"
        )

    return True


# ============================================================
# ✅ REGION TRACE (OBSERVABILITY)
# ============================================================

def trace_region(event: dict, context):
    """
    Debug helper — non-intrusive.
    """

    region = resolve_region(event, context)

    return {
        "event_id": event.get("event_id"),
        "region": region,
        "policy_region": context.policy.get("default_region"),
    }


# ============================================================
# ✅ REGION GROUPING (UTILITY)
# ============================================================

def group_events_by_region(events: list, context):
    """
    Groups events by region.

    Useful for:
    - regional batching
    - distributed scheduling
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    groups = {}

    for event in events:
        region = resolve_region(event, context)

        if region not in groups:
            groups[region] = []

        groups[region].append(event)

    return groups