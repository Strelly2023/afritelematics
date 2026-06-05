"""Read-only resilience intelligence for AfriPower."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from afritech.afripower.contracts.read_only_contract import assert_read_only_contract
from afritech.models import NodeReputation


@dataclass(frozen=True)
class NodeHealthAssessment:
    node_id: str
    health_score: float
    voting_weight: float
    isolated: bool
    recommendation: str
    advisory_only: bool = True
    execution_authority: bool = False


def assess_node_health(node_id: str) -> NodeHealthAssessment:
    assert_read_only_contract()
    node_health_score = import_module("afritech.federation.resilience").node_health_score
    reputation = NodeReputation.objects.get(node_id=node_id)
    health_score = node_health_score(reputation)
    if reputation.is_isolated:
        recommendation = "isolate_until_replay_correctness_proven"
    elif health_score < 0.7:
        recommendation = "increase_verification_requirements"
    else:
        recommendation = "standard_verification"
    return NodeHealthAssessment(
        node_id=node_id,
        health_score=health_score,
        voting_weight=reputation.voting_weight,
        isolated=reputation.is_isolated,
        recommendation=recommendation,
    )


def suggest_quorum_posture(*, total_nodes: int, unstable_nodes: int) -> dict[str, object]:
    assert_read_only_contract()
    base_quorum = (total_nodes // 2) + 1 if total_nodes > 0 else 1
    heightened_quorum = min(total_nodes, base_quorum + 1) if unstable_nodes else base_quorum
    return {
        "base_quorum": base_quorum,
        "suggested_quorum": heightened_quorum,
        "reason": "consensus_instability" if unstable_nodes else "standard_majority",
        "advisory_only": True,
        "execution_authority": False,
    }
