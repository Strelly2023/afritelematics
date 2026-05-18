from __future__ import annotations

from afritech.runtime.profiles import resolve_profile, validate_operation


def test_replay_critical_profile_resolves_runtime_constraints() -> None:
    profile = resolve_profile("REPLAY_CRITICAL")

    assert "SEM-DET-001" in profile["requires"]
    assert profile["runtime_constraints"]["deterministic_only"] is True
    assert profile["runtime_constraints"]["replay_required"] is True


def test_profile_validation_rejects_side_effects() -> None:
    profile = resolve_profile("REPLAY_CRITICAL")

    assert not validate_operation(
        {
            "deterministic": True,
            "side_effects": ["network"],
            "replayable": True,
        },
        profile,
    )


def test_profile_validation_accepts_replayable_deterministic_operation() -> None:
    profile = resolve_profile("REPLAY_CRITICAL")

    assert validate_operation(
        {
            "deterministic": True,
            "side_effects": [],
            "replayable": True,
        },
        profile,
    )
