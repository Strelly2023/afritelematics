from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.novaid.api import build_durable_authentication_router
from afritech.novaid.application import DurableAuthenticationService
from afritech.novaid.persistence import NovaIDUnitOfWork


def test_registration_verification_authentication_and_mfa_api(tmp_path) -> None:
    tenant = str(uuid4())
    store = NovaIDUnitOfWork(tmp_path / "api.db")
    with store:
        store.create_tenant(tenant, "API tenant", datetime.now(UTC))
    service = DurableAuthenticationService(store, pepper=b"api-test-pepper" * 3)
    app = FastAPI()
    app.include_router(build_durable_authentication_router(service))
    client = TestClient(app)
    headers = {
        "x-tenant-id": tenant,
        "idempotency-key": "idem-1",
        "x-correlation-id": str(uuid4()),
        "x-request-id": str(uuid4()),
    }
    registration = client.post(
        "/v1/novaid/register",
        headers=headers,
        json={"email": "person@example.com", "password": "a strong registration password"},
    )
    assert registration.status_code == 202
    registered = registration.json()
    verified = client.post(
        "/v1/novaid/verify",
        headers=headers,
        json={
            "identity_id": registered["identity_id"],
            "challenge_id": registered["challenge_id"],
            "code": registered["verification_code"],
        },
    )
    assert verified.status_code == 204
    login = client.post(
        "/v1/novaid/authenticate",
        headers=headers,
        json={"email": "person@example.com", "password": "a strong registration password"},
    )
    assert login.json()["outcome"] == "MFA_REQUIRED"
    challenge = login.json()
    mfa = client.post(
        "/v1/novaid/mfa/verify",
        headers=headers,
        json={
            "session_id": challenge["session_id"],
            "challenge_id": challenge["challenge_id"],
            "code": challenge["mfa_code"],
        },
    )
    assert mfa.status_code == 200
    assert "refresh_token" in mfa.json()


def test_api_authentication_failure_is_generic(tmp_path) -> None:
    tenant = str(uuid4())
    store = NovaIDUnitOfWork(tmp_path / "generic.db")
    with store:
        store.create_tenant(tenant, "API tenant", datetime.now(UTC))
    app = FastAPI()
    app.include_router(
        build_durable_authentication_router(
            DurableAuthenticationService(store, pepper=b"api-test-pepper" * 3)
        )
    )
    response = TestClient(app).post(
        "/v1/novaid/authenticate",
        headers={
            "x-tenant-id": tenant,
            "x-correlation-id": str(uuid4()),
            "x-request-id": str(uuid4()),
        },
        json={"email": "unknown@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTHENTICATION_DENIED"
