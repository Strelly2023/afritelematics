from __future__ import annotations

from tempfile import TemporaryDirectory

import pytest

from afriride_system.backend.storage import AfriRideStorage
from afriride_system.payments.modern import PaymentRepository, PaymentService, ReferenceProvider
from afriride_system.payments.private_development import (
    PrivateDevelopmentPaymentError,
    guard_payment_boundary,
    load_private_development_config,
    mark_simulated_payment,
)


pytestmark = [pytest.mark.private_dev, pytest.mark.simulated_payment, pytest.mark.no_live_charge]


def test_private_development_flags_block_live_payment_modes() -> None:
    config = load_private_development_config()
    assert config.environment == "PRIVATE_DEVELOPMENT"
    assert not config.live_payments_enabled
    assert not config.real_charging_enabled
    assert not config.external_payouts_enabled
    assert not config.production_credentials_allowed


def test_live_charge_attempt_is_blocked() -> None:
    with pytest.raises(PrivateDevelopmentPaymentError):
        guard_payment_boundary(
            provider="live_stripe",
            method="card",
            live_charge=True,
        )


def test_production_credentials_are_rejected_in_private_development() -> None:
    with pytest.raises(PrivateDevelopmentPaymentError):
        guard_payment_boundary(
            provider="bank_transfer",
            method="card",
            production_credentials_present=True,
        )


def test_simulated_payment_response_is_marked() -> None:
    payload = mark_simulated_payment({"transaction_id": "tx-1", "status": "captured"})
    assert payload["simulated_payment"] is True
    assert payload["payment_mode"] == "SIMULATED"
    assert payload["private_development"]["environment"] == "PRIVATE_DEVELOPMENT"


def test_simulated_charge_and_refund_work_without_live_network_charge() -> None:
    with TemporaryDirectory() as temp_dir:
        storage = AfriRideStorage(f"{temp_dir}/private-dev.sqlite3")
        service = PaymentService(
            PaymentRepository(storage),
            {"wallet": ReferenceProvider("wallet")},
        )
        charge = service.charge(
            idempotency_key="pd-charge-1",
            payer_id="customer-1",
            amount_minor=25000,
            currency="AUD",
            method="wallet",
            provider="wallet",
            ride_id=None,
            driver_id=None,
        )
        assert charge["simulated_payment"] is True
        assert charge["payment_mode"] == "SIMULATED"
        assert charge["status"] == "captured"
        assert charge["provider_reference"].startswith("wallet:charge:")

        refund = service.refund(charge["transaction_id"], 5000)
        assert refund["simulated_payment"] is True
        assert refund["status"] in {"partially_refunded", "refunded"}
        assert refund["provider_reference"].startswith("wallet:refund:")

