from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_operational_verification_api import build_novacodepro_operational_verification_router


def _headers(role: str) -> dict[str, str]:
    token = JWT.create_token("usr-test", role=role, organization_id="novatech")
    return {"Authorization": f"Bearer {token}"}


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_operational_verification_router())
    return TestClient(app)


def test_observer_can_read_and_developer_can_execute() -> None:
    client = _client()

    status = client.get("/v1/novacodepro/operational-verification/status", headers=_headers("OBSERVER"))
    assert status.status_code == 200
    assert status.json()["invariants"]["GA_ALLOWED"] is False

    program = client.post(
        "/v1/novacodepro/operational-verification/programs",
        headers=_headers("DEVELOPER"),
        json={"release_id": "rel-1"},
    )
    assert program.status_code == 200
    assert program.json()["status"] == "CONFIGURED"

    run = client.post(
        f"/v1/novacodepro/operational-verification/programs/{program.json()['id']}/execute",
        headers=_headers("DEVELOPER"),
    )
    assert run.status_code == 200
    assert run.json()["status"] == "EXECUTED"


def test_unauthorized_roles_rejected_and_sensitive_states_fail_closed() -> None:
    client = _client()

    denied = client.post("/v1/novacodepro/operational-verification/programs", headers=_headers("OBSERVER"), json={})
    assert denied.status_code == 403

    ga = client.get("/v1/novacodepro/operational-verification/ga/status", headers=_headers("OBSERVER"))
    pay = client.get("/v1/novacodepro/operational-verification/payments/status", headers=_headers("OBSERVER"))
    assert ga.json()["ga_allowed"] is False
    assert pay.json()["real_payments_enabled"] is False
