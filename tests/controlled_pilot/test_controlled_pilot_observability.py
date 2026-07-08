from __future__ import annotations

import pytest

from afriride_system.pilot.controlled_pilot import audit_log, record_event
from tests.controlled_pilot._helpers import read_text


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_security]


def test_pilot_events_are_logged_with_required_fields() -> None:
    start = len(audit_log())
    record_event(actor="rider-001", role="CUSTOMER", device="device-011", action="trip_requested", result="ok")
    record_event(actor="rider-001", role="CUSTOMER", device="device-011", action="payment_guard", result="simulated")
    events = audit_log()[start:]
    assert len(events) >= 2
    for event in events:
        for key in ["timestamp", "actor", "role", "device", "action", "result", "environment"]:
            assert key in event
        assert event["environment"] == "CONTROLLED_PILOT"

    doc = read_text("docs/pilot/CONTROLLED_PILOT_OPERATIONS_RUNBOOK.md")
    assert "Monitoring" in doc
    assert "support" in doc.lower()
