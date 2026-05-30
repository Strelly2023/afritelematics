from __future__ import annotations

import pytest

from afritech.afritpps.metrics import (
    AfriTPPSExecutionMetric,
    AfriTPPSMetricError,
    build_program_metric_bundle,
    calculate_readiness_score,
)
from afritech.afritpps.models import (
    AfriTPPSCapability,
    AfriTPPSProgram,
    AfriTPPSWorkflow,
    AfriTPPSWorkflowStep,
)


def _program() -> AfriTPPSProgram:
    capability_a = AfriTPPSCapability(
        capability_id="cap.dispatch",
        name="Dispatch",
        capability_type="service",
        maturity_level="measured",
        owner="ops",
        service_objective="dispatch",
    )
    capability_b = AfriTPPSCapability(
        capability_id="cap.routing",
        name="Routing",
        capability_type="technology",
        maturity_level="defined",
        owner="platform",
        service_objective="route",
    )
    workflow = AfriTPPSWorkflow(
        workflow_id="workflow.dispatch",
        name="Dispatch",
        steps=(
            AfriTPPSWorkflowStep(
                step_id="step.1",
                capability_id="cap.dispatch",
                name="Receive",
                process="intake",
                role="dispatcher",
                expected_output="request",
                sequence=1,
            ),
        ),
    )
    return AfriTPPSProgram(
        program_id="program.mobility",
        name="Mobility",
        capabilities=(capability_a, capability_b),
        workflows=(workflow,),
    )


def test_execution_metric_canonical_dict_preserves_boundary():
    metric = AfriTPPSExecutionMetric(
        metric_type="throughput",
        value=12,
        unit="items/hour",
        label="Throughput",
    )

    data = metric.canonical_dict()

    assert data["component"] == "AfriTPPS"
    assert data["pillar"] == "EXECUTION"
    assert data["classification"] == "EXECUTION_METRIC"
    assert data["label"] == "Throughput"
    assert data["defines_execution"] is True
    assert data["creates_governance_authority"] is False
    assert data["mutates_proof"] is False


def test_execution_metric_rejects_invalid_type():
    with pytest.raises(AfriTPPSMetricError):
        AfriTPPSExecutionMetric(
            metric_type="invalid",
            value=1,
            unit="count",
        )


def test_calculate_readiness_score():
    program = _program()

    assert calculate_readiness_score(program.capabilities) == 70.0


def test_calculate_readiness_score_rejects_empty_input():
    with pytest.raises(AfriTPPSMetricError):
        calculate_readiness_score(tuple())


def test_build_program_metric_bundle():
    bundle = build_program_metric_bundle(_program())
    data = bundle.canonical_dict()
    values = {
        metric["metric_type"]: metric["value"]
        for metric in data["metrics"]
    }

    assert data["metric_count"] == 3
    assert values["capability_count"] == 2
    assert values["workflow_count"] == 1
    assert values["readiness_score"] == 70.0


def test_build_program_metric_bundle_rejects_wrong_type():
    with pytest.raises(AfriTPPSMetricError):
        build_program_metric_bundle("bad")  # type: ignore[arg-type]
