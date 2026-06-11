from __future__ import annotations

from afritech.afriprogramming.services import (
    build_engineering_plan_from_mappings,
    build_engineering_platform,
    build_pr_intelligence_summary,
)
from afritech.afriprogramming.integration import (
    build_afriprog_boundary_profile,
    build_afriprog_to_afriprogramming_view,
)
from afritech.extensions.afriprog.copilot_assist import generate_context_aware_proposal


def _task():
    return {
        "id": "task.ga",
        "intent": "Build engineering platform",
        "lifecycle_stage": "build",
        "required_capabilities": (
            "code_generation",
            "test_generation",
            "security_validation",
            "pr_explanation",
            "verification_receipts",
        ),
        "evidence_refs": ("claim.ga",),
    }


def _agents():
    return (
        {
            "id": "agent.backend",
            "name": "Backend Agent",
            "role": "backend",
            "capabilities": ("code_generation", "pr_explanation"),
        },
        {
            "id": "agent.test",
            "name": "Testing Agent",
            "role": "testing",
            "capabilities": ("test_generation", "verification_receipts"),
        },
        {
            "id": "agent.security",
            "name": "Security Agent",
            "role": "security",
            "capabilities": ("security_validation",),
        },
    )


def _artifacts():
    return (
        {
            "id": "artifact.code",
            "artifact_type": "CODE",
            "title": "Generated code",
            "source_task_id": "task.ga",
            "trace_refs": ("claim.ga",),
        },
        {
            "id": "artifact.validation",
            "artifact_type": "VERIFICATION_RECEIPT",
            "title": "Verification receipt",
            "source_task_id": "task.ga",
            "trace_refs": ("claim.ga",),
        },
        {
            "id": "artifact.pr",
            "artifact_type": "PR_EXPLANATION",
            "title": "PR explanation",
            "source_task_id": "task.ga",
            "trace_refs": ("claim.ga",),
        },
    )


def test_build_engineering_plan_from_mappings():
    plan = build_engineering_plan_from_mappings(
        plan_id="plan.ga",
        task=_task(),
        agents=_agents(),
        artifacts=_artifacts(),
    )

    assert plan.plan_id == "plan.ga"
    assert plan.task.task_id == "task.ga"
    assert len(plan.agents) == 3
    assert len(plan.artifacts) == 3


def test_pr_intelligence_summary_is_merge_recommendation_ready():
    plan = build_engineering_plan_from_mappings(
        plan_id="plan.ga",
        task=_task(),
        agents=_agents(),
        artifacts=_artifacts(),
    )

    summary = build_pr_intelligence_summary(plan)

    assert summary["component"] == "AfriProgramming"
    assert summary["pillar"] == "ENGINEERING"
    assert summary["explainable_engineering"] is True
    assert summary["test_evidence"] is True
    assert summary["security_review"] is True
    assert summary["merge_recommendation_ready"] is True
    assert summary["creates_governance_authority"] is False


def test_build_engineering_platform_is_ga_elite_view():
    plan = build_engineering_plan_from_mappings(
        plan_id="plan.ga",
        task=_task(),
        agents=_agents(),
        artifacts=_artifacts(),
    )

    platform = build_engineering_platform(plan)

    assert platform["component"] == "AfriProgramming"
    assert platform["pillar"] == "ENGINEERING"
    assert platform["status"] == "GA_ELITE_AUTONOMOUS_ENGINEERING_PLATFORM"
    assert platform["question_answered"] == "How do we build it?"
    assert len(platform["feature_groups"]) == 17
    assert platform["engineers_systems"] is True
    assert platform["proof_aware"] is True
    assert platform["creates_governance_authority"] is False
    assert platform["creates_proof_authority"] is False
    assert platform["creates_replay_authority"] is False
    assert platform["mutates_proof"] is False


def test_afriprog_boundary_profile_keeps_productivity_and_governance_separate():
    profile = build_afriprog_boundary_profile()

    assert profile.source_layer == "AfriProg"
    assert profile.target_layer == "AfriProgramming"
    assert profile.handoff_mode == "proposal_only"
    assert profile.truth_authority_transferred is False


def test_afriprog_proposals_integrate_only_through_governed_handoff():
    proposal = generate_context_aware_proposal(
        intent="prepare governed driver route proposal",
        affected_files=("afritech/api/driver_routes.py",),
    )

    view = build_afriprog_to_afriprogramming_view(proposal)

    assert view["source_is_productivity_only"] is True
    assert view["target_is_governed_execution"] is True
    assert view["authority_boundary_preserved"] is True
    assert view["integration_record"]["source_validation_status"] == "ready_for_governance"
    assert view["integration_record"]["target_validation_status"] == "pass"
    assert view["integration_record"]["activation_allowed"] is False
