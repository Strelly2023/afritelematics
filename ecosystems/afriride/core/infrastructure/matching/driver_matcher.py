from math import sqrt


# --------------------------------------------------
# DISTANCE FUNCTION (PURE + SAFE)
# --------------------------------------------------
def _distance(a, b):
    """
    Deterministic Euclidean distance.

    Defensive:
    - validates required keys
    """

    if "lat" not in a or "lng" not in a:
        raise Exception("Invalid point 'a': missing lat/lng")

    if "lat" not in b or "lng" not in b:
        raise Exception("Invalid point 'b': missing lat/lng")

    return sqrt(
        (a["lat"] - b["lat"]) ** 2 +
        (a["lng"] - b["lng"]) ** 2
    )


# --------------------------------------------------
# SINGLE MATCH (BEST DRIVER)
# --------------------------------------------------
def match_driver(drivers, pickup):
    """
    Deterministic driver selection.

    Rules:
    - closest distance wins
    - tie-break by driver_id (stable ordering)
    """

    if not drivers:
        return None

    # Validate inputs
    for d in drivers:
        if "id" not in d:
            raise Exception("Driver missing 'id'")
        if "lat" not in d or "lng" not in d:
            raise Exception(f"Driver {d.get('id')} missing coordinates")

    # Deterministic ordering
    ordered = sorted(
        drivers,
        key=lambda d: (
            _distance(d, pickup),
            d["id"]  # ensures stable ordering
        )
    )

    return ordered[0]


# --------------------------------------------------
# FULL RANKING (FOR DISPATCH LOOP)
# --------------------------------------------------
def rank_drivers(drivers, pickup):
    """
    Returns full deterministic ordering.

    Used for:
    - dispatch queue
    - retry sequencing
    """

    if not drivers:
        return []

    for d in drivers:
        if "id" not in d:
            raise Exception("Driver missing 'id'")
        if "lat" not in d or "lng" not in d:
            raise Exception(f"Driver {d.get('id')} missing coordinates")

    return sorted(
        drivers,
        key=lambda d: (
            _distance(d, pickup),
            d["id"]
        )
    )


# --------------------------------------------------
# OPTIONAL: LIMIT NEAREST DRIVERS
# --------------------------------------------------
def top_k_drivers(drivers, pickup, k):
    """
    Returns top-K closest drivers.

    Useful for:
    - limiting dispatch load
    - performance optimization
    """

    ranked = rank_drivers(drivers, pickup)

    return ranked[:k] if k > 0 else []


# --------------------------------------------------
# OPTIONAL: DISTANCE ANNOTATION
# --------------------------------------------------
def annotate_distances(drivers, pickup):
    """
    Returns drivers with computed distance.

    Helpful for debugging, metrics, logs.
    """

    result = []

    for d in drivers:
        result.append({
            **d,
            "distance": _distance(d, pickup)
        })

    return sorted(
        result,
        key=lambda d: (d["distance"], d["id"])
    )