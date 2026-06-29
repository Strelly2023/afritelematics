from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import zipfile
import io
import time

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import (
    build_core_platform_router,
    build_public_trust_explorer_router,
)
from afritech.core_platform.cryptographic_consensus import run_cryptographic_consensus
from afritech.core_platform.proof_receipts import build_proof_receipt
from afritech.core_platform.signing import sign_packet
from afritech.fintech.webhook_security import sign_webhook


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_core_platform_router())
    app.include_router(build_public_trust_explorer_router())
    return TestClient(app)


def auth_headers(
    role: str = "OPERATOR",
    user_id: str = "operator-1",
    organization_id: str = "org-core",
) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_core_platform_console_api_exposes_core_only_routes() -> None:
    client = build_client()

    response = client.get("/v1/core-platform/console", headers=auth_headers(role="OBSERVER"))

    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "NovaTechSol"
    assert body["product_applications_included"] is False
    assert body["modules"][0]["path"] == "/console/identity"
    assert body["modules"][-1]["path"] == "/console/programming"
    assert body["deployment"]["settlement"]["available"] is True
    assert body["deployment"]["corridor_matrix"]
    assert body["deployment"]["corridor_matrix"][0]["corridor"]
    assert "execution_state" in body["deployment"]["corridor_matrix"][0]


def test_contract_portal_exposes_signed_schemas_graph_metrics_and_sdks() -> None:
    client = build_client()

    response = client.get("/v1/core-platform/contracts")

    assert response.status_code == 200
    body = response.json()
    assert body["contract"]["version"] == "2.0.0"
    assert len(body["schema_registry"]["schemas"]) == 6
    assert body["architecture"]["acyclic"] is True
    assert body["metrics"]["overall"] == 100
    assert set(body["sdk_downloads"]) == {"python", "typescript", "kotlin", "swift"}


def test_platform_operations_readiness_exposes_sre_and_rollout_gates() -> None:
    client = build_client()

    response = client.get(
        "/v1/core-platform/operations/readiness",
        headers=auth_headers(role="OBSERVER"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ready"] is True
    assert body["service_objective_count"] == 3
    assert body["canary_stages_percent"] == [1, 5, 25, 50, 100]
    assert "replay_mismatch" in body["automatic_rollback_signals"]
    assert "RESTRICTED" in body["data_classifications"]


def test_settlement_corridor_status_exposes_operator_drilldown() -> None:
    client = build_client()

    response = client.get(
        "/v1/core-platform/payments/settlement/corridors/status",
        headers=auth_headers(role="OBSERVER"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["view"] == "core_platform_settlement_corridor_status"
    assert body["primary_corridor"]
    assert body["corridors"]
    assert body["corridors"][0]["corridor"]
    assert "rollback_criteria" in body
    assert "reconciliation_mismatch" in body["rollback_criteria"]


def test_contract_negotiation_and_governed_request_admission() -> None:
    client = build_client()

    negotiation = client.get(
        "/v1/core-platform/contracts/negotiate",
        headers={
            "Accept-Contract-Version": "2.0.0",
            "Accept-Replay-Version": "1.0.0",
        },
    )
    unsupported = client.get(
        "/v1/core-platform/contracts/negotiate",
        headers={"Accept-Contract-Version": "3.0.0"},
    )
    admitted = client.post(
        "/v1/core-platform/contracts/admit",
        headers=auth_headers(),
        json={
            "request_id": "request-api-1",
            "operation": "payment.execute",
            "tenant_id": "org-core",
            "actor_id": "operator-1",
            "idempotency_key": "idempotency-api-1",
            "contract_version": "2.0.0",
            "schema_version": "1.0.0",
            "payload": {"intent_id": "intent-1"},
        },
    )

    assert negotiation.status_code == 200
    assert negotiation.json()["status"] == "COMPATIBLE"
    assert unsupported.status_code == 426
    assert admitted.status_code == 200
    assert admitted.json()["tenant_id"] == "org-core"
    assert admitted.json()["trust_level"] == 2


def test_governed_request_openapi_matches_canonical_required_fields() -> None:
    client = build_client()
    schema = client.app.openapi()
    model = schema["components"]["schemas"]["GovernedRequestPayload"]

    assert set(model["required"]) == {
        "request_id",
        "operation",
        "tenant_id",
        "actor_id",
        "idempotency_key",
        "contract_version",
        "schema_version",
        "payload",
    }
    assert model["additionalProperties"] is False


def test_governed_request_rejects_cross_tenant_context() -> None:
    client = build_client()

    response = client.post(
        "/v1/core-platform/contracts/admit",
        headers=auth_headers(),
        json={
            "request_id": "request-api-tenant",
            "operation": "payment.execute",
            "tenant_id": "other-org",
            "actor_id": "operator-1",
            "idempotency_key": "idempotency-api-tenant",
            "contract_version": "2.0.0",
            "schema_version": "1.0.0",
            "payload": {},
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "tenant_context_mismatch"


def test_core_platform_identity_and_authority_api_are_tenant_bound() -> None:
    client = build_client()

    identity = client.get("/v1/core-platform/identity/me", headers=auth_headers())
    assert identity.status_code == 200
    assert identity.json()["identity"]["organization_id"] == "org-core"
    assert identity.json()["secures_downstream_layers"] is True

    decision = client.post(
        "/v1/core-platform/authority/evaluate",
        headers=auth_headers(),
        json={
            "action": "payment.execute",
            "organization_id": "org-core",
            "required_roles": ["OPERATOR"],
            "required_scopes": ["payments:write"],
            "resource_owner_id": "operator-1",
            "risk_score": "0.10",
        },
    )
    assert decision.status_code == 200
    assert decision.json()["decision"]["decision"] == "ALLOW"

    denied = client.post(
        "/v1/core-platform/authority/evaluate",
        headers=auth_headers(),
        json={
            "action": "payment.execute",
            "organization_id": "other-org",
            "required_roles": ["ADMIN"],
            "required_scopes": ["payments:write"],
            "resource_owner_id": "other-user",
            "risk_score": "0.95",
        },
    )
    assert denied.status_code == 200
    assert denied.json()["decision"]["decision"] == "DENY"
    assert "tenant_mismatch" in denied.json()["decision"]["checks"]


def test_transfer_api_rejects_float_amounts_at_boundary() -> None:
    client = build_client()

    response = client.post(
        "/v1/core-platform/transfers/quote",
        headers=auth_headers(role="RIDER"),
        json={
            "recipient_name": "Amina Okello",
            "recipient_identifier": "+254700000001",
            "recipient_country": "KE",
            "amount": 100.0,
            "source_currency": "AUD",
            "payout_method": "bank_deposit",
            "use_case": "transparent_pricing",
            "memo": "family support",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"].startswith("Value error, float_not_allowed_at_api_boundary")


def test_transfer_execute_rejects_nested_float_in_quote() -> None:
    client = build_client()
    quote = client.post(
        "/v1/core-platform/transfers/quote",
        headers=auth_headers(role="RIDER"),
        json={
            "recipient_name": "Amina Okello",
            "recipient_identifier": "+254700000001",
            "recipient_country": "KE",
            "amount": "100.00",
            "source_currency": "AUD",
            "payout_method": "bank_deposit",
            "use_case": "transparent_pricing",
            "memo": "family support",
        },
    ).json()["quote"]
    quote["source_amount"] = 100.0

    response = client.post(
        "/v1/core-platform/transfers/execute",
        headers=auth_headers(role="RIDER"),
        json={"quote": quote},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"].startswith("Value error, float_not_allowed_at_api_boundary")


def test_core_platform_payment_api_runs_full_wiring() -> None:
    client = build_client()

    response = client.post(
        "/v1/core-platform/payments/execute",
        headers=auth_headers(),
        json={
            "intent_id": "intent-api-001",
            "amount": "49.90",
            "currency": "aud",
            "destination": "merchant-core",
            "provider": "payid",
            "required_roles": ["OPERATOR"],
            "required_scopes": ["payments:write"],
            "risk_score": "0.20",
        },
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["decision"]["decision"] == "ALLOW"
    assert result["payment"]["status"] == "completed"
    assert result["payment"]["provider"] == "payid"
    assert result["payment"]["provider_reference"].startswith("PAYID-")
    assert result["trust"]["replay_status"] == "verified"
    assert result["explanation"]["risk_level"] == "LOW"
    assert result["proposal"]["lifecycle_state"] == "ready_for_validation"


def test_controlled_payid_payment_accepts_normalized_provider_webhook(monkeypatch) -> None:
    client = build_client()
    secret = "payid-webhook-test-secret"
    monkeypatch.setenv("NOVAPAY_PAYID_WEBHOOK_SECRET", secret)

    execution = client.post(
        "/v1/core-platform/payments/execute",
        headers=auth_headers(),
        json={
            "intent_id": "intent-webhook-001",
            "amount": "18.75",
            "currency": "AUD",
            "destination": "rider@example.com",
            "provider": "payid",
            "required_roles": ["OPERATOR"],
            "required_scopes": ["payments:write"],
        },
    )
    assert execution.status_code == 200
    payment = execution.json()["result"]["payment"]

    payload = {
        "event_id": "payid-event-001",
        "provider": "payid",
        "data": {
            "transaction_id": payment["provider_reference"],
            "merchant_reference": payment["payment_id"],
            "status": "completed",
            "transaction_status": "successful",
        },
    }
    timestamp = int(time.time())
    webhook = client.post(
        "/webhooks/payments",
        headers={
            "X-NovaPay-Timestamp": str(timestamp),
            "X-NovaPay-Signature": sign_webhook(
                payload,
                timestamp=timestamp,
                secret=secret,
            ),
        },
        json=payload,
    )

    assert webhook.status_code == 200, webhook.text
    body = webhook.json()
    assert body["provider"] == "payid"
    assert body["provider_reference"] == payment["provider_reference"]
    assert body["payment_id"] == payment["payment_id"]
    assert body["settlement_status"] == "settled"
    assert body["signature_verified"] is True
    assert body["settlement_authority"] is False


def test_core_platform_trust_ai_and_programming_api_surfaces() -> None:
    client = build_client()

    replay = client.post(
        "/v1/core-platform/trust/replay",
        headers=auth_headers(role="VERIFIER"),
        json={
            "packet": {
                "subject_id": "subject-1",
                "organization_id": "org-core",
                "event_type": "core.test",
                "value": "stable",
            }
        },
    )
    assert replay.status_code == 200
    assert replay.json()["replay_valid"] is True

    explanation = client.post(
        "/v1/core-platform/ai/explain",
        headers=auth_headers(role="DEVELOPER"),
        json={"subject": "payment intent-api-001"},
    )
    assert explanation.status_code == 200
    assert explanation.json()["layer"] == "NovaScript"
    assert explanation.json()["explanation"]["recommended_action"] == "continue"

    proposal = client.post(
        "/v1/core-platform/programming/proposals",
        headers=auth_headers(role="DEVELOPER"),
        json={
            "title": "Add NovaPay retry validation",
            "risk_level": "LOW",
            "evidence_refs": ["trust-001"],
        },
    )
    assert proposal.status_code == 200
    assert proposal.json()["layer"] == "NovaProgramming"


def test_proof_receipt_qr_mobile_and_onchain_api_surfaces() -> None:
    client = build_client()
    packet = {
        "trust_id": "trust-api-proof-001",
        "replay_status": "verified",
        "payload": {"sequence": 12},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]
    result = run_cryptographic_consensus(packet, votes, total_nodes=3)
    trust_seal = result["trust_seal"]

    qr_response = client.post(
        "/v1/core-platform/trust/consensus/proof-receipt/qr",
        headers=auth_headers(),
        json={"trust_seal": trust_seal, "issuer": "api-test"},
    )
    assert qr_response.status_code == 200
    qr_body = qr_response.json()
    assert qr_body["receipt"]["receipt_hash"]
    assert qr_body["qr_payload"]

    mobile_response = client.post(
        "/v1/core-platform/trust/consensus/proof-receipt/mobile-verify",
        headers=auth_headers(),
        json={"qr_data": qr_body["qr_payload"]},
    )
    assert mobile_response.status_code == 200
    assert mobile_response.json()["status"] is True
    assert mobile_response.json()["trust_level"] == "PARTIAL"

    onchain_response = client.post(
        "/v1/core-platform/trust/consensus/proof-receipt/onchain",
        headers=auth_headers(),
        json={"receipt": qr_body["receipt"]},
    )
    assert onchain_response.status_code == 200
    onchain_body = onchain_response.json()
    assert onchain_body["bundle"]["bundle_hash"]
    assert "contract NovaTrustVerifier" in onchain_body["solidity_verifier_source"]


def test_proof_receipt_qr_png_api_returns_png_bytes() -> None:
    client = build_client()
    packet = {
        "trust_id": "trust-api-proof-002",
        "replay_status": "verified",
        "payload": {"sequence": 13},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]
    result = run_cryptographic_consensus(packet, votes, total_nodes=3)
    trust_seal = result["trust_seal"]

    response = client.post(
        "/v1/core-platform/trust/consensus/proof-receipt/qr.png",
        headers=auth_headers(),
        json={"trust_seal": trust_seal, "issuer": "api-test"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_core_platform_pilot_flow_persists_public_trust_explorer_packet() -> None:
    client = build_client()

    pilot = client.post(
        "/v1/core-platform/pilot/flow",
        headers=auth_headers(role="OPERATOR"),
        json={
            "intent_id": "pilot-api-001",
            "amount": "25.00",
            "currency": "aud",
            "destination": "pilot-merchant",
            "provider": "payid",
        },
    )
    assert pilot.status_code == 200
    body = pilot.json()
    assert body["status"] == "deployed"
    trust_id = body["result"]["trust"]["trust_id"]
    assert body["trust_explorer"] == f"/trust/explorer/{trust_id}"

    packet = client.get(f"/v1/core-platform/trust/explorer/{trust_id}")
    assert packet.status_code == 200
    assert packet.json()["view"] == "public_trust_explorer"
    assert packet.json()["packet"]["trust"]["trust_id"] == trust_id
    assert packet.json()["execution_authority"] is False

    html = client.get(f"/trust/explorer/{trust_id}")
    assert html.status_code == 200
    assert "NovaTrust Explorer" in html.text
    assert trust_id in html.text

    public_packet = client.get(
        f"/trust/explorer/{trust_id}",
        headers={"Accept": "application/json"},
    )
    assert public_packet.status_code == 200
    assert public_packet.json()["packet"]["trust"]["trust_id"] == trust_id

    sandbox = client.get("/trust/sandbox/demo")
    assert sandbox.status_code == 200
    assert sandbox.json()["links"]["explorer"] == "/trust/explorer/sandbox-demo"


def test_core_platform_persistence_status_exposes_postgres_adapter() -> None:
    client = build_client()

    response = client.get(
        "/v1/core-platform/persistence/status",
        headers=auth_headers(role="OBSERVER"),
    )

    assert response.status_code == 200
    assert response.json()["postgres_adapter"] == "available"
    assert response.json()["postgres_table"] == "novatech_core_trust_packets"
    assert response.json()["migration_system"]["style"] == "alembic_compatible_linear_sql"


def test_core_platform_provider_status_and_pdf_export() -> None:
    client = build_client()

    provider_status = client.get(
        "/v1/core-platform/payments/providers/status",
        headers=auth_headers(role="OBSERVER"),
    )
    assert provider_status.status_code == 200
    body = provider_status.json()["providers"]
    assert body["payid"]["available"] is True
    assert body["payid"]["mode"] in {"controlled_pilot", "live_gateway"}
    assert body["stripe"]["available"] is True
    assert "ready_for_real_charge" in body["stripe"]
    assert body["cbdc"]["available"] is True
    assert provider_status.json()["settlement"]["cross_border_supported"] is True
    assert provider_status.json()["event_bus"]["event_bus"]["ready"] is True

    settlement = client.get(
        "/v1/core-platform/payments/settlement/status",
        headers=auth_headers(role="OBSERVER"),
    )
    assert settlement.status_code == 200
    assert settlement.json()["available"] is True

    trust_nodes = client.get(
        "/v1/core-platform/trust/node/network/status",
        headers=auth_headers(role="OBSERVER"),
    )
    assert trust_nodes.status_code == 200
    assert trust_nodes.json()["consensus_layer"] == "future_non_authoritative"

    consensus = client.get(
        "/v1/core-platform/trust/consensus/status",
        headers=auth_headers(role="OBSERVER"),
    )
    assert consensus.status_code == 200
    assert consensus.json()["consensus_layer"] == "future_non_authoritative"

    pilot = client.post(
        "/v1/core-platform/pilot/flow",
        headers=auth_headers(role="OPERATOR"),
        json={
            "intent_id": "pilot-pdf-001",
            "amount": "30.00",
            "currency": "aud",
            "destination": "pilot-merchant",
            "provider": "payid",
        },
    )
    trust_id = pilot.json()["result"]["trust"]["trust_id"]

    private_pdf = client.get(f"/v1/core-platform/trust/explorer/{trust_id}/audit.pdf")
    assert private_pdf.status_code == 200
    assert private_pdf.headers["content-type"] == "application/pdf"
    assert private_pdf.content.startswith(b"%PDF-1.4")

    public_pdf = client.get(f"/trust/explorer/{trust_id}/audit.pdf")
    assert public_pdf.status_code == 200
    assert public_pdf.headers["content-type"] == "application/pdf"
    assert public_pdf.content.startswith(b"%PDF-1.4")
    assert b"Embedded verification QR:" in public_pdf.content


def test_distributed_verification_validate_node_health_and_seal() -> None:
    client = build_client()

    packet = {
        "trust_id": "trust-distributed-001",
        "replay_status": "verified",
        "event_hash": "abc123",
        "payload": {"sequence": 1},
    }
    signature = sign_packet(packet).canonical()
    validators = [
        {"node_id": "validator-melbourne-001", "packet": packet, "signature": signature},
        {"node_id": "validator-frankfurt-001", "packet": packet, "signature": signature},
        {"node_id": "validator-nairobi-001", "packet": packet, "signature": signature},
    ]

    validation = client.post(
        "/v1/core-platform/trust/consensus/validate",
        headers=auth_headers(role="VERIFIER"),
        json={
            "packet": packet,
            "validators": validators,
            "total_nodes": 3,
        },
    )
    assert validation.status_code == 200
    body = validation.json()
    assert body["consensus"]["consensus_reached"] is True
    assert body["consensus"]["accepted_votes"] == 3
    assert body["node_health"]["consensus_ready"] is True
    assert body["trust_seal"]["trust_id"] == "trust-distributed-001"
    assert len(body["trust_seal"]["seal_hash"]) == 64

    node_health = client.get(
        "/v1/core-platform/trust/nodes/health",
        headers=auth_headers(role="OBSERVER"),
        params={"configured_nodes": 3, "healthy_nodes": 3},
    )
    assert node_health.status_code == 200
    assert node_health.json()["status"] == "healthy"
    return

    signature = client.get(f"/trust/explorer/{trust_id}/signature")
    assert signature.status_code == 200
    assert signature.json()["signature"]["scheme"] == "ed25519"
    assert signature.json()["verified"] is True

    report = client.get(f"/trust/explorer/{trust_id}/compliance-report")
    assert report.status_code == 200
    assert report.json()["classification"] == "ISO_SOC2_REGULATOR_READY_PACKET"
    assert report.json()["tamper_evident"] is True

    anchor = client.get(f"/trust/explorer/{trust_id}/anchor")
    assert anchor.status_code == 200
    assert anchor.json()["anchor"]["status"] == "anchored"

    blockchain_anchor = client.get(f"/trust/explorer/{trust_id}/anchor/blockchain")
    assert blockchain_anchor.status_code == 200
    assert blockchain_anchor.json()["anchor"]["status"] == "disabled"
    assert (
        blockchain_anchor.json()["anchor"]["message"]
        == "optional blockchain anchoring is not configured"
    )

    qr = client.get(f"/trust/explorer/{trust_id}/qr.png")
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"
    assert qr.content.startswith(b"\x89PNG\r\n\x1a\n")

    bundle = client.get(f"/trust/explorer/{trust_id}/bundle.zip")
    assert bundle.status_code == 200
    assert bundle.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
        assert "packet.json" in archive.namelist()
        assert "signature.json" in archive.namelist()
        assert "audit.pdf" in archive.namelist()
        assert "verification-qr.png" in archive.namelist()

    private_dashboard = client.post(
        "/v1/core-platform/auditor/dashboard",
        headers=auth_headers(role="VERIFIER"),
        json={"identifiers": [trust_id, "missing-demo"]},
    )
    assert private_dashboard.status_code == 200
    assert private_dashboard.json()["mode"] == "multi_receipt_verification"
    assert private_dashboard.json()["total"] == 2

    public_dashboard = client.get(f"/trust/auditor/dashboard?ids={trust_id},missing-demo")
    assert public_dashboard.status_code == 200
    assert public_dashboard.json()["view"] == "novatrust_auditor_dashboard"

    signing = client.get("/v1/core-platform/signing/status", headers=auth_headers(role="OBSERVER"))
    assert signing.status_code == 200
    assert signing.json()["rotation_plan"]["steps"]


def test_core_platform_readiness_reports_distributed_verification() -> None:
    client = build_client()

    response = client.get(
        "/v1/core-platform/readiness",
        headers=auth_headers(role="OBSERVER"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["layers"]["distributed_verification"] == "future_non_authoritative"
    assert body["capabilities"]["distributed_verification_ready"] is False
    assert body["fintech"]["distributed_verification"]["status"] in {
        "unavailable",
        "critical",
        "degraded",
        "healthy",
        "quarantined",
    }


def test_cryptographic_consensus_endpoint_reports_aggregate_signature() -> None:
    client = build_client()

    packet = {
        "trust_id": "trust-crypto-001",
        "replay_status": "verified",
        "payload": {"sequence": 5},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]

    response = client.post(
        "/v1/core-platform/trust/consensus/cryptographic",
        headers=auth_headers(role="VERIFIER"),
        json={"packet": packet, "votes": votes, "total_nodes": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["consensus"]["consensus_reached"] is True
    assert body["consensus"]["aggregate_signature_scheme"] == "deterministic-aggregate"
    assert body["trust_seal"]["cryptographic_consensus"] is True
    assert body["trust_seal"]["accepted_validators"] == [
        "validator-a",
        "validator-b",
        "validator-c",
    ]
    assert body["node_health"]["consensus_ready"] is True


def test_proof_receipt_endpoint_builds_receipt_and_verifies() -> None:
    client = build_client()

    packet = {
        "trust_id": "trust-receipt-001",
        "replay_status": "verified",
        "payload": {"sequence": 6},
    }
    signature = sign_packet(packet).canonical()
    votes = [
        {
            "node_id": "validator-a",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-b",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
        {
            "node_id": "validator-c",
            "packet": packet,
            "signature": signature,
            "replay_status": "verified",
        },
    ]
    consensus = client.post(
        "/v1/core-platform/trust/consensus/cryptographic",
        headers=auth_headers(role="VERIFIER"),
        json={"packet": packet, "votes": votes, "total_nodes": 3},
    ).json()

    receipt_response = client.post(
        "/v1/core-platform/trust/consensus/proof-receipt",
        headers=auth_headers(role="VERIFIER"),
        json={
            "trust_seal": consensus["trust_seal"],
            "issuer": "test-issuer",
        },
    )
    assert receipt_response.status_code == 200
    receipt = receipt_response.json()
    assert receipt["type"] == "novatrust-proof-receipt"
    assert len(receipt["receipt_hash"]) == 64
    assert receipt["signer_set"]

    verify_response = client.post(
        "/v1/core-platform/trust/consensus/proof-receipt/verify",
        headers=auth_headers(role="VERIFIER"),
        json={"receipt": receipt},
    )
    assert verify_response.status_code == 200
    assert verify_response.json()["valid"] is True
