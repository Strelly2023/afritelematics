from __future__ import annotations

import json

import pytest

from afriride_system.pilot import public_pilot
from afriride_system.pilot.public_pilot import PublicPilotError, public_pilot_payment_guard, record_event, audit_log
from tests.public_pilot._helpers import public_pilot_approval_payload


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_compliance, pytest.mark.public_pilot_payments]


def _install_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    path.write_text(json.dumps(public_pilot_approval_payload(), indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()


def test_public_pilot_fraud_controls_block_over_limit_and_log(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    _install_approval(monkeypatch, tmp_path)
    with pytest.raises(PublicPilotError):
        public_pilot_payment_guard(provider="wallet", method="wallet", amount_aud=99, region="Melbourne")


def test_public_pilot_live_provider_blocked_without_explicit_approval(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    path = tmp_path / "PUBLIC_PILOT_APPROVAL.json"
    payload = public_pilot_approval_payload(public_pilot_live_payment_approved=False, limited_real_payments_approved=False)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    monkeypatch.setattr(public_pilot, "PUBLIC_PILOT_APPROVAL_PATH", path)
    public_pilot.load_public_pilot_approval.cache_clear()
    public_pilot.reset_runtime_state()
    with pytest.raises(PublicPilotError):
        public_pilot_payment_guard(provider="live_stripe", method="card", amount_aud=10, region="Melbourne")

    record_event(actor="public-consumer-1", role="CUSTOMER", device="public-device-consumer-1", action="fraud_check", result="flagged", region="Melbourne")
    log = audit_log()
    assert log
    assert log[-1]["environment"] == "PUBLIC_PILOT"
    assert "timestamp" in log[-1]
    assert log[-1]["actor"] == "public-consumer-1"
