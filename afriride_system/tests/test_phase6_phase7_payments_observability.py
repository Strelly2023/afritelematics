from fastapi.testclient import TestClient

from afriride_system.api.auth import JWT
from afriride_system.api.dispatcher_adapter import reset_gateway
from afriride_system.api.main import app


def auth(role: str, actor: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {JWT.create_token(actor, role)}"}


def test_provider_neutral_charge_split_wallet_refund_and_reporting() -> None:
    reset_gateway()
    client = TestClient(app)
    operator = auth("OPERATOR", "ops-pay")
    rider = auth("CUSTOMER", "rider-pay")
    promo = client.post(
        "/v1/payments/promotions",
        json={"code": "LAUNCH10", "credit_minor": 1000, "currency": "AUD", "uses": 2},
        headers=operator,
    )
    assert promo.status_code == 200
    payload = {
        "payer_id": "rider-pay",
        "ride_id": "ride-pay",
        "driver_id": "driver-pay",
        "amount_minor": 10000,
        "currency": "AUD",
        "method": "card",
        "provider": "stripe",
        "promotion_code": "LAUNCH10",
    }
    charge = client.post(
        "/v1/payments/charges", json=payload,
        headers={"Idempotency-Key": "charge-1", **rider},
    )
    assert charge.status_code == 200
    body = charge.json()
    assert body["amount_minor"] == 9000
    assert body["split"] == {
        "driver_minor": 6300,
        "commission_minor": 1800,
        "tax_minor": 900,
        "promotion_minor": 1000,
    }
    replay = client.post(
        "/v1/payments/charges", json=payload,
        headers={"Idempotency-Key": "charge-1", **rider},
    )
    assert replay.json()["transaction_id"] == body["transaction_id"]
    wallet = client.get(
        "/v1/payments/wallets/driver/driver-pay/AUD", headers=auth("DRIVER", "driver-pay")
    )
    assert wallet.json()["balance_minor"] == 6300
    refund = client.post(
        f"/v1/payments/transactions/{body['transaction_id']}/refunds",
        json={"amount_minor": 2000}, headers=operator,
    )
    assert refund.json()["status"] == "partially_refunded"
    report = client.get("/v1/payments/reporting", headers=operator)
    assert report.json()["commission_minor"] == 1800


def test_cash_flutterwave_payout_and_dispute_contracts() -> None:
    reset_gateway()
    client = TestClient(app)
    operator = auth("OPERATOR", "ops-pay")
    charge = client.post(
        "/v1/payments/charges",
        json={
            "payer_id": "rider-2", "amount_minor": 5000, "currency": "USD",
            "method": "regional", "provider": "flutterwave",
        },
        headers={"Idempotency-Key": "regional-1", **auth("CUSTOMER", "rider-2")},
    )
    assert charge.json()["provider_reference"].startswith("flutterwave:")
    dispute = client.post(
        f"/v1/payments/transactions/{charge.json()['transaction_id']}/disputes",
        json={"opened_by": "rider-2", "reason": "fare questioned"},
        headers=auth("CUSTOMER", "rider-2"),
    )
    assert dispute.json()["status"] == "open"
    payout = client.post(
        "/v1/payments/payouts",
        json={"driver_id": "driver-2", "amount_minor": 3000, "currency": "USD",
              "scheduled_for": "2026-07-04T10:00:00Z"},
        headers=operator,
    )
    assert payout.json()["status"] == "scheduled"


def test_enterprise_observability_dashboard_is_protected_and_complete() -> None:
    reset_gateway()
    client = TestClient(app)
    assert client.get("/v1/operations/observability").status_code == 401
    client.get("/health")
    response = client.get(
        "/v1/operations/observability", headers=auth("OPERATOR", "ops-observe")
    )
    assert response.status_code == 200
    assert set(response.json()) >= {
        "fleet_health", "dispatch_latency", "queue_depth", "notification_delivery",
        "gps_quality", "api_latency", "payment_health", "trust_metrics",
    }
    readiness = client.get(
        "/v1/operations/launch-readiness", headers=auth("OPERATOR", "ops-observe")
    )
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "blocked"
    assert "android_production_signing" in readiness.json()["blocking"]
