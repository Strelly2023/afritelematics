from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def _client(tmp_path: Path) -> TestClient:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_platform_router(platform))
    return TestClient(app)


def _headers(role: str, user_id: str = "usr_djuma") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def test_eros_manifest_and_architecture_framework_include_resilience_models(tmp_path: Path) -> None:
    service = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "platform.sqlite3"))

    eros = service.eros_manifest()
    framework = service.architecture_framework()

    assert eros["name"] == "NovaDigitalTwin Enterprise Resilience Operating System"
    assert len(eros["core_views"]) == 6
    assert eros["lifecycle"][-1] == "Optimize"
    assert "Optimization Engine" in eros["runtime_services"]
    assert "nerm" in framework["models"]
    assert "Simulation confidence" not in framework["models"]["ndtm"]["capabilities"]
    assert "Replay support" in framework["models"]["ndtm"]["capabilities"]


def test_eros_api_supports_registry_observation_simulation_and_recovery(tmp_path: Path) -> None:
    client = _client(tmp_path)

    eros_response = client.get("/v1/novacodepro/eros", headers=_headers("OBSERVER"))
    assert eros_response.status_code == 200
    assert eros_response.json()["name"] == "NovaDigitalTwin Enterprise Resilience Operating System"

    create_response = client.post(
        "/v1/novacodepro/digital-twins",
        headers=_headers("DEVELOPER"),
        json={
            "id": "twin-payments-core",
            "name": "Payments Core Twin",
            "type": "SERVICE",
            "owner": "Payments Engineering",
            "region": "Australia",
            "summary": "Payments runtime twin.",
            "sources": ["Prometheus", "Knowledge Graph"],
            "metrics": {"availability": 0.998, "risk_score": 22, "recovery_minutes": 12},
            "relationships": [
                {
                    "source": "twin-payments-core",
                    "target": "Primary Ledger",
                    "type": "DEPENDS_ON",
                    "criticality": "CRITICAL",
                    "weight": 4.8,
                    "confidence": 0.97,
                }
            ],
        },
    )
    assert create_response.status_code == 200

    registry_response = client.get("/v1/novacodepro/digital-twins", headers=_headers("OBSERVER"))
    assert registry_response.status_code == 200
    assert any(item["id"] == "twin-payments-core" for item in registry_response.json())

    summary_response = client.get("/v1/novacodepro/digital-twins/twin-payments-core/summary", headers=_headers("OBSERVER"))
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["scores"]["enterprise_resilience_score"] > 0

    observe_response = client.post(
        "/v1/novacodepro/digital-twins/twin-payments-core/observe",
        headers=_headers("DEVELOPER"),
        json={
            "observed_state": "DEGRADED",
            "observed_detail": "Latency increased in the payment path.",
            "observed_evidence": ["prometheus"],
            "metrics": {"availability": 0.984, "risk_score": 41, "recovery_minutes": 18},
            "status": "degraded",
        },
    )
    assert observe_response.status_code == 200
    assert observe_response.json()["twin"]["observed_state"] == "DEGRADED"

    simulation_response = client.post(
        "/v1/novacodepro/digital-twins/twin-payments-core/simulate",
        headers=_headers("DEVELOPER"),
        json={
            "scenario": "postgres_failure",
            "root_failure": "Primary Ledger",
            "predicted_recovery_minutes": 25,
            "recommended_actions": ["activate replica", "freeze releases"],
        },
    )
    assert simulation_response.status_code == 200
    simulation = simulation_response.json()
    assert simulation["scenario"] == "postgres_failure"
    assert simulation["risk_after"] <= simulation["risk_before"]
    assert simulation["affected_entities"]

    recovery_plan_response = client.post(
        "/v1/novacodepro/digital-twins/twin-payments-core/recovery-plans",
        headers=_headers("DEVELOPER"),
        json={
            "scenario": "postgres_failure",
            "workflow_id": "recovery-plan-payments-core",
            "expected_rto": "15m",
            "expected_rpo": "5m",
            "blast_radius": 3,
        },
    )
    assert recovery_plan_response.status_code == 200
    assert recovery_plan_response.json()["steps"][0] == "verify_failure"

    recovery_response = client.post(
        "/v1/novacodepro/digital-twins/twin-payments-core/recover",
        headers=_headers("DEVELOPER"),
        json={
            "scenario": "postgres_failure",
            "root_failure": "Primary Ledger",
            "predicted_recovery_minutes": 18,
            "risk_after": 19,
            "summary": "Validated recovery through the replica path.",
            "recovery_plan": recovery_plan_response.json(),
            "evidence": {
                "id": "evidence-recovery-payments-core",
                "type": "recovery_evidence",
                "twin_id": "twin-payments-core",
                "status": "VERIFIED",
                "summary": "Recovery validated in the portal.",
            },
            "approved_detail": "Recovery approved by governance.",
            "recovered_detail": "Twin returned to healthy state.",
        },
    )
    assert recovery_response.status_code == 200
    body = recovery_response.json()
    assert body["status"] == "VERIFIED"
    assert body["twin"]["recovered_state"] == "HEALTHY"
    assert body["evidence"]["status"] == "VERIFIED"

    evidence_response = client.get("/v1/novacodepro/digital-twins/twin-payments-core/evidence", headers=_headers("OBSERVER"))
    assert evidence_response.status_code == 200
    assert evidence_response.json()
