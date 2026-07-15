from __future__ import annotations

import dataclasses

import pytest

from afritech.novaride_runtime.common.errors import AuthorityDenied
from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.events.replay import rebuild_projection
from afritech.novaride_runtime.events.replay_planner import ReplayMode, plan_replay
from afritech.novaride_runtime.events.replay_side_effect_guard import ReplayExecutionContext
from afritech.novaride_runtime.events.replay_verifier import verify_replay


def _event(version: int = 1) -> MobilityEvent:
    return MobilityEvent(
        event_type="BookingCreated",
        aggregate_id="booking_1",
        aggregate_type="Booking",
        aggregate_version=version,
        tenant_id="tenant",
        region="AU",
        actor_type="SYSTEM",
        actor_id="system",
        correlation_id="corr_replay",
        causation_id=None,
        payload={"booking_id": "booking_1"},
    )


def test_deterministic_replay_matches_and_projection_rebuilds() -> None:
    events = [_event(1)]
    plan = plan_replay(mode=ReplayMode.AGGREGATE, scope={"aggregate_id": "booking_1"}, operator_id="operator", reason="verify")
    result = verify_replay(replay_id=plan.replay_id, events=events)
    projection = rebuild_projection(events)

    assert result.matched is True
    assert result.source_state_hash == result.replay_state_hash
    assert result.source_event_count == 1
    assert projection.event_count == 1


def test_event_hash_tampering_is_quarantined() -> None:
    event = _event(1)
    tampered = dataclasses.replace(event, integrity_hash="sha256:tampered")
    result = verify_replay(replay_id="replay_tamper", events=[tampered])

    assert result.matched is False
    assert result.quarantined_events == (event.event_id,)


def test_replay_side_effects_blocked() -> None:
    replay_context = ReplayExecutionContext()
    with pytest.raises(AuthorityDenied):
        replay_context.assert_allowed("novapay_execution")
    with pytest.raises(AuthorityDenied):
        replay_context.assert_allowed("driver_dispatch")
