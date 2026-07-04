from __future__ import annotations

import ast
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novaid_api import build_novaid_router
from afritech.core_platform.models import AuthorityRequest
from afritech.core_platform.services import NovaPowerEngine, NovaTrustService
from afritech.novaid import NovaIDEcosystem, NovaIDRepository
from afritech.novaid.ai import identity_assistant
from afritech.novaid.trust import build_identity_receipt, verify_identity_receipt


def _client(service: NovaIDEcosystem) -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novaid_router(service))
    return TestClient(app)


def _headers(role: str, user_id: str, organization_id: str) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_identity_lifecycle_passkeys_biometrics_and_devices(tmp_path: Path) -> None:
    service = NovaIDEcosystem(NovaIDRepository(tmp_path / "novaid.sqlite3"))

    identity = service.register_identity(
        identity_id="user-1",
        organization_id="org-novaid",
        email="user-1@novaid.local",
        display_name="User One",
        roles=("CUSTOMER",),
        scopes=("profile",),
        kyc_status="pending",
        attributes={"country": "AU"},
    )
    verified = service.verify_identity(
        identity_id="user-1",
        organization_id="org-novaid",
        method="document+biometric",
        evidence_refs=("doc-1", "face-1"),
    )
    passkey = service.register_passkey(
        identity_id="user-1",
        organization_id="org-novaid",
        credential_id="passkey-1",
        public_key="public-key-1",
        user_handle="user-1",
    )
    biometric = service.verify_biometric(
        identity_id="user-1",
        organization_id="org-novaid",
        modality="face",
        confidence="0.98",
    )
    device = service.register_device(
        identity_id="user-1",
        organization_id="org-novaid",
        device_id="device-1",
        public_key="device-pub-1",
        trust_level="trusted",
    )
    receipt = build_identity_receipt(
        subject_id="user-1",
        organization_id="org-novaid",
        event_type="novaid.identity.lifecycle",
        packet={"identity": identity["identity_id"], "state": verified["lifecycle_state"]},
    )

    assert identity["lifecycle_state"] == "pending"
    assert verified["verification_status"] == "verified"
    assert passkey["status"] == "active"
    assert biometric["status"] == "verified"
    assert device["status"] == "trusted"
    assert receipt["verified"] is True
    assert verify_identity_receipt(receipt["receipt"], NovaTrustService()) is True


def test_credentials_consent_sharing_kyc_kyb_and_recovery(tmp_path: Path) -> None:
    service = NovaIDEcosystem(NovaIDRepository(tmp_path / "novaid.sqlite3"))
    service.register_identity(
        identity_id="user-2",
        organization_id="org-novaid",
        roles=("CUSTOMER",),
        kyc_status="pending",
    )

    credential = service.issue_credential(
        subject_id="user-2",
        organization_id="org-novaid",
        credential_type="passport",
        claims={"country": "AU", "number": "P1234567"},
    )
    revoked = service.revoke_credential(
        credential_id=credential["record_id"],
        organization_id="org-novaid",
        reason="updated_document",
    )
    consent = service.grant_consent(
        subject_id="user-2",
        organization_id="org-novaid",
        purpose="share_profile",
        scopes=("profile", "email"),
        attributes=("name", "email"),
        recipient="partner-app",
    )
    shared = service.share_attributes(
        subject_id="user-2",
        organization_id="org-novaid",
        consent_id=consent["record_id"],
        attributes={"name": "User Two", "email": "user-2@novaid.local", "phone": "+61"},
        recipient="partner-app",
    )
    consent_revoked = service.revoke_consent(
        consent_id=consent["record_id"],
        organization_id="org-novaid",
        reason="user_request",
    )
    kyc = service.run_kyc(
        subject_id="user-2",
        organization_id="org-novaid",
        risk_score="0.12",
        checks=("document", "liveness"),
    )
    kyb = service.run_kyb(
        subject_id="business-2",
        organization_id="org-novaid",
        risk_score="0.22",
        checks=("director", "ubo"),
    )
    recovery = service.recover_identity(
        identity_id="user-2",
        organization_id="org-novaid",
        recovery_method="backup_codes",
        evidence_refs=("case-1",),
    )

    assert credential["status"] == "issued"
    assert revoked["status"] == "revoked"
    assert consent["status"] == "granted"
    assert shared["attributes"] == {"name": "User Two", "email": "user-2@novaid.local"}
    assert consent_revoked["status"] == "revoked"
    assert kyc["kyc"]["status"] == "verified"
    assert kyb["kyb"]["status"] == "verified"
    assert recovery["status"] == "verified"


def test_employee_partner_inspector_session_risk_and_governance(tmp_path: Path) -> None:
    service = NovaIDEcosystem(NovaIDRepository(tmp_path / "novaid.sqlite3"))
    service.register_identity(identity_id="partner-1", organization_id="org-novaid", roles=("PARTNER",), kyc_status="verified")
    employee = service.provision_employee(
        employee_id="employee-1",
        organization_id="org-novaid",
        employer_id="company-1",
        department="finance",
        access_roles=("APPROVER", "VIEWER"),
        expense_wallet_enabled=True,
    )
    partner_cert = service.register_partner_certificate(
        partner_id="partner-1",
        organization_id="org-novaid",
        certificate_name="partner-api",
        scopes=("identity.read", "directory.read"),
    )
    inspector = service.verify_inspector_offline(
        inspector_id="inspector-1",
        organization_id="org-novaid",
        certificate_id=partner_cert["record_id"],
        device_id="device-inspector-1",
        evidence_hash="hash-1",
    )
    oauth_client = service.register_oauth_client(
        organization_id="org-novaid",
        client_name="NovaID SDK",
        redirect_uris=("https://sdk.example/callback",),
        scopes=("openid", "profile"),
    )
    session = service.create_session(
        identity_id="employee-1",
        organization_id="org-novaid",
        device_id="device-employee-1",
        auth_method="passkey",
    )
    monitoring = service.monitor_sessions(organization_id="org-novaid")
    risk = service.risk_explanation(identity_id="employee-1", organization_id="org-novaid")
    advice_before = identity_assistant(subject_id="employee-1", topic="risk", context={"signal": "low"})
    advice_after = identity_assistant(subject_id="employee-1", topic="recovery", context={"signal": "review"})

    assert employee["status"] == "provisioned"
    assert partner_cert["status"] == "active"
    assert inspector["verified"] is True
    assert oauth_client["status"] == "active"
    assert session["status"] == "active"
    assert monitoring["active_sessions"] >= 1
    assert risk["confidence"] != ""
    assert advice_before["advisory_only"] is True
    assert advice_after["advisory_only"] is True


def test_openid_saml_contracts_and_authorization_boundary(tmp_path: Path) -> None:
    service = NovaIDEcosystem(NovaIDRepository(tmp_path / "novaid.sqlite3"))
    service.register_identity(
        identity_id="operator-1",
        organization_id="org-novaid",
        roles=("OPERATOR",),
        scopes=("identity:write",),
        kyc_status="verified",
    )
    service.register_identity(identity_id="customer-1", organization_id="org-novaid", roles=("CUSTOMER",), kyc_status="verified")

    openid = service.openid_configuration()
    saml = service.saml_metadata()
    power = service.authorize_action(
        identity_id="operator-1",
        organization_id="org-novaid",
        action="identity.provision",
        required_roles=("OPERATOR",),
        required_scopes=("identity:write",),
    )
    denied = service.authorize_action(
        identity_id="customer-1",
        organization_id="org-novaid",
        action="identity.provision",
        required_roles=("ADMIN",),
        required_scopes=("identity:write",),
    )
    trust = service.trust_receipt(
        subject_id="operator-1",
        organization_id="org-novaid",
        event_type="novaid.identity.audited",
        packet={"identity_id": "operator-1"},
    )

    assert openid["issuer"].endswith("/v1/novaid")
    assert saml["entity_id"].endswith("/saml")
    assert power["decision"]["decision"] == "ALLOW"
    assert denied["decision"]["decision"] == "DENY"
    assert trust["verified"] is True


def test_api_surfaces_and_role_gates(tmp_path: Path) -> None:
    service = NovaIDEcosystem(NovaIDRepository(tmp_path / "novaid.sqlite3"))
    client = _client(service)

    customer_headers = _headers("CUSTOMER", "customer-1", "org-novaid")
    operator_headers = _headers("OPERATOR", "operator-1", "org-novaid")
    developer_headers = _headers("DEVELOPER", "developer-1", "org-novaid")
    verifier_headers = _headers("VERIFIER", "verifier-1", "org-novaid")
    partner_headers = _headers("PARTNER", "partner-1", "org-novaid")

    assert client.get("/v1/novaid/personal", headers=customer_headers).json()["view"] == "novaid_personal_app"
    assert client.get("/v1/novaid/wallet", headers=customer_headers).json()["view"] == "novaid_wallet"
    assert client.get("/v1/novaid/business", headers=partner_headers).json()["view"] == "novaid_business_app"
    assert client.get("/v1/novaid/employee", headers=customer_headers).json()["view"] == "novaid_employee_app"
    assert client.get("/v1/novaid/partner", headers=partner_headers).json()["view"] == "novaid_partner_app"

    assert client.get("/v1/novaid/government", headers=operator_headers).status_code == 200
    assert client.get("/v1/novaid/enterprise", headers=operator_headers).status_code == 200
    assert client.get("/v1/novaid/command-center", headers=operator_headers).status_code == 200
    assert client.get("/v1/novaid/core", headers=operator_headers).json()["view"] == "novaid_core_catalog"
    assert client.get("/v1/novaid/inspector", headers=verifier_headers).status_code == 200
    assert client.get("/v1/novaid/standards", headers=developer_headers).json()["view"] == "novaid_standards"
    assert client.get("/v1/novaid/developer/openid-configuration", headers=developer_headers).status_code == 200
    assert client.get("/v1/novaid/developer/saml-metadata", headers=developer_headers).status_code == 200

    assert client.get("/v1/novaid/command-center", headers=customer_headers).status_code == 403
    assert client.get("/v1/novaid/developer", headers=customer_headers).status_code == 403


def test_repository_and_api_import_boundaries() -> None:
    api_source = Path("afritech/api/novaid_api.py").read_text()
    api_tree = ast.parse(api_source)
    api_imports = {
        node.module
        for node in api_tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert all(not module.startswith("afriride_system") for module in api_imports)

    service_source = Path("afritech/novaid/service.py").read_text()
    service_tree = ast.parse(service_source)
    service_imports = {
        node.module
        for node in service_tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "afritech.api" not in service_imports
