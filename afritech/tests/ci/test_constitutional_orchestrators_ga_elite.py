from __future__ import annotations

import pytest

from afritech.ci.constitutional_pipeline import (
    PIPELINE,
    ConstitutionalPipelineError,
    PipelineStep,
    validate_pipeline_registry,
)
from afritech.ci.constitutional_validation import (
    SUBSYSTEMS,
    ConstitutionalValidationError,
    ValidationSubsystem,
    ordered_subsystems,
    validate_subsystem_registry,
)


def test_constitutional_validation_registry_is_unique_and_phase_complete():
    validate_subsystem_registry(SUBSYSTEMS)

    names = [subsystem.name for subsystem in SUBSYSTEMS]
    modules = [subsystem.module for subsystem in SUBSYSTEMS]

    assert len(names) == len(set(names))
    assert len(modules) == len(set(modules))
    assert {subsystem.phase for subsystem in SUBSYSTEMS} == {1, 2, 3, 4, 5}


def test_constitutional_validation_rejects_duplicate_module():
    duplicate = (
        ValidationSubsystem(
            name="first",
            module="afritech.ci.identity_validator",
            phase=1,
        ),
        ValidationSubsystem(
            name="second",
            module="afritech.ci.identity_validator",
            phase=2,
        ),
    )

    with pytest.raises(ConstitutionalValidationError):
        validate_subsystem_registry(duplicate)


def test_constitutional_validation_order_is_deterministic():
    ordered = ordered_subsystems(SUBSYSTEMS)

    assert ordered == tuple(sorted(SUBSYSTEMS, key=lambda item: (item.phase, item.name)))


def test_constitutional_pipeline_registry_is_unique():
    validate_pipeline_registry(PIPELINE)

    names = [step.name for step in PIPELINE]
    commands = [step.command for step in PIPELINE]

    assert len(names) == len(set(names))
    assert len(commands) == len(set(commands))


def test_constitutional_pipeline_rejects_duplicate_step_name():
    duplicate = (
        PipelineStep(
            name="same",
            phase="CONSTITUTION",
            command=("python3", "-m", "afritech.ci.identity_validator"),
        ),
        PipelineStep(
            name="same",
            phase="CONSTITUTION",
            command=("python3", "-m", "afritech.ci.alias_validator"),
        ),
    )

    with pytest.raises(ConstitutionalPipelineError):
        validate_pipeline_registry(duplicate)
