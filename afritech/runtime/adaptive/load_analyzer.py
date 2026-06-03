"""
AfriTech Load Analyzer

PURPOSE:
--------
Interprets telemetry data to determine system load state.

Responsibilities:
- classify system load (idle, normal, high, overloaded)
- detect bottlenecks
- provide deterministic load signals
- support adaptive policy optimization

CRITICAL LAW:
-------------
Load Analyzer MAY:
- interpret telemetry
- classify load levels

Load Analyzer may NOT:
- modify runtime state
- alter event semantics
- introduce randomness
"""

# ============================================================
# ✅ LOAD THRESHOLDS (TUNABLE VIA POLICY)
# ============================================================

DEFAULT_THRESHOLDS = {
    "idle": 0,
    "normal": 50,
    "high": 100,
    "overloaded": 1000,
}


# ============================================================
# ✅ MAIN LOAD ANALYZER
# ============================================================

def analyze_load(telemetry: dict):
    """
    Determines system load state.

    Input:
        telemetry = {
            "queue_sizes": dict,
            "total_events": int,
            "max_queue_depth": int,
            ...
        }

    Output:
        load_state: str
    """

    if not isinstance(telemetry, dict):
        raise TypeError("Telemetry must be a dictionary")

    total_events = telemetry.get("total_events", 0)
    max_queue_depth = telemetry.get("max_queue_depth", 0)

    # --------------------------------------------------------
    # Classification logic (deterministic)
    # --------------------------------------------------------

    if total_events == 0:
        return "idle"

    if max_queue_depth >= DEFAULT_THRESHOLDS["overloaded"]:
        return "overloaded"

    if max_queue_depth >= DEFAULT_THRESHOLDS["high"]:
        return "high"

    return "normal"


# ============================================================
# ✅ ADVANCED LOAD ANALYSIS (MULTI-METRIC)
# ============================================================

def analyze_load_detailed(telemetry: dict):
    """
    More granular load analysis.

    Returns:
        {
            "state": str,
            "pressure_score": int,
            "imbalance": float
        }
    """

    queue_sizes = telemetry.get("queue_sizes", {})
    total_events = telemetry.get("total_events", 0)

    if not queue_sizes:
        return {
            "state": "idle",
            "pressure_score": 0,
            "imbalance": 0.0,
        }

    max_q = max(queue_sizes.values())
    min_q = min(queue_sizes.values())
    avg_q = total_events / len(queue_sizes) if queue_sizes else 0

    imbalance = (max_q - min_q) / (avg_q + 1)  # avoid div by zero

    state = analyze_load(telemetry)

    return {
        "state": state,
        "pressure_score": max_q,
        "imbalance": imbalance,
    }


# ============================================================
# ✅ HOTSPOT DETECTION
# ============================================================

def detect_hotspots(telemetry: dict, threshold: int = 200):
    """
    Identify overloaded queues (hotspots).
    """

    queue_sizes = telemetry.get("queue_sizes", {})

    hotspots = {}

    for queue, size in queue_sizes.items():
        if size >= threshold:
            hotspots[queue] = size

    return hotspots


# ============================================================
# ✅ LOAD TREND ANALYSIS (STATELESS APPROX)
# ============================================================

def estimate_load_trend(current: dict, previous: dict):
    """
    Estimate whether load is increasing or decreasing.

    Returns:
        "increasing", "decreasing", "stable"
    """

    curr_total = current.get("total_events", 0)
    prev_total = previous.get("total_events", 0)

    if curr_total > prev_total:
        return "increasing"

    if curr_total < prev_total:
        return "decreasing"

    return "stable"


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_load_state(state: str):
    """
    Ensures load state is valid.
    """

    valid_states = {"idle", "normal", "high", "overloaded"}

    if state not in valid_states:
        raise Exception(f"[LOAD ANALYZER ERROR] Invalid state: {state}")

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_load_determinism(telemetry: dict):
    """
    Ensures consistent output for same input.
    """

    s1 = analyze_load(telemetry)
    s2 = analyze_load(telemetry)

    if s1 != s2:
        raise Exception(
            "[LOAD ANALYZER ERROR] Non-deterministic load classification"
        )

    return True


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_load_analysis(telemetry: dict):
    """
    Debug helper for understanding load decisions.
    """

    state = analyze_load(telemetry)
    detailed = analyze_load_detailed(telemetry)

    return {
        "state": state,
        "detailed": detailed,
    }