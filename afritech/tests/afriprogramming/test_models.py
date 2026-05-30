from __future__ import annotations

import pytest

from afritech.afriprogramming.models import (
    AfriProgrammingAgent,
    AfriProgrammingArtifact,
    AfriProgrammingEngineeringPlan,
    AfriProgrammingModelError,
    AfriProgrammingTask,
)


def _task() -> AfriProgrammingTask:
    return AfriProgrammingTask(
        task_id="task.ga",
        intent="Build engineering platform",
        lifecycle_stage="build",
        required_capabilities=(
            "code_generation",
            "test_generation",
            "security_validation",
            "pr_explanation",
            "verification_receipts",
        ),
        evidence_refs=("claim.ga",),
    )


def _agents() -> tuple[AfriProgrammingAgent, ...]:
    return (
        AfriProgrammingAgent(
            agent_id="agent.security",
            name="Security Agent",
            role="security",
            capabilities=("security_validation",),
        ),
        AfriProgrammingAgent(
            agent_id="agent.backend",
            name="Backend Agent",
            role="backend",
            capabilities=("code_generation", "pr_explanation"),
            metadata=(("repo", "afritelematics"),),
        ),
        AfriProgrammingAgent(
            agent_id="agent.test",
            name="Test Agent",
            role="testing",
            capabilities=("test_generation", "verification_receipts"),
        ),
    )


def _artifacts() -> tuple[AfriProgrammingArtifact, ...]:
    return (
        AfriProgrammingArtifact(
            artifact_id="artifact.validation",
            artifact_type="VERIFICATION_RECEIPT",
            title="Verification receipt",
            source_task_id="task.ga",
            trace_refs=("claim.ga",),
        ),
        AfriProgrammingArtifact(
            artifact_id="artifact.code",
            artifact_type="CODE",
            title="Generated code",
            source_task_id="task.ga",
            trace_refs=("claim.ga",),
        ),
        AfriProgrammingArtifact(
            artifact_id="artifact.pr",
            artifact_type="PR_EXPLANATION",
            title="PR explanation",
            source_task_id="task.ga",
            trace_refs=("claim.ga",),
        ),
    )


def test_agent_canonical_dict_preserves_engineering_boundary():
    data = _agents()[1].canonical_dict()

    assert data["component"] == "AfriProgramming"
    assert data["pillar"] == "ENGINEERING"
    assert data["classification"] == "AUTONOMOUS_ENGINEERING_MODEL"
    assert data["role"] == "backend"
    assert data["metadata"] == {"repo": "afritelematics"}
    assert data["engineers_systems"] is True
    assert data["creates_governance_authority"] is False
    assert data["creates_proof_authority"] is False
    assert data["creates_replay_authority"] is False
    assert data["mutates_proof"] is False


def test_agent_from_mapping_normalizes_payload():
    agent = AfriProgrammingAgent.from_mapping(
        {
            "id": "agent.docs",
            "name": "Documentation Agent",
            "role": "documentation",
            "capabilities": ("documentation_generation", "engineering_explainability"),
            "metadata": {"team": "platform"},
        }
    )

    assert agent.agent_id == "agent.docs"
    assert agent.metadata_dict() == {"team": "platform"}


def test_agent_rejects_invalid_role():
    with pytest.raises(AfriProgrammingModelError):
        AfriProgrammingAgent(
            agent_id="agent.bad",
            name="Bad Agent",
            role="invalid",
            capabilities=("code_generation",),
        )


def test_task_tracks_claim_evidence_mapping():
    data = _task().canonical_dict()

    assert data["task_id"] == "task.ga"
    assert data["lifecycle_stage"] == "build"
    assert data["claim_evidence_mapping"] is True
    assert data["creates_governance_authority"] is False


def test_artifact_from_mapping_and_proof_awareness():
    artifact = AfriProgrammingArtifact.from_mapping(
        {
            "id": "artifact.witness",
            "artifact_type": "WITNESS",
            "title": "Build witness",
            "source_task_id": "task.ga",
            "trace_refs": ("claim.ga",),
        }
    )

    data = artifact.canonical_dict()
    assert data["classification"] == "ENGINEERING_ARTIFACT"
    assert data["proof_aware"] is True
    assert data["creates_proof_authority"] is False


def test_artifact_rejects_missing_trace_refs():
    with pytest.raises(AfriProgrammingModelError, match="trace_refs"):
        AfriProgrammingArtifact(
            artifact_id="artifact.bad",
            artifact_type="CODE",
            title="Bad artifact",
            source_task_id="task.ga",
            trace_refs=(),
        )


def test_plan_orders_agents_and_artifacts_deterministically():
    plan = AfriProgrammingEngineeringPlan(
        plan_id="plan.ga",
        task=_task(),
        agents=_agents(),
        artifacts=_artifacts(),
    )

    data = plan.canonical_dict()

    assert [agent.agent_id for agent in plan.agents] == [
        "agent.backend",
        "agent.security",
        "agent.test",
    ]
    assert data["agent_count"] == 3
    assert data["artifact_count"] == 3
    assert data["engineers_systems"] is True
    assert data["proof_aware"] is True
    assert data["creates_governance_authority"] is False


def test_plan_rejects_uncovered_task_capability():
    artifact = AfriProgrammingArtifact(
        artifact_id="artifact.bad",
        artifact_type="CODE",
        title="Bad artifact",
        source_task_id="task.bad",
        trace_refs=("claim.bad",),
    )

    with pytest.raises(AfriProgrammingModelError, match="not covered"):
        AfriProgrammingEngineeringPlan(
            plan_id="plan.bad",
            task=AfriProgrammingTask(
                task_id="task.bad",
                intent="Build",
                lifecycle_stage="build",
                required_capabilities=("architecture_validation",),
            ),
            agents=_agents(),
            artifacts=(artifact,),
        )
