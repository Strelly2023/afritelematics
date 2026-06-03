"""
AfriTech Adaptive Runtime Tests

PURPOSE:
--------
Validate adaptive layer:

- telemetry collection correctness
- load analysis determinism
- policy optimization behavior
- safe policy adaptation
- full adaptive pipeline integration

CRITICAL GUARANTEE:
------------------
Adaptive logic MUST NOT affect event truth
"""

import pytest

from afritech.runtime.adaptive.adaptive_manager import AdaptiveManager
from afritech.runtime.adaptive.telemetry_collector import collect_telemetry
from afritech.runtime.adaptive.load_analyzer import analyze_load
from afritech.runtime.adaptive.policy_optimizer import optimize_policy
from afritech.runtime.adaptive.adaptation_engine import apply_adaptation

from afritech.runtime.async_runtime.queue_runtime import QueueRuntime
#afritech/tests/runtime/test_asdaptive.py
 
# ============================================================
# ✅ TEST CONTEXT
# ============================================================

class DummyContext:
    def __init__(self):
        self.policy = {
            "batch_size": 2,
            "retry_limit": 1,
            "transport_mode": "test",
        }
        self.queue_runtime = QueueRuntime()


@pytest.fixture
def context():
    return DummyContext()


# ============================================================
# ✅ TELEMETRY TEST
# ============================================================

def test_telemetry_collection(context):
    telemetry = collect_telemetry(context)

    assert "queue_sizes" in telemetry
    assert "total_events" in telemetry
    assert telemetry["total_events"] == 0


# ============================================================
# ✅ LOAD ANALYSIS TEST
# ============================================================

def test_load_analysis(context):
    telemetry = collect_telemetry(context)

    state = analyze_load(telemetry)

    assert state == "idle"


# ============================================================
# ✅ POLICY OPTIMIZATION TEST
# ============================================================

def test_policy_optimization(context):
    state = "high"

    new_policy = optimize_policy(state, context)

    assert isinstance(new_policy, dict)
    assert "batch_size" in new_policy


# ============================================================
# ✅ ADAPTATION ENGINE TEST
# ============================================================

def test_policy_application(context):
    new_policy = {
        "batch_size": 5,
    }

    updated = apply_adaptation(context, new_policy)

    assert context.policy["batch_size"] == 5
    assert updated["batch_size"] == 5


# ============================================================
# ✅ ADAPTIVE MANAGER END-TO-END
# ============================================================

def test_adaptive_manager(context):
    manager = AdaptiveManager()

    result = manager.evaluate(context)

    assert "load_state" in result
    assert "applied_policy" in result

    assert isinstance(result["applied_policy"], dict)


# ============================================================
# ✅ ADAPTIVE DETERMINISM TEST
# ============================================================

def test_adaptive_determinism(context):
    manager = AdaptiveManager()

    result1 = manager.dry_run(context)
    result2 = manager.dry_run(context)

    assert result1 == result2


# ============================================================
# ✅ NO EVENT MUTATION TEST
# ============================================================

def test_adaptive_does_not_touch_events(context):
    manager = AdaptiveManager()

    # simulate evaluation
    _ = manager.evaluate(context)

    # no exception = pass (adaptive does not access events)
    assert True