from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.afriride_mobile_release_api import build_afriride_mobile_release_router


def test_public_afriride_mobile_release_readiness_contract() -> None:
    app = FastAPI()
    app.include_router(build_afriride_mobile_release_router())
    client = TestClient(app)

    response = client.get("/public/afriride/mobile/release-readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "AFRIRIDE_MOBILE_RELEASE_READINESS_CONTRACT"
    assert payload["status"] == "PILOT_RELEASE_READY_STORE_PRODUCTION_BLOCKED"
    assert payload["production_claim_allowed"] is False
    assert "dependency_audit_requires_expo_react_native_upgrade_review" in payload["production_blockers"]
    assert len(payload["readiness_hash"]) == 64
    assert {app_manifest["app_id"] for app_manifest in payload["apps"]} == {
        "afriride-rider",
        "afriride-driver",
        "afriride-operator-dashboard",
    }
    assert payload["blocking_findings"] == []
    assert (
        payload["authority_boundary"]
        == "mobile_apps_are_interface_only_replay_proof_and_server_protocol_remain_authority"
    )
