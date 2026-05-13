# ecosystems/afriride/tests/test_concurrent_assignment.py

from ecosystems.afriride.runtime.replay import run_replay


def test_replay_equivalence_under_concurrent_admissible_mutation():
    """
    This test asserts that concurrent admissible mutation
    produces a single canonical execution history.

    It verifies that:
    - replay hashes are identical across runs
    - replay-defining traces are identical
    - final canonical state is stable and deterministic
    """

    r1 = run_replay()
    r2 = run_replay()

    # Replay identity must be stable
    assert r1["hash"] == r2["hash"]

    # Canonical trace must be identical
    assert r1["trace"] == r2["trace"]

    # Final canonical state must be deterministic and identical
    assert r1["final_state"] == {
        "drivers_available": ["B"],
        "ride_status": "OPEN",
        "assigned_driver": "A",
        "ride_a_assigned": None,
        "ride_b_assigned": None,
    }