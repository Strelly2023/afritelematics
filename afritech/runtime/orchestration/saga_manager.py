"""
AfriTech Saga Manager

PURPOSE:
--------
Handles failure recovery using the Saga pattern.

Responsibilities:
- detect workflow failures
- apply compensation logic
- ensure deterministic rollback
- maintain execution safety

CRITICAL LAW:
-------------
Saga Manager MAY:
- trigger compensating actions
- manage rollback logic

Saga Manager may NOT:
- modify original event semantics
- introduce randomness
- break determinism
"""

# ============================================================
# ✅ MAIN SAGA APPLICATION
# ============================================================

def apply_saga(result: dict, context):
    """
    Applies saga compensation logic.

    Input:
        result = workflow execution output

    Output:
        possibly compensated result
    """

    if not isinstance(result, dict):
        raise TypeError("Result must be a dictionary")

    status = result.get("status")

    # --------------------------------------------------------
    # ✅ SUCCESS CASE
    # --------------------------------------------------------
    if status == "completed":
        return result

    # --------------------------------------------------------
    # ✅ FAILURE CASE → APPLY COMPENSATION
    # --------------------------------------------------------
    if status in ("failed", "error"):
        compensations = get_compensation_steps(result, context)

        executed = execute_compensations(compensations, context)

        return {
            "status": "compensated",
            "original_status": status,
            "compensations": executed,
            "event": result.get("event"),
        }

    # --------------------------------------------------------
    # ✅ UNKNOWN STATUS → PASS THROUGH
    # --------------------------------------------------------
    return result


# ============================================================
# ✅ COMPENSATION RESOLUTION
# ============================================================

def get_compensation_steps(result: dict, context):
    """
    Identify compensation steps for a failed workflow.

    Strategy:
    - check result["results"]
    - map each executed step to compensation
    """

    steps = result.get("results", [])

    compensations = []

    # Reverse order (important!)
    for step in reversed(steps):
        compensation = resolve_compensation(step, context)

        if compensation:
            compensations.append(compensation)

    return compensations


# ============================================================
# ✅ RESOLVE SINGLE COMPENSATION
# ============================================================

def resolve_compensation(step_result: dict, context):
    """
    Determine compensation for a step.

    Convention:
    step_result may include:
        "compensate": callable
    """

    if not isinstance(step_result, dict):
        return None

    comp = step_result.get("compensate")

    if callable(comp):
        return comp

    return None


# ============================================================
# ✅ EXECUTE COMPENSATIONS
# ============================================================

def execute_compensations(compensations: list, context):
    """
    Execute compensation steps safely.

    Guarantees:
    - reverse order execution
    - deterministic behavior
    """

    results = []

    for index, comp in enumerate(compensations):
        try:
            result = comp(context)

            if not isinstance(result, dict):
                raise Exception(
                    f"[SAGA ERROR] Compensation {index} must return dict"
                )

            results.append({
                "status": "success",
                "result": result,
                "step": index,
            })

        except Exception as e:
            # compensation failure is recorded, not fatal
            results.append({
                "status": "failed",
                "error": str(e),
                "step": index,
            })

    return results


# ============================================================
# ✅ BULK SAGA APPLICATION
# ============================================================

def apply_saga_bulk(results: list, context):
    """
    Apply saga logic to multiple workflow results.
    """

    if not isinstance(results, list):
        raise TypeError("Results must be a list")

    final = []

    for result in results:
        final.append(apply_saga(result, context))

    return final


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_saga_result(result: dict):
    """
    Ensures result structure is valid.
    """

    if not isinstance(result, dict):
        raise TypeError("Result must be a dictionary")

    if "status" not in result:
        raise Exception("[SAGA ERROR] Missing status field")

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_saga_determinism(result: dict, context):
    """
    Ensures saga produces deterministic output.
    """

    r1 = apply_saga(result, context)
    r2 = apply_saga(result, context)

    if r1 != r2:
        raise Exception("[SAGA ERROR] Non-deterministic saga detected")

    return True


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_saga(result: dict, context):
    """
    Debug helper.

    Shows:
    - original result
    - compensation plan
    """

    compensations = get_compensation_steps(result, context)

    return {
        "original_status": result.get("status"),
        "compensation_count": len(compensations),
        "compensations": [
            str(comp) for comp in compensations
        ],
    }