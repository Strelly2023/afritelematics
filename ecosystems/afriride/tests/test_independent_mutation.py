# ecosystems/afriride/tests/test_independent_mutation.py

from ecosystems.afriride.runtime.replay import (
    run_independent_replay_variant_a,
    run_independent_replay_variant_b,
)


def test_independent_mutations_are_canonical():
    """
    This test asserts that independent, non‑conflicting mutations
    compose into a single canonical replay‑legitimate history.

    It verifies that:
    - replay hashes are identical across variants
    - replay‑defining traces are identical
    - final canonical state is identical
    - ordering is not emergent or scheduler‑defined
    """

    r1 = run_independent_replay_variant_a()
    r2 = run_independent_replay_variant_b()

    # Replay identity must be stable
    assert r1["hash"] == r2["hash"]

    # Canonical trace must be identical
    assert r1["trace"] == r2["trace"]

    # Final canonical state must be identical
    assert r1["final_state"] == r2["final_state"]

    # Explicit expected canonical state
    assert r1["final_state"] == {
        "drivers_available": [],
        "ride_status": "OPEN",
        "assigned_driver": None,
        "ride_a_assigned": "A",
        "ride_b_assigned": "B",
    }