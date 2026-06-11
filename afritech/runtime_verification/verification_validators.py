from __future__ import annotations


def validate_observation_integrity(observation: dict[str, object]) -> dict[str, object]:
    violations: list[str] = []
    for field in ("event", "expected_state", "observed_state", "contract"):
        if not observation.get(field):
            violations.append(f"missing observation field: {field}")
    for field in ("activation_allowed", "runtime_mutation_allowed", "rollback_execution_allowed"):
        if observation.get(field) is not False:
            violations.append(f"observation gained authority: {field}")
    return {"valid": not violations, "violations": tuple(violations)}


def validate_drift_non_authority(drift: dict[str, object]) -> dict[str, object]:
    violations = tuple(
        field
        for field in ("activation_allowed", "runtime_mutation_allowed", "rollback_execution_allowed")
        if drift.get(field) is not False
    )
    return {"valid": not violations, "violations": violations}


__all__ = ["validate_drift_non_authority", "validate_observation_integrity"]
