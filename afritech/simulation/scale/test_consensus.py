from afritech.simulation.scale.consensus_simulator import (
    run_consensus_round,
)


# ============================================================
# TEST 1 — BASIC CONSENSUS
# ============================================================

def test_basic_consensus():
    result = run_consensus_round(
        worker_counts=[3, 5, 7],
        event_count=100,
    )

    assert result["votes"] == result["total_nodes"]


# ============================================================
# TEST 2 — CONSENSUS WITH FAILURES
# ============================================================

def test_consensus_with_failures():
    result = run_consensus_round(
        worker_counts=[4, 6, 8],
        event_count=150,
        inject_failures=True,
        failure_rate=5,
    )

    assert result["votes"] == result["total_nodes"]


# ============================================================
# TEST 3 — CONSENSUS UNDER EXTREME FAILURE
# ============================================================

def test_consensus_extreme_failure():
    result = run_consensus_round(
        worker_counts=[5, 7, 9],
        event_count=200,
        inject_failures=True,
        failure_rate=2,
    )

    assert result["votes"] == result["total_nodes"]


# ============================================================
# TEST 4 — LARGE CLUSTER CONSENSUS
# ============================================================

def test_large_cluster_consensus():
    result = run_consensus_round(
        worker_counts=[3, 4, 5, 6, 7],
        event_count=250,
    )

    assert result["votes"] == result["total_nodes"]


# ============================================================
# TEST 5 — MULTI-ROUND CONSISTENCY
# ============================================================

def test_consensus_repeatability():
    r1 = run_consensus_round(
        worker_counts=[3, 5, 7],
        event_count=120,
    )

    r2 = run_consensus_round(
        worker_counts=[3, 5, 7],
        event_count=120,
    )

    assert r1["consensus"] == r2["consensus"]


# ============================================================
# TEST 6 — PARTIAL DISAGREEMENT (HYBRID CASE)
# ============================================================

def test_consensus_majority_rule():
    result = run_consensus_round(
        worker_counts=[3, 5, 7],
        event_count=100,
        inject_failures=True,
        failure_rate=3,
    )

    # majority must be >= 2
    assert result["votes"] >= 2