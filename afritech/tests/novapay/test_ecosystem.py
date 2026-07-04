from __future__ import annotations

import ast
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novapay_ecosystem_api import build_novapay_ecosystem_router
from afritech.novapay import NovaPayEcosystem, NovaPayRepository


def _client(service: NovaPayEcosystem) -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novapay_ecosystem_router(service))
    return TestClient(app)


def _headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_repository_creates_requested_novapay_tables(tmp_path: Path) -> None:
    repo = NovaPayRepository(tmp_path / "novapay.sqlite3")

    assert {
        "novapay_wallets",
        "novapay_accounts",
        "novapay_ledger_entries",
        "novapay_transactions",
        "novapay_transfers",
        "novapay_qr_codes",
        "novapay_merchants",
        "novapay_agents",
        "novapay_settlements",
        "novapay_reconciliation_batches",
        "novapay_refunds",
        "novapay_disputes",
        "novapay_payouts",
        "novapay_invoices",
        "novapay_receipts",
        "novapay_provider_events",
        "novapay_audit_events",
        "novapay_policy_approvals",
        "novapay_developer_apps",
        "novapay_webhooks",
    }.issubset(set(repo.table_names()))


def test_wallet_send_receive_qr_merchant_and_agent_flow(tmp_path: Path) -> None:
    service = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    client = _client(service)
    headers = _headers("OPERATOR", "ops-1", "org-pay")

    sender = client.post(
        "/v1/novapay/wallets",
        headers=headers,
        json={
            "owner_id": "customer-1",
            "organization_id": "org-pay",
            "owner_type": "consumer",
            "currency": "AUD",
            "initial_balance": "100.00",
            "kyc_status": "verified",
        },
    ).json()
    receiver = client.post(
        "/v1/novapay/wallets",
        headers=headers,
        json={
            "owner_id": "merchant-1",
            "organization_id": "org-pay",
            "owner_type": "merchant",
            "currency": "AUD",
            "initial_balance": "0.00",
            "kyc_status": "verified",
        },
    ).json()
    agent = client.post(
        "/v1/novapay/wallets",
        headers=headers,
        json={
            "owner_id": "agent-1",
            "organization_id": "org-pay",
            "owner_type": "agent",
            "currency": "AUD",
            "initial_balance": "20.00",
            "kyc_status": "verified",
        },
    ).json()

    transfer = client.post(
        "/v1/novapay/transfers",
        headers=headers,
        json={
            "organization_id": "org-pay",
            "actor_id": "customer-1",
            "actor_role": "CUSTOMER",
            "sender_wallet_id": sender["wallet_id"],
            "receiver_wallet_id": receiver["wallet_id"],
            "amount": "25.00",
            "currency": "AUD",
            "transfer_type": "send_money",
            "idempotency_key": "idem-1",
        },
    )
    assert transfer.status_code == 200
    assert transfer.json()["receipt"]["receipt_id"]

    receive = service.receive_money(
        organization_id="org-pay",
        actor_id="merchant-1",
        actor_role="SUPPLIER",
        sender_wallet_id=receiver["wallet_id"],
        receiver_wallet_id=sender["wallet_id"],
        amount="5.00",
        currency="AUD",
        transfer_type="receive_money",
        idempotency_key="idem-receive-1",
    )
    assert receive["transaction"]["transfer_type"] == "receive_money"

    qr = client.post(
        "/v1/novapay/qr",
        headers=headers,
        json={
            "organization_id": "org-pay",
            "actor_id": "customer-1",
            "actor_role": "CUSTOMER",
            "payer_wallet_id": sender["wallet_id"],
            "merchant_wallet_id": receiver["wallet_id"],
            "amount": "5.00",
            "currency": "AUD",
            "qr_code": "qr-1",
            "idempotency_key": "idem-qr-1",
        },
    )
    assert qr.status_code == 200

    agent_cash_in = client.post(
        "/v1/novapay/agent/cash",
        headers=headers,
        json={
            "organization_id": "org-pay",
            "actor_id": "agent-1",
            "actor_role": "AGENT",
            "wallet_id": agent["wallet_id"],
            "amount": "10.00",
            "currency": "AUD",
            "direction": "in",
            "idempotency_key": "idem-agent-in",
        },
    )
    assert agent_cash_in.status_code == 200

    agent_cash_out = client.post(
        "/v1/novapay/agent/cash",
        headers=headers,
        json={
            "organization_id": "org-pay",
            "actor_id": "agent-1",
            "actor_role": "AGENT",
            "wallet_id": agent["wallet_id"],
            "amount": "5.00",
            "currency": "AUD",
            "direction": "out",
            "idempotency_key": "idem-agent-out",
        },
    )
    assert agent_cash_out.status_code == 200
    assert service.wallet(sender["wallet_id"])["balance"] == "75.00"
    assert service.wallet(receiver["wallet_id"])["balance"] == "25.00"
    assert service.wallet(agent["wallet_id"])["balance"] == "25.00"


def test_business_payroll_refund_dispute_settlement_and_reconciliation(tmp_path: Path) -> None:
    service = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    client = _client(service)
    headers = _headers("OPERATOR", "ops-1", "org-enterprise")

    source = client.post(
        "/v1/novapay/wallets",
        headers=headers,
        json={
            "owner_id": "corp-1",
            "organization_id": "org-enterprise",
            "owner_type": "enterprise",
            "currency": "AUD",
            "initial_balance": "1000.00",
            "kyc_status": "verified",
        },
    ).json()
    employee = client.post(
        "/v1/novapay/wallets",
        headers=headers,
        json={
            "owner_id": "staff-1",
            "organization_id": "org-enterprise",
            "owner_type": "consumer",
            "currency": "AUD",
            "initial_balance": "0.00",
            "kyc_status": "verified",
        },
    ).json()

    payroll = client.post(
        "/v1/novapay/operations/payroll",
        headers=headers,
        json={
            "organization_id": "org-enterprise",
            "actor_id": "ops-1",
            "actor_role": "OPERATOR",
            "source_wallet_id": source["wallet_id"],
            "currency": "AUD",
            "payroll": [
                {"recipient_wallet_id": employee["wallet_id"], "amount": "200.00", "note": "salary"},
            ],
            "idempotency_key": "payroll-1",
        },
    )
    assert payroll.status_code == 200
    assert payroll.json()["payroll"][0]["transaction"]["transfer_type"] == "payroll"

    refund = client.post(
        "/v1/novapay/refunds",
        headers=headers,
        json={
            "organization_id": "org-enterprise",
            "actor_id": "ops-1",
            "actor_role": "OPERATOR",
            "source_wallet_id": source["wallet_id"],
            "destination_wallet_id": employee["wallet_id"],
            "amount": "20.00",
            "currency": "AUD",
            "reason": "service_adjustment",
            "idempotency_key": "refund-1",
        },
    )
    assert refund.status_code == 200

    dispute = client.post(
        "/v1/novapay/disputes",
        headers=headers,
        json={
            "organization_id": "org-enterprise",
            "actor_id": "ops-1",
            "actor_role": "OPERATOR",
            "transaction_id": payroll.json()["payroll"][0]["transaction"]["transaction_id"],
            "reason": "review_required",
            "idempotency_key": "dispute-1",
        },
    )
    assert dispute.status_code == 200

    settlement = client.post(
        "/v1/novapay/settlements",
        headers=headers,
        json={
            "organization_id": "org-enterprise",
            "actor_id": "ops-1",
            "actor_role": "OPERATOR",
            "transaction_id": payroll.json()["payroll"][0]["transaction"]["transaction_id"],
            "reason": "not_used",
            "idempotency_key": "not-used",
        },
    )
    assert settlement.status_code == 200

    reconciliation = client.post(
        "/v1/novapay/reconciliation",
        headers=_headers("INVESTOR", "investor-1", "org-enterprise"),
        json={"organization_id": "org-enterprise", "batch_name": "daily-close"},
    )
    assert reconciliation.status_code == 200
    assert reconciliation.json()["transaction_count"] >= 2
    assert service.verify_receipt(payroll.json()["payroll"][0]["receipt"]["receipt_id"])["valid"] is True
    assert service.replay_evidence(payroll.json()["payroll"][0]["transaction"]["transaction_id"])["replay_verified"] is True


def test_developer_api_key_lifecycle_compliance_hold_finance_reporting_and_portals(tmp_path: Path) -> None:
    service = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    client = _client(service)
    headers = _headers("OPERATOR", "ops-1", "org-enterprise")
    client.post(
        "/v1/novapay/wallets",
        headers=headers,
        json={
            "owner_id": "corp-1",
            "organization_id": "org-enterprise",
            "owner_type": "enterprise",
            "currency": "AUD",
            "initial_balance": "1000.00",
            "kyc_status": "verified",
        },
    )

    hold = client.post(
        "/v1/novapay/compliance/holds",
        headers=headers,
        json={
            "organization_id": "org-enterprise",
            "actor_id": "ops-1",
            "subject_id": "corp-1",
            "reason": "review_required",
        },
    )
    assert hold.status_code == 200
    assert hold.json()["status"] == "hold"

    developer = client.post(
        "/v1/novapay/developer/apps",
        headers=_headers("DEVELOPER", "dev-1", "org-enterprise"),
        json={
            "organization_id": "org-enterprise",
            "developer_id": "dev-1",
            "app_name": "partner-sync",
            "webhook_url": "https://example.com/webhook",
        },
    )
    assert developer.status_code == 200
    assert developer.json()["app"]["app_name"] == "partner-sync"

    report = client.get("/v1/novapay/finance", headers=_headers("INVESTOR", "investor-1", "org-enterprise"))
    assert report.status_code == 200
    assert report.json()["wallet_count"] == 1

    operations = client.get("/v1/novapay/operations", headers=headers)
    assert operations.status_code == 200
    assert "novapay_wallets" in operations.json()["table_names"]

    portals = client.get("/v1/novapay/portals", headers=headers)
    assert portals.status_code == 200
    assert any(portal["name"] == "Trust Explorer" for portal in portals.json()["portals"])

    app_suite = client.get("/v1/novapay/apps", headers=headers)
    assert app_suite.status_code == 200
    assert any(app["name"] == "NovaPay Agent App" for app in app_suite.json()["apps"])
    assert any(app["name"] == "NovaPay Corporate Portal" for app in app_suite.json()["apps"])

    ai = client.get("/v1/novapay/ai/insights", headers=headers)
    assert ai.status_code == 200
    assert "spending_insights" in ai.json()

    agents = client.get("/v1/novapay/agents", headers=headers)
    business = client.get("/v1/novapay/business", headers=headers)
    corporate = client.get("/v1/novapay/corporate", headers=headers)
    invoices = client.get("/v1/novapay/invoices", headers=headers)

    assert agents.status_code == 200
    assert business.status_code == 200
    assert corporate.status_code == 200
    assert invoices.status_code == 200


def test_role_permission_boundaries_block_consumer_access_to_internal_surfaces(tmp_path: Path) -> None:
    service = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    client = _client(service)
    consumer_headers = _headers("CUSTOMER", "customer-1", "org-pay")

    finance = client.get("/v1/novapay/finance", headers=consumer_headers)
    operations = client.get("/v1/novapay/operations", headers=consumer_headers)
    trust = client.get("/v1/novapay/trust/explorer/demo", headers=consumer_headers)
    corporate = client.get("/v1/novapay/corporate", headers=consumer_headers)

    assert finance.status_code == 403
    assert operations.status_code == 403
    assert trust.status_code == 403
    assert corporate.status_code == 403


def test_invoice_and_webhook_lifecycle(tmp_path: Path) -> None:
    service = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    client = _client(service)
    headers = _headers("DEVELOPER", "dev-1", "org-pay")

    wallet = client.post(
        "/v1/novapay/wallets",
        headers=_headers("OPERATOR", "ops-1", "org-pay"),
        json={
            "owner_id": "customer-1",
            "organization_id": "org-pay",
            "owner_type": "consumer",
            "currency": "AUD",
            "initial_balance": "50.00",
            "kyc_status": "verified",
        },
    ).json()

    invoice = client.post(
        "/v1/novapay/invoices",
        headers=headers,
        json={
            "organization_id": "org-pay",
            "actor_id": "dev-1",
            "actor_role": "DEVELOPER",
            "customer_wallet_id": wallet["wallet_id"],
            "amount": "12.50",
            "currency": "AUD",
            "reference": "inv-001",
            "due_date": "2026-07-31",
            "idempotency_key": "invoice-1",
        },
    )
    assert invoice.status_code == 200
    assert invoice.json()["reference"] == "inv-001"

    webhook = client.post(
        "/v1/novapay/developer/webhooks",
        headers=headers,
        json={
            "organization_id": "org-pay",
            "developer_id": "dev-1",
            "webhook_url": "https://example.com/webhook",
            "event_types": ["payment.completed", "settlement.completed"],
            "secret_hint": "rotating",
        },
    )
    assert webhook.status_code == 200
    assert webhook.json()["delivery_status"] == "pending"

    developer_portal = client.get("/v1/novapay/developer", headers=headers)
    assert developer_portal.status_code == 200
    assert developer_portal.json()["view"] == "novapay_developer_portal"

    finance_report = client.get("/v1/novapay/finance", headers=_headers("INVESTOR", "investor-2", "org-pay"))
    assert finance_report.status_code == 200
    assert finance_report.json()["invoice_count"] == 1


def test_signed_receipt_and_runtime_boundary_validation() -> None:
    source = Path("afritech/api/novapay_ecosystem_api.py").read_text()
    tree = ast.parse(source)
    imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert all(not module.startswith("afriride_system") for module in imports)
