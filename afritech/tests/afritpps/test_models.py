from __future__ import annotations

import pytest

from afritech.afritpps.models import (
    AfriTPPSCapability,
    AfriTPPSModelError,
    AfriTPPSProgram,
    AfriTPPSWorkflow,
    AfriTPPSWorkflowStep,
)


def _capability(capability_id: str = "cap.dispatch") -> AfriTPPSCapability:
    return AfriTPPSCapability(
        capability_id=capability_id,
        name="Dispatch Operations",
        capability_type="service",
        maturity_level="measured",
        owner="operations",
        service_objective="assign rides deterministically",
        metadata=(("region", "pilot"),),
    )


def _workflow() -> AfriTPPSWorkflow:
    return AfriTPPSWorkflow(
        workflow_id="workflow.dispatch",
        name="Dispatch workflow",
        steps=(
            AfriTPPSWorkflowStep(
                step_id="step.2",
                capability_id="cap.dispatch",
                name="Assign driver",
                process="assignment",
                role="dispatcher",
                expected_output="driver assignment",
                sequence=2,
            ),
            AfriTPPSWorkflowStep(
                step_id="step.1",
                capability_id="cap.dispatch",
                name="Receive request",
                process="intake",
                role="dispatcher",
                expected_output="validated request",
                sequence=1,
                status="ready",
            ),
        ),
    )


def test_capability_canonical_dict_preserves_execution_boundary():
    data = _capability().canonical_dict()

    assert data["component"] == "AfriTPPS"
    assert data["pillar"] == "EXECUTION"
    assert data["classification"] == "OPERATIONAL_EXECUTION_MODEL"
    assert data["capability_id"] == "cap.dispatch"
    assert data["metadata"] == {"region": "pilot"}
    assert data["defines_execution"] is True
    assert data["creates_governance_authority"] is False
    assert data["creates_proof_authority"] is False
    assert data["creates_replay_authority"] is False
    assert data["mutates_proof"] is False


def test_capability_from_mapping_normalizes_payload():
    capability = AfriTPPSCapability.from_mapping(
        {
            "id": "cap.routing",
            "name": "Routing",
            "capability_type": "technology",
            "maturity_level": "defined",
            "owner": "platform",
            "service_objective": "route safely",
            "metadata": {"priority": 1},
        }
    )

    assert capability.capability_id == "cap.routing"
    assert capability.metadata_dict() == {"priority": 1}


def test_capability_rejects_invalid_type():
    with pytest.raises(AfriTPPSModelError):
        AfriTPPSCapability(
            capability_id="cap.bad",
            name="Bad",
            capability_type="invalid",
            maturity_level="managed",
            owner="ops",
            service_objective="none",
        )


def test_workflow_orders_steps_deterministically():
    workflow = _workflow()

    assert [step.step_id for step in workflow.steps] == ["step.1", "step.2"]
    assert workflow.canonical_dict()["step_count"] == 2


def test_workflow_rejects_non_contiguous_sequence():
    with pytest.raises(AfriTPPSModelError, match="contiguous"):
        AfriTPPSWorkflow(
            workflow_id="workflow.bad",
            name="Bad workflow",
            steps=(
                AfriTPPSWorkflowStep(
                    step_id="step.2",
                    capability_id="cap.dispatch",
                    name="Skip",
                    process="assignment",
                    role="dispatcher",
                    expected_output="assignment",
                    sequence=2,
                ),
            ),
        )


def test_workflow_from_mapping_builds_steps():
    workflow = AfriTPPSWorkflow.from_mapping(
        {
            "id": "workflow.dispatch",
            "name": "Dispatch",
            "steps": [
                {
                    "id": "step.1",
                    "capability_id": "cap.dispatch",
                    "name": "Receive",
                    "process": "intake",
                    "role": "dispatcher",
                    "expected_output": "request",
                    "sequence": 1,
                }
            ],
        }
    )

    assert workflow.workflow_id == "workflow.dispatch"
    assert workflow.steps[0].status == "planned"


def test_program_validates_workflow_capability_references():
    program = AfriTPPSProgram(
        program_id="program.mobility",
        name="Mobility execution",
        capabilities=(_capability(),),
        workflows=(_workflow(),),
    )

    data = program.canonical_dict()

    assert data["program_id"] == "program.mobility"
    assert data["capability_count"] == 1
    assert data["workflow_count"] == 1
    assert data["defines_execution"] is True
    assert data["creates_governance_authority"] is False


def test_program_rejects_unknown_capability_reference():
    with pytest.raises(AfriTPPSModelError, match="unknown capability"):
        AfriTPPSProgram(
            program_id="program.bad",
            name="Bad",
            capabilities=(_capability("cap.other"),),
            workflows=(_workflow(),),
        )
