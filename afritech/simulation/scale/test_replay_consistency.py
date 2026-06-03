from afritech.simulation.scale.run_multi_node import run_simulation
from afritech.simulation.scale.replay_runner import replay_simulation


# ============================================================
# TEST 1 — BASIC REPLAY CONSISTENCY
# ============================================================

def test_replay_basic():
    execution = run_simulation(worker_count=5, event_count=100)
    replay = replay_simulation(worker_count=5, event_count=100)

    assert execution == replay


# ============================================================
# TEST 2 — LARGE SCALE REPLAY
# ============================================================

def test_replay_large_scale():
    execution = run_simulation(worker_count=10, event_count=500)
    replay = replay_simulation(worker_count=10, event_count=500)

    assert execution == replay


# ============================================================
# TEST 3 — SCALING INVARIANCE
# ============================================================

def test_replay_scaling_invariance():
    execution = run_simulation(worker_count=5, event_count=200)
    replay = replay_simulation(worker_count=15, event_count=200)

    assert execution == replay


# ============================================================
# TEST 4 — FAILURE REPLAY CONSISTENCY
# ============================================================

def test_replay_with_failures():
    execution = run_simulation(
        worker_count=8,
        event_count=300,
        inject_failures=True,
        failure_rate=5,
    )

    replay = replay_simulation(
        worker_count=8,
        event_count=300,
        inject_failures=True,
        failure_rate=5,
    )

    assert execution == replay


# ============================================================
# TEST 5 — EXTREME CHAOS REPLAY
# ============================================================

def test_replay_extreme_chaos():
    execution = run_simulation(
        worker_count=12,
        event_count=400,
        inject_failures=True,
        failure_rate=2,
    )

    replay = replay_simulation(
        worker_count=12,
        event_count=400,
        inject_failures=True,
        failure_rate=2,
    )

    assert execution == replay


# ============================================================
# TEST 6 — MULTI-CYCLE REPLAY STABILITY
# ============================================================

def test_replay_multiple_cycles():
    runs = [
        replay_simulation(worker_count=6, event_count=200)
        for _ in range(3)
    ]

    assert runs[0] == runs[1] == runs[2]


# ============================================================
# TEST 7 — ORDER INTEGRITY
# ============================================================

def test_replay_order_integrity():
    execution = run_simulation(worker_count=5, event_count=150)
    replay = replay_simulation(worker_count=5, event_count=150)

    assert execution == replay
    assert len(execution) == len(replay)


# ============================================================
# TEST 8 — HIGH VOLUME REPLAY
# ============================================================

def test_replay_high_volume():
    execution = run_simulation(worker_count=10, event_count=1000)
    replay = replay_simulation(worker_count=10, event_count=1000)

    assert execution == replay
