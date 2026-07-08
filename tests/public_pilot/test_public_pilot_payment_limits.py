from __future__ import annotations

import json

import pytest

from afriride_system.pilot import public_pilot
from afriride_system.pilot.public_pilot import PublicPilotError, mark_public_pilot_payment, public_pilot_payment_allowed, public_pilot_payment_guard
from tests.public_pilot._helpers import PUBLIC_PILOT_APPROVAL_PATH, public_pilot_approval_payload, read_json


pytestmark = [pytest.mark.public_pilot, pytest.mark.pilot_real_limited, pytest.mark.public_pilot_payments]


def _install_approval(monkeypatch: pytest.MonkeyPatch, tmp_path, **overrides) -> None:
    payload = public_pilot_approval_payload(**overrides)
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_payment_mode_and_limits_are_enforced(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    assert read_json("config/public_pilot.json")["payment_mode"] == "PILOT_REAL"
    assert public_pilot_payment_allowed() is True
    public_pilot_payment_guard(provider="wallet", method="wallet", amount_aud=50, region="Melbourne")
    with pytest.raises(PublicPilotError):
        public_pilot_payment_guard(provider="wallet", method="wallet", amount_aud=51, region="Melbourne")


def test_public_pilot_live_provider_requires_explicit_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path, public_pilot_live_payment_approved=False, limited_real_payments_approved=True)
    assert public_pilot_payment_allowed() is True
    with pytest.raises(PublicPilotError):
        public_pilot_payment_guard(provider="live_stripe", method="card", amount_aud=10, region="Melbourne")


def test_public_pilot_payment_payload_is_marked_public_pilot(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    payload = mark_public_pilot_payment({"transaction_id": "pp-001", "status": "captured"})
    assert payload["public_pilot"] is True
    assert payload["simulated_payment"] is False
    assert payload["public_pilot_environment"]["environment"] == "PUBLIC_PILOT"
