"""
AfriTech Orchestration Manager

PURPOSE:
--------
Coordinates workflow execution and decision flow (FLOW layer).

Responsibilities:
- validate orchestration inputs
- apply decision routing (branching)
- manage workflow execution (multi-step)
- enforce orchestration safety rules
- integrate with async + locality + adaptive layers

CRITICAL LAW:
-------------
Orchestration Manager MAY:
- coordinate execution flow
- invoke workflows
- apply routing decisions

Orchestration Manager may NOT:
- mutate event payload
- change event semantics
- interfere with replay truth
"""

from afritech.runtime.orchestration.workflow_engine import execute_workflow
from afritech.runtime.orchestration.decision_engine import make_decision
from afritech.runtime.orchestration.saga_manager import apply_saga
from afritech.runtime.orchestration.dependency_graph import DependencyGraph
from afritech.runtime.guards import enforce_orchestration_safety


# ============================================================
# ✅ ORCHESTRATION MANAGER
# ============================================================

class OrchestrationManager:
    """
    Coordinates execution flow across workflows, decisions, and dependencies.
    """

    def __init__(self):
        # Dependency tracking (optional usage)
        self.dependency_graph = DependencyGraph()

    # ========================================================
    # ✅ MAIN ENTRY POINT
    # ========================================================

    def process(self, event: dict, context, decisions: dict = None):
        """
        Main orchestration entry point.

        Steps:
        1. Validate orchestration decisions
        2. Apply routing / branching
        3. Execute workflow
        4. Apply saga (failure compensation)

        Returns:
            structured orchestration result
        """

        # ----------------------------------------------------
        # 1. Validate orchestration decisions
        # ----------------------------------------------------
        if decisions:
            enforce_orchestration_safety(event, decisions)

        # ----------------------------------------------------
        # 2. Apply decision routing
        # ----------------------------------------------------
        routed_event = make_decision(event, decisions or {})

        # ----------------------------------------------------
        # 3. Execute workflow
        # ----------------------------------------------------
        workflow_result = execute_workflow(routed_event, context)

        # ----------------------------------------------------
        # 4. Apply saga (safe compensation layer)
        # ----------------------------------------------------
        final_result = apply_saga(workflow_result, context)

        return {
            "status": final_result.get("status"),
            "event_id": event.get("event_id"),
            "result": final_result,
        }

    # ========================================================
    # ✅ DEPENDENCY-AWARE PROCESSING
    # ========================================================

    def process_with_dependencies(
        self,
        event: dict,
        context,
        completed_events: set,
        dependencies: list = None,
    ):
        """
        Process event only if dependencies are satisfied.
        """

        event_id = event.get("event_id")
        deps = dependencies or []

        # Register dependencies
        for dep in deps:
            self.dependency_graph.add_dependency(event_id, dep)

        # Check readiness
        if not self.dependency_graph.is_ready(event_id, completed_events):
            return {
                "status": "waiting",
                "event_id": event_id,
                "reason": "dependencies not satisfied",
            }

        return self.process(event, context)

    # ========================================================
    # ✅ WORKFLOW BATCH PROCESSING
    # ========================================================

    def process_batch(self, events: list, context, decisions_map: dict = None):
        """
        Process multiple events with optional decisions.

        Guarantees:
        - each event processed independently
        - no cross-event mutation
        """

        if not isinstance(events, list):
            raise TypeError("Events must be a list")

        results = []

        for event in events:
            decisions = None
            if decisions_map:
                decisions = decisions_map.get(event.get("event_id"))

            result = self.process(event, context, decisions)
            results.append(result)

        return results

    # ========================================================
    # ✅ CONDITIONAL WORKFLOW EXECUTION
    # ========================================================

    def process_with_condition(self, event: dict, context, condition_fn):
        """
        Execute workflow only if condition is satisfied.

        condition_fn(event) -> bool
        """

        if not callable(condition_fn):
            raise TypeError("condition_fn must be callable")

        if not condition_fn(event):
            return {
                "status": "skipped",
                "event_id": event.get("event_id"),
            }

        return self.process(event, context)

    # ========================================================
    # ✅ SAFE DECISION PREVIEW (DRY RUN)
    # ========================================================

    def preview(self, event: dict, decisions: dict = None):
        """
        Preview orchestration flow WITHOUT execution.

        Useful for:
        - debugging
        - UI inspection
        """

        if decisions:
            enforce_orchestration_safety(event, decisions)

        routed_event = make_decision(event, decisions or {})

        return {
            "event_id": event.get("event_id"),
            "decisions": decisions,
            "routed_event": routed_event,
        }

    # ========================================================
    # ✅ TRACE (OBSERVABILITY)
    # ========================================================

    def trace(self, event: dict, context, decisions: dict = None):
        """
        Full trace of orchestration execution.

        Provides full visibility WITHOUT mutating anything.
        """

        if decisions:
            enforce_orchestration_safety(event, decisions)

        routed_event = make_decision(event, decisions or {})
        workflow_result = execute_workflow(routed_event, context)

        return {
            "input_event": event,
            "decisions": decisions,
            "routed_event": routed_event,
            "workflow_result": workflow_result,
        }