from __future__ import annotations

import pytest

from afriride_system.backend.storage import AfriRideStorage
from afriride_system.payments.modern import PaymentRepository, PaymentService, ReferenceProvider
from afriride_system.payments.private_development import (
    PrivateDevelopmentPaymentError,
    guard_payment_boundary,
    load_private_development_config,
    mark_simulated_payment,
)
from tests.internal_qa._helpers import INTERNAL_QA_CONFIG_PATH, read_json


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_security, pytest.mark.simulated_payment, pytest.mark.no_live_charge]


def test_internal_qa_config_blocks_live_payment_modes() -> None:
    config = read_json(INTERNAL_QA_CONFIG_PATH)
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False
    assert config["production_credentials_allowed"] is False


def test_private_development_guard_blocks_live_charge_and_payouts() -> None:
    config = load_private_development_config()
    assert config.live_payments_enabled is False
    assert config.real_charging_enabled is False
    assert config.external_payouts_enabled is False

    with pytest.raises(PrivateDevelopmentPaymentError):
        guard_payment_boundary(provider="live_gateway", method="card", live_charge=True)
    with pytest.raises(PrivateDevelopmentPaymentError):
        guard_payment_boundary(provider="live_gateway", method="wallet", payout=True)


def test_simulated_payment_response_is_marked() -> None:
    payload = mark_simulated_payment({"transaction_id": "tx-internal-qa", "status": "captured"})
    assert payload["simulated_payment"] is True
    assert payload["payment_mode"] == "SIMULATED"
    assert payload["private_development"]["environment"] == "PRIVATE_DEVELOPMENT"


def test_simulated_payment_service_does_not_require_live_network(tmp_path) -> None:
    storage = AfriRideStorage(tmp_path / "internal-qa-payments.sqlite3")
    repository = PaymentRepository(storage)
    service = PaymentService(
        repository,
        {
            "cash": ReferenceProvider("cash"),
            "wallet": ReferenceProvider("wallet"),
            "stripe": ReferenceProvider("stripe"),
            "flutterwave": ReferenceProvider("flutterwave"),
        },
    )
    charge = service.charge(
        idempotency_key="internal-qa-1",
        payer_id="customer-1",
        amount_minor=1000,
        currency="AUD",
        method="wallet",
        provider="wallet",
        ride_id=None,
        driver_id=None,
    )
    assert charge["simulated_payment"] is True
    refund = service.refund(charge["transaction_id"], 250)
    assert refund["simulated_payment"] is True
