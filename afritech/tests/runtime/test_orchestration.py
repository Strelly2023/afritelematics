"""
AfriTech Orchestration Tests

PURPOSE:
--------
Validate orchestration layer:

- decision routing correctness
- workflow execution behavior
- dependency resolution
- state transitions
- saga compensation
- full orchestration flow

CRITICAL GUARANTEE:
------------------
Orchestration MUST NOT mutate event semantics
"""

import pytest

from afritech.runtime.orchestration.orchestration_manager import OrchestrationManager
from afritech.runtime.orchestration.workflow_engine import (
    execute_step_workflow,
)
from afritech.runtime.orchestration.dependency_graph import DependencyGraph
from afritech.runtime.orchestration.state_machine import StateMachine
from afritech.runtime.orchestration.saga_manager import apply_saga
from afritech.runtime.orchestration.decision_engine import make_decision

#afritech/tests/runtime/test_orchestration.py
# ============================================================
# ✅ TEST CONTEXT
# ============================================================

class DummyContext:
    def __init__(self):
        self.policy = {}


@pytest.fixture
def context():
    return DummyContext()


# ============================================================
# ✅ DECISION ENGINE TEST
# ============================================================

def test_decision_engine_basic(context):
    event = {"event_id": "1", "payload": {}}

    decisions = {"route": "alpha", "priority": 5}

    result = make_decision(event, decisions)

    assert result["_route"] == "alpha"
    assert result["_priority"] == 5

    # Ensure original event unchanged
    assert "route" not in event


# ============================================================
# ✅ WORKFLOW ENGINE TEST
# ============================================================

def test_workflow_execution(context):
    def step1(event, context):
        return {"status": "ok", "event": event}

    def step2(event, context):
        return {"status": "ok", "event": event}

    event = {"event_id": "2", "payload": {}}

    result = execute_step_workflow(event, [step1, step2], context)

    assert result["status"] == "completed"
    assert result["steps_executed"] == 2


# ============================================================
# ✅ WORKFLOW FAILURE TEST
# ============================================================

def test_workflow_failure(context):
    def step1(event, context):
        return {"status": "ok", "event": event}

    def step2(event, context):
        return {"status": "failed", "event": event}

    event = {"event_id": "3", "payload": {}}

    result = execute_step_workflow(event, [step1, step2], context)

    # Step workflow does not auto-fail → still completes
    assert result["steps_executed"] == 2


# ============================================================
# ✅ DEPENDENCY GRAPH TEST
# ============================================================

def test_dependency_graph_basic():
    graph = DependencyGraph()

    graph.add_dependency("B", "A")

    assert graph.get_dependencies("B") == ["A"]
    assert graph.get_dependents("A") == ["B"]

    # A completed → B ready
    assert graph.is_ready("B", {"A"}) is True
    assert graph.is_ready("B", set()) is False


# ============================================================
# ✅ DEPENDENCY CYCLE DETECTION
# ============================================================

def test_dependency_cycle_detection():
    graph = DependencyGraph()

    graph.add_dependency("A", "B")
    graph.add_dependency("B", "A")

    assert graph.detect_cycle() is True


# ============================================================
# ✅ STATE MACHINE TEST
# ============================================================

def test_state_machine_transitions():
    sm = StateMachine()

    assert sm.get_state() == "init"

    sm.transition("start")
    assert sm.get_state() == "running"

    sm.transition("complete")
    assert sm.get_state() == "done"

    assert sm.is_terminal() is True


# ============================================================
# ✅ INVALID STATE TRANSITION
# ============================================================

def test_invalid_state_transition():
    sm = StateMachine()

    with pytest.raises(Exception):
        sm.transition("invalid_event")


# ============================================================
# ✅ SAGA COMPENSATION TEST
# ============================================================

def test_saga_compensation(context):
    def compensation_fn(context):
        return {"status": "rolled_back"}

    result = {
        "status": "failed",
        "results": [
            {"status": "ok"},
            {"status": "ok", "compensate": compensation_fn},
        ],
    }

    final = apply_saga(result, context)

    assert final["status"] == "compensated"
    assert len(final["compensations"]) == 1


# ============================================================
# ✅ SAGA NO-OP TEST
# ============================================================

def test_saga_no_compensation(context):
    result = {
        "status": "completed",
        "results": [],
    }

    final = apply_saga(result, context)

    assert final["status"] == "completed"


# ============================================================
# ✅ ORCHESTRATION MANAGER TEST
# ============================================================

def test_orchestration_manager_basic(context):
    manager = OrchestrationManager()

    event = {
        "event_id": "10",
        "payload": {"x": 1},
    }

    decisions = {"route": "beta"}

    result = manager.process(event, context, decisions)

    assert result["event_id"] == "10"
    assert result["status"] in ["completed", "compensated"]


# ============================================================
# ✅ ORCHESTRATION WITH DEPENDENCIES
# ============================================================

def test_orchestration_with_dependencies(context):
    manager = OrchestrationManager()

    event = {
        "event_id": "20",
        "payload": {},
    }

    # dependency not satisfied
    result1 = manager.process_with_dependencies(
        event,
        context,
        completed_events=set(),
        dependencies=["A"],
    )

    assert result1["status"] == "waiting"

    # dependency satisfied
    result2 = manager.process_with_dependencies(
        event,
        context,
        completed_events={"A"},
        dependencies=["A"],
    )

    assert result2["status"] == "completed"


# ============================================================
# ✅ BATCH PROCESSING TEST
# ============================================================

def test_orchestration_batch(context):
    manager = OrchestrationManager()

    events = [
        {"event_id": str(i), "payload": {}}
        for i in range(3)
    ]

    results = manager.process_batch(events, context)

    assert len(results) == 3
    assert all("status" in r for r in results)


# ============================================================
# ✅ DECISION DETERMINISM TEST
# ============================================================

def test_decision_determinism():
    event = {"event_id": "d1", "payload": {}}
    decisions = {"route": "x"}

    r1 = make_decision(event, decisions)
    r2 = make_decision(event, decisions)

    assert r1 == r2


# ============================================================
# ✅ ORCHESTRATION DOES NOT MUTATE EVENT
# ============================================================

def test_orchestration_no_mutation(context):
    manager = OrchestrationManager()

    event = {
        "event_id": "immut",
        "payload": {"v": 1},
    }

    original = dict(event)

    _ = manager.process(event, context)

    assert event == original