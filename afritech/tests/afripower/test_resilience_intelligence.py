from __future__ import annotations

from importlib import import_module

import pytest

from afritech.afripower.resilience_intelligence import (
    assess_node_health,
    suggest_quorum_posture,
)

record_node_signal = import_module("afritech.federation.resilience").record_node_signal


@pytest.mark.django_db
def test_node_health_assessment_is_advisory_only():
    record_node_signal(node_id="node-watch", replay_failure=True, reason="minority divergence")

    assessment = assess_node_health("node-watch")

    assert assessment.node_id == "node-watch"
    assert assessment.advisory_only is True
    assert assessment.execution_authority is False
    assert assessment.recommendation in {
        "standard_verification",
        "increase_verification_requirements",
        "isolate_until_replay_correctness_proven",
    }


def test_quorum_posture_can_heighten_but_not_execute():
    posture = suggest_quorum_posture(total_nodes=5, unstable_nodes=1)

    assert posture["base_quorum"] == 3
    assert posture["suggested_quorum"] == 4
    assert posture["advisory_only"] is True
    assert posture["execution_authority"] is False
