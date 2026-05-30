"""AfriProgramming GA Elite engineering services."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from afritech.afriprogramming.constants import (
    AFRIPROGRAMMING_COMPONENT,
    AFRIPROGRAMMING_PILLAR,
    AFRIPROGRAMMING_STATUS,
    FEATURE_GROUPS,
    OUTPUTS,
    QUESTION_ANSWERED,
    constitutional_afriprogramming_metadata,
)
from afritech.afriprogramming.models import (
    AfriProgrammingAgent,
    AfriProgrammingArtifact,
    AfriProgrammingEngineeringPlan,
    AfriProgrammingTask,
)


def build_engineering_plan_from_mappings(
    plan_id: str,
    task: Mapping[str, object],
    agents: Iterable[Mapping[str, object]],
    artifacts: Iterable[Mapping[str, object]],
) -> AfriProgrammingEngineeringPlan:
    return AfriProgrammingEngineeringPlan(
        plan_id=plan_id,
        task=AfriProgrammingTask.from_mapping(task),
        agents=tuple(AfriProgrammingAgent.from_mapping(payload) for payload in agents),
        artifacts=tuple(
            AfriProgrammingArtifact.from_mapping(payload) for payload in artifacts
        ),
    )


def build_pr_intelligence_summary(
    plan: AfriProgrammingEngineeringPlan,
) -> dict[str, object]:
    artifact_types = tuple(artifact.artifact_type for artifact in plan.artifacts)
    agent_roles = tuple(agent.role for agent in plan.agents)

    return {
        "component": AFRIPROGRAMMING_COMPONENT,
        "pillar": AFRIPROGRAMMING_PILLAR,
        "plan_id": plan.plan_id,
        "task_id": plan.task.task_id,
        "agent_roles": agent_roles,
        "artifact_types": artifact_types,
        "explainable_engineering": "PR_EXPLANATION" in artifact_types,
        "test_evidence": any(
            artifact_type in {"TEST", "VALIDATION", "VERIFICATION_RECEIPT"}
            for artifact_type in artifact_types
        ),
        "security_review": "security" in agent_roles,
        "merge_recommendation_ready": "PR_EXPLANATION" in artifact_types
        and any(
            artifact_type in {"VALIDATION", "VERIFICATION_RECEIPT"}
            for artifact_type in artifact_types
        ),
        "creates_governance_authority": False,
        "creates_proof_authority": False,
        "creates_replay_authority": False,
        "mutates_proof": False,
    }


def build_engineering_platform(
    plan: AfriProgrammingEngineeringPlan,
) -> dict[str, object]:
    pr_summary = build_pr_intelligence_summary(plan)

    return {
        "component": AFRIPROGRAMMING_COMPONENT,
        "pillar": AFRIPROGRAMMING_PILLAR,
        "status": AFRIPROGRAMMING_STATUS,
        "question_answered": QUESTION_ANSWERED,
        "feature_groups": FEATURE_GROUPS,
        "outputs": OUTPUTS,
        "constitution": constitutional_afriprogramming_metadata(),
        "engineering_plan": plan.canonical_dict(),
        "pull_request_intelligence": pr_summary,
        "engineers_systems": True,
        "proof_aware": plan.canonical_dict()["proof_aware"],
        "creates_governance_authority": False,
        "creates_proof_authority": False,
        "creates_replay_authority": False,
        "mutates_proof": False,
    }


__all__ = [
    "build_engineering_plan_from_mappings",
    "build_engineering_platform",
    "build_pr_intelligence_summary",
]
