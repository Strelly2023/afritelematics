from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import zipfile
import io

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.core_platform_api import (
    build_core_platform_router,
    build_public_trust_explorer_router,
)


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
    assert "test_suite" in proposal.json()["proposal"]["validators"]


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
    assert blockchain_anchor.json()["anchor"]["message"] == "optional blockchain anchoring is not configured"

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
