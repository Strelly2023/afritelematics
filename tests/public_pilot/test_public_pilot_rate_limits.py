from __future__ import annotations

import json

import pytest

from afriride_system.pilot import public_pilot
from afriride_system.pilot.public_pilot import PublicPilotError, public_pilot_payment_guard
from tests.public_pilot._helpers import public_pilot_approval_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.pilot_real_limited, pytest.mark.public_pilot_payments]


def _install_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    path.write_text(json.dumps(public_pilot_approval_payload(), indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_transaction_limits_are_enforced(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    public_pilot_payment_guard(provider="wallet", method="wallet", amount_aud=50, region="Melbourne")
    with pytest.raises(PublicPilotError):
        public_pilot_payment_guard(provider="wallet", method="wallet", amount_aud=51, region="Melbourne")
    with pytest.raises(PublicPilotError):
        public_pilot_payment_guard(provider="wallet", method="wallet", amount_aud=1, region="Sydney")
