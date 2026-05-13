# ecosystems/afriride/tests/test_observational_replay.py

from ecosystems.afriride.runtime.replay import (
    run_replay_variant_a,
    run_replay_variant_b,
)


def test_observation_order_does_not_affect_replay_hash():
    """
    This test asserts that replay legitimacy is not influenced by
    observational or auxiliary command ordering.

    It verifies that:
    - replay hashes are identical across variants
    - replay-defining traces are identical
    - final canonical state is identical
    - observational emissions do not leak scheduler-defined ordering
      into replay identity
    """

    r1 = run_replay_variant_a()
    r2 = run_replay_variant_b()

    # Replay identity must be stable
    assert r1["hash"] == r2["hash"]

    # Canonical traces must be identical
    assert r1["trace"] == r2["trace"]

    # Final canonical state must be identical
    assert r1["final_state"] == r2["final_state"]

    # Explicit expected canonical state
    assert r1["final_state"] == {
        "drivers_available": ["B"],
        "ride_status": "OPEN",
        "assigned_driver": "A",
        "ride_a_assigned": None,
        "ride_b_assigned": None,
    }