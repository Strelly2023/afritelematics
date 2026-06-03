from afritech.simulation.scale.recovery_storm import run_recovery_storm


# ============================================================
# TEST 1 — BASIC RECOVERY STABILITY
# ============================================================

def test_recovery_basic():
    runs = run_recovery_storm(
        cycles=3,
        worker_count=5,
        event_count=100,
        failure_rate=5,
    )

    assert runs[0] == runs[1] == runs[2]


# ============================================================
# TEST 2 — HIGH FAILURE STORM
# ============================================================

def test_recovery_high_failure():
    runs = run_recovery_storm(
        cycles=3,
        worker_count=8,
        event_count=200,
        failure_rate=3,
    )

    assert runs[0] == runs[1] == runs[2]


# ============================================================
# TEST 3 — EXTREME FAILURE STORM
# ============================================================

def test_recovery_extreme_failure():
    runs = run_recovery_storm(
        cycles=3,
        worker_count=10,
        event_count=300,
        failure_rate=2,
    )

    assert runs[0] == runs[1] == runs[2]


# ============================================================
# TEST 4 — SCALING CONSISTENCY DURING RECOVERY
# ============================================================

def test_recovery_scaling_consistency():
    small = run_recovery_storm(
        cycles=2,
        worker_count=3,
        event_count=150,
        failure_rate=4,
    )

    large = run_recovery_storm(
        cycles=2,
        worker_count=12,
        event_count=150,
        failure_rate=4,
    )

    assert small[0] == large[0]


# ============================================================
# TEST 5 — MULTI-CYCLE LONG STORM
# ============================================================

def test_long_recovery_storm():
    runs = run_recovery_storm(
        cycles=5,
        worker_count=6,
        event_count=200,
        failure_rate=3,
    )

    first = runs[0]
    for r in runs[1:]:
        assert r == first


# ============================================================
# TEST 6 — OUTPUT VALIDITY
# ============================================================

def test_recovery_output_valid():
    runs = run_recovery_storm(
        cycles=3,
        worker_count=5,
        event_count=120,
        failure_rate=4,
    )

    for run in runs:
        assert isinstance(run, list)
        assert all(isinstance(x, str) for x in run)
        assert all(len(x) > 0 for x in run)


# ============================================================
# TEST 7 — NO DIVERGENCE ACROSS STORMS
# ============================================================

def test_no_divergence_between_storms():
    storm1 = run_recovery_storm(
        cycles=3,
        worker_count=7,
        event_count=180,
        failure_rate=3,
    )

    storm2 = run_recovery_storm(
        cycles=3,
        worker_count=7,
        event_count=180,
        failure_rate=3,
    )

    assert storm1 == storm2