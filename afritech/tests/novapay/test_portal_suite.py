from __future__ import annotations

import ast
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novaportal_suite_api import build_novaportal_suite_router
from afritech.novapay import NovaPayEcosystem, NovaPayRepository, NovaPortalSuite


def _client(service: NovaPortalSuite) -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novaportal_suite_router(service))
    return TestClient(app)


def _headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_trust_explorer_receipt_payment_ride_replay_and_audit_bundle(tmp_path: Path) -> None:
    ecosystem = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    portal = NovaPortalSuite(ecosystem)
    client = _client(portal)
    headers = _headers("OPERATOR", "ops-1", "org-trust")

    sender = ecosystem.create_wallet(
        owner_id="customer-1",
        organization_id="org-trust",
        owner_type="consumer",
        currency="AUD",
        initial_balance="100.00",
        kyc_status="verified",
    )
    receiver = ecosystem.create_wallet(
        owner_id="merchant-1",
        organization_id="org-trust",
        owner_type="merchant",
        currency="AUD",
        initial_balance="0.00",
        kyc_status="verified",
    )
    transfer = ecosystem.transfer_money(
        organization_id="org-trust",
        actor_id="customer-1",
        actor_role="CUSTOMER",
        sender_wallet_id=sender["wallet_id"],
        receiver_wallet_id=receiver["wallet_id"],
        amount="25.00",
        currency="AUD",
        transfer_type="payment",
        idempotency_key="portal-payment-1",
        metadata={"ride_id": "ride-123"},
    )

    explorer = client.get("/v1/novatrust/explorer")
    assert explorer.status_code == 200
    assert explorer.json()["view"] == "novatrust_explorer"

    receipt = client.get(f"/v1/novatrust/verify/receipt/{transfer['receipt']['receipt_id']}")
    assert receipt.status_code == 200
    assert receipt.json()["verified"] is True

    payment = client.get(f"/v1/novatrust/verify/payment/{transfer['transaction']['transaction_id']}")
    assert payment.status_code == 200
    assert payment.json()["verified"] is True

    ride = client.get("/v1/novatrust/verify/ride/ride-123")
    assert ride.status_code == 200
    assert ride.json()["verified"] is True

    replay = client.get(f"/v1/novatrust/replay/{transfer['transaction']['transaction_id']}")
    assert replay.status_code == 200
    assert replay.json()["replay"]["replay_verified"] is True

    bundle = client.get(f"/v1/novatrust/audit-bundles/{transfer['receipt']['receipt_id']}")
    assert bundle.status_code == 200
    assert bundle.json()["verified"] is True


def test_role_gated_portal_surfaces_return_expected_views(tmp_path: Path) -> None:
    ecosystem = NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3"))
    portal = NovaPortalSuite(ecosystem)
    client = _client(portal)

    ecosystem.create_wallet(
        owner_id="customer-1",
        organization_id="org-portals",
        owner_type="consumer",
        currency="AUD",
        initial_balance="1000.00",
        kyc_status="verified",
    )
    ecosystem.register_identity(
        identity_id="partner-1",
        identity_type="partner",
        organization_id="org-portals",
        kyc_status="verified",
    )

    support_headers = _headers("OPERATOR", "ops-1", "org-portals")
    finance_headers = _headers("INVESTOR", "investor-1", "org-portals")
    partner_headers = _headers("PARTNER", "partner-1", "org-portals")
    inspector_headers = _headers("VERIFIER", "inspector-1", "org-portals")

    assert client.get("/v1/novapay/support/customers", headers=support_headers).json()["view"] == "novapay_support_customers"
    assert client.get("/v1/novapay/support/cases", headers=support_headers).json()["view"] == "novapay_support_cases"
    assert client.get("/v1/novapay/support/disputes", headers=support_headers).json()["view"] == "novapay_support_disputes"
    assert client.get("/v1/novapay/support/refunds", headers=support_headers).json()["view"] == "novapay_support_refunds"

    assert client.get("/v1/novapay/compliance/alerts", headers=support_headers).json()["view"] == "novapay_compliance_alerts"
    assert client.get("/v1/novapay/compliance/aml", headers=support_headers).json()["view"] == "novapay_compliance_aml"
    assert client.get("/v1/novapay/compliance/sanctions", headers=support_headers).json()["view"] == "novapay_compliance_sanctions"
    assert client.get("/v1/novapay/compliance/investigations", headers=support_headers).json()["view"] == "novapay_compliance_investigations"
    assert client.get("/v1/novapay/compliance/reports", headers=support_headers).json()["view"] == "novapay_compliance_reports"

    assert client.get("/v1/novatech/operations/health", headers=support_headers).json()["view"] == "novatech_operations_health"
    assert client.get("/v1/novatech/operations/incidents", headers=support_headers).json()["view"] == "novatech_operations_incidents"
    assert client.get("/v1/novatech/operations/services", headers=support_headers).json()["view"] == "novatech_operations_services"
    assert client.get("/v1/novatech/operations/automation", headers=support_headers).json()["view"] == "novatech_operations_automation"

    assert client.get("/v1/novapay/finance/ledger", headers=finance_headers).json()["view"] == "novapay_finance_ledger"
    assert client.get("/v1/novapay/finance/settlements", headers=finance_headers).json()["view"] == "novapay_finance_settlements"
    assert client.get("/v1/novapay/finance/reconciliation", headers=finance_headers).json()["view"] == "novapay_finance_reconciliation"
    assert client.get("/v1/novapay/finance/reports", headers=finance_headers).json()["view"] == "novapay_finance_reports"

    assert client.get("/v1/novapay/partners", headers=partner_headers).json()["view"] == "novapay_partner_directory"
    assert client.get("/v1/novapay/partners/onboarding", headers=partner_headers).json()["view"] == "novapay_partner_onboarding"
    assert client.get("/v1/novapay/partners/certification", headers=partner_headers).json()["view"] == "novapay_partner_certification"
    assert client.get("/v1/novapay/partners/revenue", headers=partner_headers).json()["view"] == "novapay_partner_revenue"
    assert client.get("/v1/novapay/partners/sla", headers=partner_headers).json()["view"] == "novapay_partner_sla"

    assert client.get("/v1/novapay/inspector/inspections", headers=inspector_headers).json()["view"] == "novapay_inspector_inspections"
    assert client.get("/v1/novapay/inspector/evidence", headers=inspector_headers).json()["view"] == "novapay_inspector_evidence"
    assert client.get("/v1/novapay/inspector/checklists", headers=inspector_headers).json()["view"] == "novapay_inspector_checklists"
    assert client.get("/v1/novapay/inspector/incidents", headers=inspector_headers).json()["view"] == "novapay_inspector_incidents"


def test_consumer_is_blocked_from_internal_portals(tmp_path: Path) -> None:
    portal = NovaPortalSuite(NovaPayEcosystem(NovaPayRepository(tmp_path / "novapay.sqlite3")))
    client = _client(portal)
    consumer_headers = _headers("CUSTOMER", "customer-1", "org-portals")

    assert client.get("/v1/novapay/support/customers", headers=consumer_headers).status_code == 403
    assert client.get("/v1/novapay/compliance/alerts", headers=consumer_headers).status_code == 403
    assert client.get("/v1/novatech/operations/health", headers=consumer_headers).status_code == 403
    assert client.get("/v1/novapay/finance/ledger", headers=consumer_headers).status_code == 403
    assert client.get("/v1/novapay/partners", headers=consumer_headers).status_code == 403
    assert client.get("/v1/novapay/inspector/inspections", headers=consumer_headers).status_code == 403


def test_portal_api_does_not_import_afriride_system() -> None:
    source = Path("afritech/api/novaportal_suite_api.py").read_text()
    tree = ast.parse(source)
    imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert all(not module.startswith("afriride_system") for module in imports)
