from __future__ import annotations

from afritech.pilot.activation import AfriRidePilotSignals, evaluate_afriride_pilot


def test_pilot_activation_is_blocked_without_real_evidence():
    decision = evaluate_afriride_pilot()

    assert decision.authorized is False
    assert decision.status == "READY_BLOCKED"
    assert "real trips completed" in decision.missing_evidence
    assert decision.allowed_next_action == "collect real-world pilot evidence only"


def test_pilot_activation_can_become_ready_but_not_economic():
    decision = evaluate_afriride_pilot(
        AfriRidePilotSignals(
            real_drivers_onboarded=True,
            real_trips_completed=True,
            raw_transaction_evidence_collected=True,
            trust_kernel_events_recorded=True,
            replay_verified=True,
            operator_review_complete=True,
            economic_activation_requested=False,
        )
    )

    assert decision.authorized is True
    assert decision.status == "READY_FOR_CONTROLLED_FIELD_EXECUTION"


def test_pilot_activation_blocks_economic_activation_request():
    decision = evaluate_afriride_pilot(
        AfriRidePilotSignals(
            real_drivers_onboarded=True,
            real_trips_completed=True,
            raw_transaction_evidence_collected=True,
            trust_kernel_events_recorded=True,
            replay_verified=True,
            operator_review_complete=True,
            economic_activation_requested=True,
        )
    )

    assert decision.authorized is False
    assert decision.forbidden_actions == ("economic activation",)
