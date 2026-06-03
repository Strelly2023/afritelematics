"""
AfriTech Workflow Engine

PURPOSE:
--------
Executes multi-step workflows in a deterministic, safe, and extensible way.

Responsibilities:
- orchestrate ordered execution steps
- maintain deterministic behavior
- support step-based workflows
- handle failure states (no mutation)
- integrate safely with orchestration layer

CRITICAL LAW:
-------------
Workflow Engine MAY:
- execute ordered steps
- coordinate workflow progression

Workflow Engine may NOT:
- modify event payload semantics
- introduce randomness
- violate execution determinism
"""

# ============================================================
# ✅ DEFAULT WORKFLOW (FALLBACK)
# ============================================================

def execute_workflow(event: dict, context):
    """
    Default workflow execution.

    If no workflow is defined:
    - pass-through execution
    """

    return {
        "status": "completed",
        "event": event,
        "steps_executed": 0,
    }


# ============================================================
# ✅ STEP-BASED WORKFLOW EXECUTION
# ============================================================

def execute_step_workflow(event: dict, steps: list, context):
    """
    Executes a list of steps sequentially.

    Each step must be a callable:
        step(event, context) -> dict(result)
    """

    if not isinstance(steps, list):
        raise TypeError("Steps must be a list")

    current_event = dict(event)  # safe copy
    results = []

    for index, step in enumerate(steps):
        if not callable(step):
            raise TypeError(f"Step {index} is not callable")

        result = step(current_event, context)

        # Validate step result
        if not isinstance(result, dict):
            raise Exception(
                f"[WORKFLOW ERROR] Step {index} must return dict"
            )

        # Prevent semantic mutation
        if result.get("event") and result["event"] != current_event:
            raise Exception(
                f"[WORKFLOW ERROR] Step {index} attempted to mutate event"
            )

        results.append(result)

        # Update ONLY non-semantic metadata
        current_event = result.get("event", current_event)

    return {
        "status": "completed",
        "event": current_event,
        "steps_executed": len(steps),
        "results": results,
    }


# ============================================================
# ✅ CONDITIONAL WORKFLOW EXECUTION
# ============================================================

def execute_conditional_workflow(event: dict, steps: list, context):
    """
    Executes steps conditionally.

    Each step returns:
        {"continue": bool}
    """

    current_event = dict(event)
    results = []

    for index, step in enumerate(steps):
        result = step(current_event, context)

        if not isinstance(result, dict):
            raise Exception(
                f"[WORKFLOW ERROR] Step {index} invalid result"
            )

        results.append(result)

        if result.get("continue") is False:
            break

    return {
        "status": "completed",
        "event": current_event,
        "steps_executed": len(results),
        "results": results,
    }


# ============================================================
# ✅ PARALLEL WORKFLOW (SAFE SIMULATION)
# ============================================================

def execute_parallel_workflow(event: dict, steps: list, context):
    """
    Executes steps independently (no mutation sharing).

    NOTE:
    - parallel in concept (not actual threading)
    - each step receives original event
    """

    results = []

    for index, step in enumerate(steps):
        result = step(dict(event), context)

        if not isinstance(result, dict):
            raise Exception(
                f"[WORKFLOW ERROR] Step {index} invalid result"
            )

        results.append(result)

    return {
        "status": "completed",
        "event": event,
        "steps_executed": len(steps),
        "results": results,
    }


# ============================================================
# ✅ FAILURE-AWARE WORKFLOW
# ============================================================

def execute_with_failure_handling(event: dict, steps: list, context):
    """
    Stops execution if a step fails.

    Failure defined as:
        result["status"] == "failed"
    """

    current_event = dict(event)
    results = []

    for index, step in enumerate(steps):
        result = step(current_event, context)

        if not isinstance(result, dict):
            raise Exception(
                f"[WORKFLOW ERROR] Step {index} invalid result"
            )

        results.append(result)

        if result.get("status") == "failed":
            return {
                "status": "failed",
                "failed_step": index,
                "event": current_event,
                "results": results,
            }

    return {
        "status": "completed",
        "event": current_event,
        "steps_executed": len(results),
        "results": results,
    }


# ============================================================
# ✅ BULK WORKFLOW EXECUTION
# ============================================================

def execute_bulk_workflows(events: list, steps: list, context):
    """
    Executes workflow for multiple events independently.
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    outputs = []

    for event in events:
        result = execute_step_workflow(event, steps, context)
        outputs.append(result)

    return outputs


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_workflow_steps(steps: list):
    """
    Ensure all workflow steps are valid.
    """

    if not isinstance(steps, list):
        raise TypeError("Steps must be a list")

    for i, step in enumerate(steps):
        if not callable(step):
            raise Exception(
                f"[WORKFLOW ERROR] Step {i} is not callable"
            )

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_workflow_determinism(event: dict, steps: list, context):
    """
    Ensures workflow behaves deterministically.
    """

    r1 = execute_step_workflow(event, steps, context)
    r2 = execute_step_workflow(event, steps, context)

    if r1 != r2:
        raise Exception(
            "[WORKFLOW ERROR] Non-deterministic workflow execution"
        )

    return True


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_workflow(event: dict, steps: list, context):
    """
    Debug helper showing workflow progression.
    """

    current_event = dict(event)
    trace = []

    for index, step in enumerate(steps):
        result = step(current_event, context)

        trace.append({
            "step": index,
            "result": result,
        })

    return {
        "event_id": event.get("event_id"),
        "trace": trace,
    }
