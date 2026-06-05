from __future__ import annotations

from afritech.afripower.predictive_orchestration import (
    detect_anomalies,
    explain_suggestion,
    learn_patterns,
    score_risk,
    suggest_orchestration,
)


def test_predictive_orchestration_suggests_but_does_not_execute():
    recommendation = suggest_orchestration(
        {
            "last_event": "TripCompleted",
            "actor_id": "driver:D001",
            "driver_id": "D001",
            "ride_id": "ride:001",
            "expected_next_steps": ("work_completed", "health_check"),
            "observed_steps": ("work_completed",),
        }
    )

    assert recommendation.advisory_only is True
    assert recommendation.execution_authority is False
    assert recommendation.intent.operations[0].domain == "AfriTalent"
    assert recommendation.intent.operations[1].domain == "AfriHealth"
    assert recommendation.anomalies == ("missing_expected_step:health_check",)
    assert recommendation.canonical_dict()["execution_authority"] is False


def test_predictive_orchestration_noop_for_unknown_context():
    recommendation = suggest_orchestration({"last_event": "Unknown"})

    assert recommendation.intent.orchestration_id == "suggestion.noop"
    assert recommendation.ranked_options[0].name == "no_action"


def test_detect_anomalies_is_read_only_projection():
    assert detect_anomalies(
        {
            "expected_next_steps": ("a", "b"),
            "observed_steps": ("a",),
        }
    ) == ("missing_expected_step:b",)


def test_afripower_v2_learns_scores_and_explains_without_authority():
    recommendation = suggest_orchestration(
        {
            "last_event": "TripCompleted",
            "actor_id": "driver:D001",
            "driver_id": "D001",
            "ride_id": "ride:002",
        }
    )
    patterns = learn_patterns(
        (
            {"event_type": "TripCompleted", "status": "verified"},
            {"event_type": "WorkCompleted", "status": "verified"},
            {"event_type": "HealthCheckTriggered", "status": "failed"},
        )
    )
    risk = score_risk(recommendation.intent)
    explanation = explain_suggestion(recommendation.intent)

    assert patterns.common_flows == (
        "TripCompleted->WorkCompleted",
        "WorkCompleted->HealthCheckTriggered",
    )
    assert patterns.failure_points == ("HealthCheckTriggered",)
    assert risk.execution_authority is False
    assert "Execution remains AfriTPPS-controlled" in explanation
