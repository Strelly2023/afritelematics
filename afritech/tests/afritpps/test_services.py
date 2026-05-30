from __future__ import annotations

from afritech.afritpps.services import (
    build_operational_model,
    build_program_from_mappings,
)


def _capabilities():
    return (
        {
            "id": "cap.dispatch",
            "name": "Dispatch",
            "capability_type": "service",
            "maturity_level": "measured",
            "owner": "ops",
            "service_objective": "dispatch",
        },
    )


def _workflows():
    return (
        {
            "id": "workflow.dispatch",
            "name": "Dispatch",
            "steps": (
                {
                    "id": "step.1",
                    "capability_id": "cap.dispatch",
                    "name": "Receive",
                    "process": "intake",
                    "role": "dispatcher",
                    "expected_output": "request",
                    "sequence": 1,
                },
            ),
        },
    )


def test_build_program_from_mappings():
    program = build_program_from_mappings(
        program_id="program.mobility",
        name="Mobility",
        capabilities=_capabilities(),
        workflows=_workflows(),
    )

    assert program.program_id == "program.mobility"
    assert len(program.capabilities) == 1
    assert len(program.workflows) == 1


def test_build_operational_model_is_ga_elite_execution_view():
    program = build_program_from_mappings(
        program_id="program.mobility",
        name="Mobility",
        capabilities=_capabilities(),
        workflows=_workflows(),
    )

    model = build_operational_model(program)

    assert model["component"] == "AfriTPPS"
    assert model["pillar"] == "EXECUTION"
    assert model["status"] == "GA_ELITE_EXECUTION_PILLAR"
    assert model["question_answered"] == "How should it be executed?"
    assert model["defines_execution"] is True
    assert model["creates_governance_authority"] is False
    assert model["creates_proof_authority"] is False
    assert model["creates_replay_authority"] is False
    assert model["mutates_proof"] is False
    assert model["program"]["program_id"] == "program.mobility"
    assert model["execution_metrics"]["metric_count"] == 3
