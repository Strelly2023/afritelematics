"""
AfriTech Adaptation Engine

PURPOSE:
--------
Applies adaptive policy updates to the runtime context.

Responsibilities:
- safely apply policy changes
- ensure only operational fields are modified
- preserve determinism
- enforce guard-safe updates

CRITICAL LAW:
-------------
Adaptation Engine MAY:
- update runtime operational parameters

Adaptation Engine may NOT:
- modify event content
- alter semantics
- modify constitutional fields
"""

from afritech.runtime.guards import (
    enforce_policy_boundary,
    enforce_runtime_scope,
)

# ============================================================
# ✅ MAIN ADAPTATION FUNCTION
# ============================================================

def apply_adaptation(context, new_policy: dict):
    """
    Apply policy updates safely.

    Steps:
    1. Validate new policy
    2. Enforce guard rules
    3. Merge with existing policy
    4. Apply changes in controlled manner
    """

    if not isinstance(new_policy, dict):
        raise TypeError("New policy must be a dictionary")

    # --------------------------------------------------------
    # 1. Validate boundaries (CRITICAL)
    # --------------------------------------------------------
    enforce_policy_boundary(new_policy)
    enforce_runtime_scope(new_policy)

    # --------------------------------------------------------
    # 2. Prepare safe merge
    # --------------------------------------------------------
    current_policy = context.policy
    merged_policy = dict(current_policy)

    changes = {}

    for key, value in new_policy.items():
        if current_policy.get(key) != value:
            merged_policy[key] = value
            changes[key] = {
                "old": current_policy.get(key),
                "new": value,
            }

    # --------------------------------------------------------
    # 3. Apply changes atomically
    # --------------------------------------------------------
    context.policy.update(merged_policy)

    return merged_policy


# ============================================================
# ✅ DRY RUN (NO APPLY)
# ============================================================

def preview_adaptation(context, new_policy: dict):
    """
    Preview adaptation without applying changes.

    Useful for:
    - monitoring
    - debugging
    - testing adaptive logic
    """

    enforce_policy_boundary(new_policy)
    enforce_runtime_scope(new_policy)

    current = context.policy
    preview = dict(current)

    for key, value in new_policy.items():
        preview[key] = value

    return {
        "current_policy": current,
        "proposed_policy": preview,
    }


# ============================================================
# ✅ DIFF GENERATOR
# ============================================================

def compute_policy_diff(old_policy: dict, new_policy: dict):
    """
    Compute changes between policies.

    Output:
        {
            key: {old: X, new: Y}
        }
    """

    diff = {}

    keys = set(old_policy.keys()).union(new_policy.keys())

    for key in keys:
        old = old_policy.get(key)
        new = new_policy.get(key)

        if old != new:
            diff[key] = {"old": old, "new": new}

    return diff


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_adaptation(context, new_policy: dict):
    """
    Ensures adaptation is valid before applying.
    """

    if not isinstance(new_policy, dict):
        raise TypeError("Policy must be dict")

    enforce_policy_boundary(new_policy)
    enforce_runtime_scope(new_policy)

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_adaptation_determinism(context, new_policy: dict):
    """
    Ensures adaptation behaves deterministically.
    """

    preview1 = preview_adaptation(context, new_policy)
    preview2 = preview_adaptation(context, new_policy)

    if preview1 != preview2:
        raise Exception(
            "[ADAPTATION ERROR] Non-deterministic adaptation"
        )

    return True


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_adaptation(context, new_policy: dict):
    """
    Debug trace of adaptation changes.

    Does NOT modify system.
    """

    current = dict(context.policy)
    diff = compute_policy_diff(current, new_policy)

    return {
        "current_policy": current,
        "proposed_policy": new_policy,
        "diff": diff,
    }
