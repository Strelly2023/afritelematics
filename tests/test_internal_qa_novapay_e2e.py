from __future__ import annotations

import pytest

from afriride_system.backend.storage import AfriRideStorage
from afriride_system.payments.modern import PaymentRepository, PaymentService, ReferenceProvider
from tests.internal_qa._helpers import BUTTON_REGISTRY_PATH, read_json, read_text
from tests.private_dev._helpers import assert_contains_all


pytestmark = [
    pytest.mark.internal_qa,
    pytest.mark.qa_mobile,
    pytest.mark.novapay,
    pytest.mark.consumer,
    pytest.mark.agent,
    pytest.mark.merchant,
    pytest.mark.business,
]


def test_novapay_internal_qa_app_surfaces_are_documented() -> None:
    registry = read_json(BUTTON_REGISTRY_PATH)["apps"]
    consumer = read_text("novapay_consumer_app/src/appConfig.ts")
    agent = read_text("novapay_agent_app/src/agentApp.tsx")
    merchant = read_text("novapay_merchant_app/src/appConfig.ts")
    business = read_text("novapay_business_app/src/appConfig.ts")

    assert_contains_all(consumer, registry["novapay_consumer"]["tabs"], context="NovaPay consumer tabs")
    assert_contains_all(consumer, registry["novapay_consumer"]["buttons"], context="NovaPay consumer buttons")
    assert_contains_all(agent, registry["novapay_agent"]["tabs"], context="NovaPay agent tabs")
    assert_contains_all(agent, registry["novapay_agent"]["buttons"], context="NovaPay agent buttons")
    assert_contains_all(merchant, registry["novapay_merchant"]["tabs"], context="NovaPay merchant tabs")
    assert_contains_all(merchant, registry["novapay_merchant"]["buttons"], context="NovaPay merchant buttons")
    assert_contains_all(business, registry["novapay_business"]["tabs"], context="NovaPay business tabs")
    assert_contains_all(business, registry["novapay_business"]["buttons"], context="NovaPay business buttons")


def test_novapay_internal_qa_simulated_payments_and_reconciliation(tmp_path) -> None:
    storage = AfriRideStorage(tmp_path / "internal-qa-novapay.sqlite3")
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
        idempotency_key="qa-wallet-transfer",
        payer_id="consumer-1",
        amount_minor=5000,
        currency="AUD",
        method="wallet",
        provider="wallet",
        ride_id=None,
        driver_id=None,
    )
    assert charge["simulated_payment"] is True
    assert charge["status"] == "captured"

    refund = service.refund(charge["transaction_id"], 500)
    assert refund["simulated_payment"] is True
    assert refund["status"] in {"refunded", "partially_refunded"}

    summary = repository.health()
    assert "captured" in summary["transactions"] or "partially_refunded" in summary["transactions"]
