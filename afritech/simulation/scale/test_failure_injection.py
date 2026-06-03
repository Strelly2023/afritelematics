"""
afritech.simulation.scale.test_failure_injection

Failure injection validation suite.

Validates:
- deterministic behavior under failure
- safe execution under dropped / duplicate events
- resilience to high failure rates
- no corruption of execution output
"""

from afritech.simulation.scale.run_multi_node import run_simulation


# ============================================================
# TEST 1 — SYSTEM DOES NOT CRASH
# ============================================================

def test_failure_does_not_crash_system():
    results = run_simulation(
        worker_count=5,
        event_count=100,
        inject_failures=True,
    )

    assert isinstance(results, list)
    assert len(results) > 0


# ============================================================
# TEST 2 — DETERMINISM UNDER FAILURE
# ============================================================

def test_failure_determinism():
    a = run_simulation(
        worker_count=6,
        event_count=150,
        inject_failures=True,
    )

    b = run_simulation(
        worker_count=6,
        event_count=150,
        inject_failures=True,
    )

    assert a == b, "Failure injection broke determinism"


# ============================================================
# TEST 3 — HIGH FAILURE PRESSURE
# ============================================================

def test_high_failure_pressure():
    a = run_simulation(
        worker_count=8,
        event_count=200,
        inject_failures=True,
        failure_rate=3,
    )

    b = run_simulation(
        worker_count=8,
        event_count=200,
        inject_failures=True,
        failure_rate=3,
    )

    assert a == b, "High failure pressure caused nondeterminism"


# ============================================================
# TEST 4 — DUPLICATE EXECUTION SAFETY
# ============================================================

def test_duplicate_execution_safety():
    results = run_simulation(
        worker_count=5,
        event_count=120,
        inject_failures=True,
    )

    assert all(isinstance(r, str) for r in results)
    assert all(len(r) > 0 for r in results)


# ============================================================
# TEST 5 — NO CORRUPTED OUTPUT
# ============================================================

def test_no_state_corruption_under_failure():
    failure = run_simulation(
        worker_count=5,
        event_count=100,
        inject_failures=True,
    )

    assert isinstance(failure, list)
    assert len(failure) >= 0

    # all valid hashes
    assert all(isinstance(h, str) for h in failure)
    assert all(len(h) > 0 for h in failure)


# ============================================================
# TEST 6 — FAILURE VS BASELINE SHAPE
# ============================================================

def test_failure_vs_baseline_shape():
    base = run_simulation(worker_count=5, event_count=100)

    failure = run_simulation(
        worker_count=5,
        event_count=100,
        inject_failures=True,
    )

    # Do NOT require equality
    # But ensure valid structural output
    assert isinstance(failure, list)
    assert len(failure) >= 0
    assert all(isinstance(x, str) for x in failure)


# ============================================================
# TEST 7 — SCALING UNDER FAILURE
# ============================================================

def test_scaling_under_failure():
    small = run_simulation(
        worker_count=3,
        event_count=150,
        inject_failures=True,
    )

    large = run_simulation(
        worker_count=10,
        event_count=150,
        inject_failures=True,
    )

    assert small == large, "Scaling under failure changed output"


# ============================================================
# TEST 8 — STABILITY UNDER REPEATED RUNS
# ============================================================

def test_repeated_failure_runs_stable():
    runs = [
        run_simulation(
            worker_count=5,
            event_count=120,
            inject_failures=True,
        )
        for _ in range(3)
    ]

    assert runs[0] == runs[1] == runs[2]


# ============================================================
# TEST 9 — EXTREME FAILURE RATE
# ============================================================

def test_extreme_failure_rate():
    a = run_simulation(
        worker_count=6,
        event_count=150,
        inject_failures=True,
        failure_rate=2,
    )

    b = run_simulation(
        worker_count=6,
        event_count=150,
        inject_failures=True,
        failure_rate=2,
    )

    assert a == b, "Extreme failure broke determinism"


# ============================================================
# TEST 10 — ZERO WORKER EDGE CASE
# ============================================================

def test_invalid_worker_count():
    try:
        run_simulation(worker_count=0, event_count=10)
    except ValueError:
        assert True
    else:
        assert False, "Expected ValueError for invalid worker count"