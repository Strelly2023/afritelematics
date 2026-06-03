"""
AfriTech Policy Optimizer

PURPOSE:
--------
Transforms system load state into safe runtime policy adjustments.

Responsibilities:
- adjust batch size based on load
- adjust retry limits based on pressure
- maintain stability (avoid oscillation)
- remain deterministic and guard-safe

CRITICAL LAW:
-------------
Policy Optimizer MAY:
- tune operational parameters

Policy Optimizer may NOT:
- modify event semantics
- introduce randomness
- affect replay truth
"""

# ============================================================
# ✅ CONFIGURATION DEFAULTS
# ============================================================

MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 1000

MIN_RETRY_LIMIT = 1
MAX_RETRY_LIMIT = 10

# smoothing limits (prevent instability)
MAX_BATCH_CHANGE_STEP = 10
MAX_RETRY_CHANGE_STEP = 1


# ============================================================
# ✅ MAIN OPTIMIZER
# ============================================================

def optimize_policy(load_state: str, context):
    """
    Main policy optimization logic.

    Input:
        load_state: ["idle", "normal", "high", "overloaded"]

    Output:
        updated policy dict (non-mutating)
    """

    if not isinstance(load_state, str):
        raise TypeError("load_state must be a string")

    current_policy = context.policy
    new_policy = dict(current_policy)  # ✅ copy (never mutate directly)

    # --------------------------------------------------------
    # Extract current values safely
    # --------------------------------------------------------

    current_batch = current_policy.get("batch_size", MIN_BATCH_SIZE)
    current_retry = current_policy.get("retry_limit", MIN_RETRY_LIMIT)

    # --------------------------------------------------------
    # Apply policy tuning
    # --------------------------------------------------------

    if load_state == "overloaded":
        new_policy["batch_size"] = _increase_batch(current_batch, aggressive=True)
        new_policy["retry_limit"] = _decrease_retry(current_retry)

    elif load_state == "high":
        new_policy["batch_size"] = _increase_batch(current_batch)
        new_policy["retry_limit"] = current_retry

    elif load_state == "normal":
        # maintain stability
        new_policy["batch_size"] = current_batch
        new_policy["retry_limit"] = current_retry

    elif load_state == "idle":
        new_policy["batch_size"] = _decrease_batch(current_batch)
        new_policy["retry_limit"] = _increase_retry(current_retry)

    else:
        # unknown state -> do nothing (safe fallback)
        return new_policy

    return _stabilize_policy(current_policy, new_policy)


# ============================================================
# ✅ BATCH SIZE ADJUSTMENTS
# ============================================================

def _increase_batch(current: int, aggressive: bool = False):
    """
    Increase batch size with safety bounds.
    """

    step = MAX_BATCH_CHANGE_STEP if aggressive else max(1, current // 4)

    new_value = current + step

    return min(new_value, MAX_BATCH_SIZE)


def _decrease_batch(current: int):
    """
    Reduce batch size safely.
    """

    step = max(1, current // 4)

    new_value = current - step

    return max(new_value, MIN_BATCH_SIZE)


# ============================================================
# ✅ RETRY LIMIT ADJUSTMENTS
# ============================================================

def _increase_retry(current: int):
    """
    Increase retry resilience.
    """

    return min(current + MAX_RETRY_CHANGE_STEP, MAX_RETRY_LIMIT)


def _decrease_retry(current: int):
    """
    Decrease retry when system overloaded.
    """

    return max(current - MAX_RETRY_CHANGE_STEP, MIN_RETRY_LIMIT)


# ============================================================
# ✅ STABILITY / SMOOTHING CONTROL
# ============================================================

def _stabilize_policy(old: dict, new: dict):
    """
    Prevent abrupt policy changes.

    Ensures:
    - gradual transitions
    - no oscillation
    """

    stabilized = dict(old)

    # stabilize batch
    if abs(new["batch_size"] - old["batch_size"]) > MAX_BATCH_CHANGE_STEP:
        if new["batch_size"] > old["batch_size"]:
            stabilized["batch_size"] = old["batch_size"] + MAX_BATCH_CHANGE_STEP
        else:
            stabilized["batch_size"] = old["batch_size"] - MAX_BATCH_CHANGE_STEP
    else:
        stabilized["batch_size"] = new["batch_size"]

    # stabilize retry
    if abs(new["retry_limit"] - old["retry_limit"]) > MAX_RETRY_CHANGE_STEP:
        if new["retry_limit"] > old["retry_limit"]:
            stabilized["retry_limit"] = old["retry_limit"] + MAX_RETRY_CHANGE_STEP
        else:
            stabilized["retry_limit"] = old["retry_limit"] - MAX_RETRY_CHANGE_STEP
    else:
        stabilized["retry_limit"] = new["retry_limit"]

    return stabilized


# ============================================================
# ✅ POLICY VALIDATION
# ============================================================

def validate_policy(policy: dict):
    """
    Ensures policy stays within safe bounds.
    """

    if not isinstance(policy, dict):
        raise TypeError("Policy must be a dictionary")

    batch = policy.get("batch_size", MIN_BATCH_SIZE)
    retry = policy.get("retry_limit", MIN_RETRY_LIMIT)

    if not (MIN_BATCH_SIZE <= batch <= MAX_BATCH_SIZE):
        raise Exception("[POLICY ERROR] Invalid batch_size bounds")

    if not (MIN_RETRY_LIMIT <= retry <= MAX_RETRY_LIMIT):
        raise Exception("[POLICY ERROR] Invalid retry_limit bounds")

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_determinism(load_state: str, context):
    """
    Ensures optimizer is deterministic.
    """

    p1 = optimize_policy(load_state, context)
    p2 = optimize_policy(load_state, context)

    if p1 != p2:
        raise Exception(
            "[POLICY OPTIMIZER ERROR] Non-deterministic output"
        )

    return True


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_policy_optimization(load_state: str, context):
    """
    Debug helper for understanding decisions.
    """

    current = context.policy
    proposed = optimize_policy(load_state, context)

    return {
        "load_state": load_state,
        "current_policy": current,
        "proposed_policy": proposed,
    }