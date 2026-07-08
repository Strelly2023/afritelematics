from __future__ import annotations

import pytest

from afriride_system.pilot.controlled_pilot import controlled_pilot_payment_guard
from tests.controlled_pilot._helpers import read_text


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_security]


def test_controlled_pilot_reconciliation_policy_is_documented_and_guarded() -> None:
    doc = read_text("docs/pilot/CONTROLLED_PILOT_RECONCILIATION.md")
    assert "opening float is recorded" in doc
    assert "end-of-day reconciliation is mandatory" in doc
    assert "shortages and overages are flagged" in doc
    controlled_pilot_payment_guard(provider="cash", method="cash")

