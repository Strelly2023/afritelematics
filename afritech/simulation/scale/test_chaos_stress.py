from afritech.simulation.scale.run_multi_node import run_simulation
from afritech.simulation.scale.load_generator import (
    generate_events,
    generate_partition_skewed_events,
    generate_burst_events,
)


# ============================================================
# TEST 1 — HIGH FAILURE RATE
# ============================================================

def test_high_failure_rate_determinism():
    events = generate_events(200)

    a = run_simulation(
        worker_count=8,
        event_count=200,
        inject_failures=True,
    )

    b = run_simulation(
        worker_count=8,
        event_count=200,
        inject_failures=True,
    )

    assert a == b, "High failure rate broke determinism"


# ============================================================
# TEST 2 — PARTITION HOTSPOT
# ============================================================

def test_partition_hotspot():
    events = generate_partition_skewed_events(300)

    a = run_simulation(worker_count=5, event_count=300)
    b = run_simulation(worker_count=10, event_count=300)

    assert a == b, "Partition hotspot caused divergence"


# ============================================================
# TEST 3 — BURST LOAD
# ============================================================

def test_burst_load_stability():
    events = generate_burst_events(bursts=10, burst_size=20)

    a = run_simulation(worker_count=6, event_count=len(events))
    b = run_simulation(worker_count=6, event_count=len(events))

    assert a == b, "Burst load broke determinism"


# ============================================================
# TEST 4 — WORKER SCALING UNDER CHAOS
# ============================================================

def test_scaling_under_failure():
    events = generate_events(250)

    small = run_simulation(
        worker_count=3,
        event_count=250,
        inject_failures=True,
    )

    large = run_simulation(
        worker_count=12,
        event_count=250,
        inject_failures=True,
    )

    assert small == large, "Scaling + failures changed outcome"


# ============================================================
# TEST 5 — EXTREME MIXED CHAOS
# ============================================================

def test_extreme_chaos():
    events = generate_partition_skewed_events(500)

    a = run_simulation(
        worker_count=10,
        event_count=500,
        inject_failures=True,
    )

    b = run_simulation(
        worker_count=10,
        event_count=500,
        inject_failures=True,
    )

    assert a == b, "Extreme chaos broke determinism"