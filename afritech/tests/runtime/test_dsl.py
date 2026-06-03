"""
AfriTech DSL Tests

PURPOSE:
--------
Validate DSL layer:

- workflow parsing
- workflow model integrity
- validation correctness
- step registry behavior
- workflow execution
- conditional execution
- failure scenarios

CRITICAL GUARANTEE:
------------------
DSL must remain deterministic, safe, and non-mutating
"""

import pytest

from afritech.runtime.dsl.workflow_parser import WorkflowParser
from afritech.runtime.dsl.workflow_model import Workflow, Step
from afritech.runtime.dsl.validator import WorkflowValidator
from afritech.runtime.dsl.step_registry import StepRegistry
from afritech.runtime.dsl.workflow_executor import WorkflowExecutor

from afritech.runtime.async_runtime.queue_runtime import QueueRuntime
from afritech.runtime.async_runtime.worker_runtime import WorkerRuntime
#afritech/tests/runtime/test_dsl.py

# ============================================================
# ✅ FIXTURES
# ============================================================

@pytest.fixture
def basic_setup():
    parser = WorkflowParser()
    registry = StepRegistry()
    validator = WorkflowValidator(registry)
    executor = WorkflowExecutor(registry)

    queue = QueueRuntime()
    worker = WorkerRuntime(queue)

    class DummyContext:
        def __init__(self):
            self.policy = {
                "batch_size": 2,
                "retry_limit": 1,
                "transport_mode": "test",
                "partition_count": 10,
                "default_region": "test-region",
            }

    context = DummyContext()

    return parser, registry, validator, executor, queue, worker, context


# ============================================================
# ✅ PARSER TEST
# ============================================================

def test_workflow_parsing(basic_setup):
    parser, _, _, _, _, _, _ = basic_setup

    data = {
        "workflow": {
            "id": "test",
            "steps": ["a", "b"],
        }
    }

    wf = parser.parse(data)

    assert isinstance(wf, Workflow)
    assert wf.id == "test"
    assert wf.get_step_names() == ["a", "b"]


# ============================================================
# ✅ VALIDATION TEST
# ============================================================

def test_workflow_validation(basic_setup):
    parser, registry, validator, _, _, _, _ = basic_setup

    def step_a(**_):
        return {"event_id": "a", "payload": {}, "timestamp": 1}

    registry.register("a", step_a)

    wf = parser.parse({
        "workflow": {
            "id": "v1",
            "steps": ["a"]
        }
    })

    assert validator.validate(wf) is True


# ============================================================
# ✅ REGISTRY TEST
# ============================================================

def test_step_registry(basic_setup):
    _, registry, _, _, _, _, _ = basic_setup

    def step_x(**_):
        return {"event_id": "x", "payload": {}, "timestamp": 1}

    registry.register("x", step_x)

    assert registry.exists("x") is True
    assert callable(registry.get("x"))

    with pytest.raises(Exception):
        registry.get("unknown")


# ============================================================
# ✅ EXECUTION TEST
# ============================================================

def test_workflow_execution(basic_setup):
    parser, registry, validator, executor, queue, worker, context = basic_setup

    def step_a(**_):
        return {"event_id": "a", "payload": {}, "timestamp": 1}

    def step_b(**_):
        return {"event_id": "b", "payload": {}, "timestamp": 2}

    registry.register_bulk({
        "a": step_a,
        "b": step_b,
    })

    wf = parser.parse({
        "workflow": {
            "id": "exec",
            "steps": ["a", "b"],
        }
    })

    validator.validate(wf)

    result = executor.execute(wf, queue, context)

    assert result["workflow_id"] == "exec"
    assert len(result["steps"]) == 2
    assert result["steps"][0]["step"] == "a"


# ============================================================
# ✅ CONDITIONAL EXECUTION TEST
# ============================================================

def test_conditional_execution(basic_setup):
    parser, registry, validator, executor, queue, worker, context = basic_setup

    def step_a(**_):
        return {"event_id": "a", "payload": {}, "timestamp": 1}

    def step_b(**_):
        return {"event_id": "b", "payload": {}, "timestamp": 2}

    registry.register_bulk({
        "a": step_a,
        "b": step_b,
    })

    wf = parser.parse({
        "workflow": {
            "id": "cond",
            "steps": [
                {"name": "a"},
                {"name": "b", "metadata": {"if": "a"}},
            ],
        }
    })

    result = executor.execute(wf, queue, context)

    steps = [s["step"] for s in result["steps"]]

    assert "a" in steps
    assert "b" in steps


# ============================================================
# ✅ CONDITIONAL SKIP TEST
# ============================================================

def test_conditional_skip(basic_setup):
    parser, registry, validator, executor, queue, worker, context = basic_setup

    def step_b(**_):
        return {"event_id": "b", "payload": {}, "timestamp": 1}

    registry.register("b", step_b)

    wf = parser.parse({
        "workflow": {
            "id": "skip",
            "steps": [
                {"name": "b", "metadata": {"if": "a"}},  # 'a' never ran
            ],
        }
    })

    result = executor.execute(wf, queue, context)

    assert result["steps"][0]["status"] == "skipped"


# ============================================================
# ✅ FAILURE TEST
# ============================================================

def test_execution_failure(basic_setup):
    parser, registry, validator, executor, queue, worker, context = basic_setup

    def bad_step(**_):
        raise Exception("boom")

    registry.register("fail", bad_step)

    wf = parser.parse({
        "workflow": {
            "id": "fail",
            "steps": ["fail"],
        }
    })

    result = executor.execute_safe(wf, queue, context)

    assert result["steps"][0]["status"] == "failed"


# ============================================================
# ✅ PREVIEW TEST
# ============================================================

def test_workflow_preview(basic_setup):
    parser, _, _, executor, _, _, _ = basic_setup

    wf = parser.parse({
        "workflow": {
            "id": "preview",
            "steps": ["a", "b"],
        }
    })

    preview = executor.preview(wf)

    assert preview["workflow_id"] == "preview"
    assert preview["steps"] == ["a", "b"]


# ============================================================
# ✅ DETERMINISM TEST
# ============================================================

def test_workflow_determinism(basic_setup):
    parser, registry, validator, executor, queue, worker, context = basic_setup

    def step_a(**_):
        return {"event_id": "a", "payload": {}, "timestamp": 1}

    registry.register("a", step_a)

    wf = parser.parse({
        "workflow": {
            "id": "det",
            "steps": ["a"],
        }
    })

    r1 = executor.execute(wf, queue, context)
    r2 = executor.execute(wf, queue, context)

    assert r1 == r2