from __future__ import annotations

import pytest

from afriride_system.pilot.controlled_pilot import controlled_pilot_payment_guard, mark_controlled_pilot_payment
from tests.controlled_pilot._helpers import read_text


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.simulated_payment]


def test_cash_procedure_is_documented_and_ledger_is_simulated() -> None:
    doc = read_text("docs/pilot/CONTROLLED_PILOT_PAYMENT_BOUNDARIES.md")
    assert "Cash only through the documented pilot cash procedure" in doc
    assert "Real payments are allowed only" in doc

    controlled_pilot_payment_guard(provider="cash", method="cash")
    payload = mark_controlled_pilot_payment({"transaction_id": "cash-procedure-1", "status": "captured"})
    assert payload["simulated_payment"] is True
    assert payload["controlled_pilot"] is True
