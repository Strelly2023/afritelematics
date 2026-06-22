from __future__ import annotations

from fastapi.testclient import TestClient

from afritech.api.app import app
from afritech.api.auth.jwt_device_auth import JWT
from afritech.afriprogramming import control_plane, persistence
from afritech.afriprogramming.persistence import PlatformStore


def _auth_headers(*, role: str = "OPERATOR", user_id: str = "operator-1", organization_id: str = "org-nova") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_documentation_compliance_status_and_registry_surface_are_available(tmp_path) -> None:
    store = PlatformStore(tmp_path / "documentation-compliance.sqlite3")
    original_control_store = control_plane._STORE
    original_default_store = persistence._DEFAULT_STORE
    control_plane._STORE = store
    persistence._DEFAULT_STORE = store
    try:
        client = TestClient(app)
        headers = _auth_headers()

        status = client.get("/v1/novatech/documentation/status", headers=headers)
        assert status.status_code == 200
        payload = status.json()
        assert payload["view"] == "novatech_documentation_compliance_status"
        assert payload["document_registry"]["registry_id"] == "NOVATECH_DOCUMENT_REGISTRY_V1"
        assert payload["compliance_registry"]["registry_id"] == "NOVATECH_DOCUMENTATION_COMPLIANCE_REGISTRY_V1"
        assert payload["summary"]["standard_protocol"] == "AfriCPPT"
        assert payload["summary"]["policy_count"] >= 1
        assert payload["summary"]["marketplace_services"] >= 4
        assert payload["summary"]["training_completion_rate"] == 0.0
        assert payload["organization_governance"]["public_verification_portal"] == "/public/verify/portal"
        assert payload["public_verification"]["documentation_portal_surface"] == "/public/documentation/portal"
        assert payload["certification_issuance"]["issue_surface"] == "/v1/novatech/documentation/certification/issue"
        assert payload["trust_registry"]["trust"]["trust_score"] >= 0
        assert payload["continuous_assurance_reports"]["status"]["view"] == "novaprogramming_assurance_status"

        registry = client.get("/v1/novatech/documentation/registry", headers=headers)
        assert registry.status_code == 200
        registry_payload = registry.json()
        assert registry_payload["document_registry"]["registry_id"] == "NOVATECH_DOCUMENT_REGISTRY_V1"
        assert registry_payload["compliance_registry"]["standard_protocol"]["name"] == "AfriCPPT"
        assert (
            registry_payload["compliance_registry"]["linked_surfaces"]["policy_registry"]["api_surface"]
            == "/v1/novatech/documentation/policy"
        )

        policy = client.get("/v1/novatech/documentation/policy", headers=headers)
        assert policy.status_code == 200
        assert policy.json()["summary"]["policy_count"] >= 1

        certification = client.get("/v1/novatech/documentation/certification", headers=headers)
        assert certification.status_code == 200
        assert certification.json()["summary"]["classification"]

        trust = client.get("/v1/novatech/documentation/trust", headers=headers)
        assert trust.status_code == 200
        assert trust.json()["summary"]["member_count"] >= 0

        assurance = client.get("/v1/novatech/documentation/assurance", headers=headers)
        assert assurance.status_code == 200
        assert assurance.json()["summary"]["assurance_status"]

        marketplace = client.get("/v1/novatech/documentation/marketplace", headers=headers)
        assert marketplace.status_code == 200
        assert marketplace.json()["summary"]["service_count"] >= 4

        onboarding = client.get("/v1/novatech/documentation/onboarding", headers=headers)
        assert onboarding.status_code == 200
        assert onboarding.json()["summary"]["phase_count"] >= 5

        organizations = client.get("/v1/novatech/documentation/organizations", headers=headers)
        assert organizations.status_code == 200
        organizations_payload = organizations.json()
        assert organizations_payload["organization_governance"]["directory_surface"] == "/v1/novatech/organizations"
        assert organizations_payload["public_verification"]["documentation_portal_surface"] == "/public/documentation/portal"

        organization_detail = client.get("/v1/novatech/documentation/organizations/org-nova", headers=headers)
        assert organization_detail.status_code == 200
        organization_detail_payload = organization_detail.json()
        assert organization_detail_payload["organization_governance"]["detail_surface"].endswith("/org-nova")
        assert organization_detail_payload["certification_issuance"]["issue_surface"] == "/v1/novatech/documentation/certification/issue"

        public_portal = client.get("/public/documentation/portal")
        assert public_portal.status_code == 200
        assert "NovaTech Documentation Compliance Portal" in public_portal.text
        assert "/public/verify/portal" in public_portal.text

        public_verification = client.get("/public/documentation/org-nova")
        assert public_verification.status_code == 200
        public_verification_payload = public_verification.json()
        assert public_verification_payload["public_verification"]["portal_surface"] == "/public/verify/portal"
        assert public_verification_payload["organization_governance"]["directory_surface"] == "/v1/novatech/organizations"

        intranet = client.get("/v1/novatech/intranet/status", headers=headers)
        assert intranet.status_code == 200
        dashboards = intranet.json()["dashboards"]
        assert dashboards["novatech_documentation_status"] == "/v1/novatech/documentation/status"
        assert dashboards["novatech_documentation_policy"] == "/v1/novatech/documentation/policy"
        assert dashboards["novatech_documentation_assurance"] == "/v1/novatech/documentation/assurance"
        assert dashboards["novatech_documentation_organizations"] == "/v1/novatech/documentation/organizations"
        assert dashboards["public_documentation"] == "/public/documentation/portal"
    finally:
        control_plane._STORE = original_control_store
        persistence._DEFAULT_STORE = original_default_store


def test_documentation_training_records_persist_and_show_summary(tmp_path) -> None:
    store = PlatformStore(tmp_path / "documentation-training.sqlite3")
    original_control_store = control_plane._STORE
    original_default_store = persistence._DEFAULT_STORE
    control_plane._STORE = store
    persistence._DEFAULT_STORE = store
    try:
        client = TestClient(app)
        headers = _auth_headers(role="DEVELOPER", user_id="developer-1")

        response = client.post(
            "/v1/novatech/documentation/training/record",
            headers=headers,
            json={
                "organization_id": "org-nova",
                "manual_id": "NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2",
                "manual_version": "2.0",
                "role": "operator",
                "trainee_user_id": "operator-42",
                "trainer_user_id": "training-admin",
                "completion_status": "completed",
                "assessment_score": 97,
                "evidence_count": 3,
                "notes": ["Read the manual", "Reviewed compliance flow"],
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "recorded"
        assert payload["record"]["trainee_user_id"] == "operator-42"
        assert payload["record"]["acknowledgement_hash"]

        training = client.get("/v1/novatech/documentation/training", headers=headers)
        assert training.status_code == 200
        training_payload = training.json()
        assert training_payload["training_summary"]["count"] == 1
        assert training_payload["training_summary"]["completion_rate"] == 100.0
        assert training_payload["training_records"][0]["manual_id"] == "NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2"
        assert training_payload["summary"]["latest_manual_id"] == "NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2"
    finally:
        control_plane._STORE = original_control_store
        persistence._DEFAULT_STORE = original_default_store


def test_documentation_certification_issue_links_public_verification_and_tenant_governance(tmp_path) -> None:
    store = PlatformStore(tmp_path / "documentation-certification-issue.sqlite3")
    original_control_store = control_plane._STORE
    original_default_store = persistence._DEFAULT_STORE
    control_plane._STORE = store
    persistence._DEFAULT_STORE = store
    try:
        client = TestClient(app)
        headers = _auth_headers(role="VERIFIER", user_id="verifier-1")

        response = client.post(
            "/v1/novatech/documentation/certification/issue",
            headers=headers,
            json={
                "organization_id": "org-nova",
                "certification_type": "DOCUMENTATION_COMPLIANCE_CERTIFICATION",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "issued"
        assert payload["certification_issuance"]["summary"]["certification_type"] == "DOCUMENTATION_COMPLIANCE_CERTIFICATION"
        assert payload["organization_governance"]["directory_surface"] == "/v1/novatech/organizations"
        assert payload["public_verification"]["documentation_portal_surface"] == "/public/documentation/portal"
    finally:
        control_plane._STORE = original_control_store
        persistence._DEFAULT_STORE = original_default_store
