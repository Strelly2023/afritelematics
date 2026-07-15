from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novapay_ecosystem_api import build_novapay_ecosystem_router
from afritech.novapay.ecosystem_contract import (
    novapay_constitutional_flow,
    novapay_ecosystem_contract,
    novapay_frontend_contract,
    novapay_production_gate_report,
)


def _headers(role: str = "CUSTOMER", user_id: str = "customer-1", organization_id: str = "org-pay") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novapay_ecosystem_router())
    return TestClient(app)


def test_novapay_ecosystem_contract_covers_required_surfaces_and_backend_domains() -> None:
    contract = novapay_ecosystem_contract()
    surface_names = {surface["name"] for surface in contract["surfaces"]}
    backend_names = {domain["name"] for domain in contract["backend"]["domains"]}

    assert {"Consumer App", "Agent App", "Merchant App", "Business App", "Partner Portal", "Operations Portal", "Compliance Portal", "Risk & Fraud Center", "Executive Command Center", "Developer Platform"}.issubset(surface_names)
    assert {"Double-Entry Ledger", "Transfer", "Risk and Compliance", "Settlement and Reconciliation", "Treasury", "Event Platform", "Workflow Platform", "Audit and Observability"}.issubset(backend_names)
    ledger = next(domain for domain in contract["backend"]["domains"] if domain["name"] == "Double-Entry Ledger")
    assert ledger["source_of_truth"] is True


def test_authority_boundaries_forbid_financial_truth_bypass() -> None:
    boundaries = novapay_ecosystem_contract()["authority_boundaries"]

    assert "double-entry accounting" in boundaries["NovaLedger"]
    assert "frontend_authoritative_balance" in boundaries["forbidden"]
    assert "wallet_balance_direct_mutation" in boundaries["forbidden"]
    assert "ai_ledger_posting" in boundaries["forbidden"]
    assert "offline_transaction_marked_completed_without_server_confirmation" in boundaries["forbidden"]


def test_constitutional_flow_preserves_ledger_reconciliation_receipt_and_evidence_order() -> None:
    flow = novapay_constitutional_flow()

    assert flow.index("Authenticate") < flow.index("Authorize")
    assert flow.index("Generate quote") < flow.index("Evaluate risk and compliance")
    assert flow.index("Post balanced ledger entries") < flow.index("Execute partner instruction")
    assert flow.index("Reconcile") < flow.index("Generate signed receipt") < flow.index("Record immutable evidence")


def test_frontend_contract_never_makes_local_state_authoritative() -> None:
    frontend = novapay_frontend_contract()

    assert "Offline queued financial transactions must not be shown as completed until server confirmation." in frontend["offline_rules"]
    assert any("Frontend must never invent balances" in rule for rule in frontend["offline_rules"])
    assert "No secrets embedded in bundles" in frontend["production_gates"]


def test_production_gates_do_not_enable_real_payments() -> None:
    gates = novapay_production_gate_report()

    assert gates["status"] == "PRODUCTION_NOT_APPROVED"
    assert gates["real_payments_enabled"] is False
    assert len(gates["gates"]) >= 17
    assert all(gate["implemented"] is True for gate in gates["gates"])
    assert all(gate["verified"] is False for gate in gates["gates"])
    assert all(gate["approved"] is False for gate in gates["gates"])


def test_novapay_ecosystem_api_exposes_read_only_contract() -> None:
    client = _client()

    response = client.get("/v1/novapay/ecosystem/architecture", headers=_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ARCHITECTURE_CONTRACT_COMPLETE_RUNTIME_AND_APPROVAL_GATES_REQUIRED"
    assert payload["production_gates"]["real_payments_enabled"] is False

    boundaries = client.get("/v1/novapay/ecosystem/boundaries", headers=_headers())
    assert boundaries.status_code == 200
    assert "ai_high_risk_approval" in boundaries.json()["forbidden"]
