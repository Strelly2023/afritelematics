from afritech.simulation.scale.partition_drift_probe import (
    capture_partition_mapping,
)


# ============================================================
# TEST 1 — BASIC STABILITY
# ============================================================

def test_partition_stability_basic():
    m1 = capture_partition_mapping(100)
    m2 = capture_partition_mapping(100)

    assert m1 == m2, "Partition drift detected"


# ============================================================
# TEST 2 — LARGE SCALE STABILITY
# ============================================================

def test_partition_stability_large_scale():
    m1 = capture_partition_mapping(500)
    m2 = capture_partition_mapping(500)

    assert m1 == m2


# ============================================================
# TEST 3 — REPLAY STABILITY
# ============================================================

def test_partition_stability_replay():
    m1 = capture_partition_mapping(200)
    m2 = capture_partition_mapping(200)

    assert m1 == m2


# ============================================================
# TEST 4 — PARTITION DISTRIBUTION CONSISTENCY
# ============================================================

def test_partition_distribution_consistency():
    m1 = capture_partition_mapping(300)
    m2 = capture_partition_mapping(300)

    counts1 = {}
    counts2 = {}

    for p in m1.values():
        counts1[p] = counts1.get(p, 0) + 1

    for p in m2.values():
        counts2[p] = counts2.get(p, 0) + 1

    assert counts1 == counts2


# ============================================================
# TEST 5 — IDENTITY-BASED ROUTING STABILITY
# ============================================================

def test_partition_identity_consistency():
    m1 = capture_partition_mapping(150)
    m2 = capture_partition_mapping(150)

    for eid in m1:
        assert m1[eid] == m2[eid]


# ============================================================
# TEST 6 — MULTIPLE RUN CONSISTENCY
# ============================================================

def test_partition_multiple_runs():
    runs = [
        capture_partition_mapping(200)
        for _ in range(3)
    ]

    assert runs[0] == runs[1] == runs[2]


# ============================================================
# TEST 7 — NO PARTITION LOSS
# ============================================================

def test_no_partition_loss():
    mapping = capture_partition_mapping(300)

    partitions = set(mapping.values())

    assert len(partitions) > 0