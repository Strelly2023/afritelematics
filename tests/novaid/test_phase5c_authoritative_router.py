from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.novaid_api import build_novaid_router
from afritech.novaid.api import build_durable_authentication_router
from afritech.novaid.application import (
    DurableAuthenticationService,
    PasswordLifecycleService,
    SessionAdministrationService,
)
from afritech.novaid.persistence import NovaIDUnitOfWork
from afritech.novaid.revocation import ProcessLocalRevocationStore
from afritech.novaid.runtime import build_default_durable_router
from afritech.novaid.tokens import AccessTokenService
from afritech.novaid.observability import NovaIDMetrics, NovaIDTracer


def uid() -> str:
    return str(uuid4())


def test_authoritative_mounted_api_lifecycle_and_route_ownership(tmp_path) -> None:
    tenant = uid()
    store = NovaIDUnitOfWork(tmp_path / "mounted.db")
    with store:
        store.create_tenant(tenant, "Mounted", datetime.now(UTC))
    revocations = ProcessLocalRevocationStore()
    auth = DurableAuthenticationService(store, pepper=b"mounted-auth-pepper" * 3)
    tokens = AccessTokenService(
        store,
        revocations,
        signing_key=b"mounted-signing-key-for-tests-0001",
        issuer="mounted",
        audience="mounted-clients",
    )
    router = build_durable_authentication_router(
        auth,
        tokens=tokens,
        passwords=PasswordLifecycleService(store, revocations, pepper=b"mounted-reset" * 3),
        sessions=SessionAdministrationService(store, revocations),
    )
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    headers = {
        "x-tenant-id": tenant,
        "idempotency-key": "register",
        "x-correlation-id": uid(),
        "x-request-id": uid(),
    }
    registered = client.post(
        "/v1/novaid/register",
        headers=headers,
        json={"email": "person@example.com", "password": "the original strong password"},
    ).json()
    assert (
        client.post(
            "/v1/novaid/verify",
            headers=headers,
            json={
                "identity_id": registered["identity_id"],
                "challenge_id": registered["challenge_id"],
                "code": registered["verification_code"],
            },
        ).status_code
        == 204
    )
    login = client.post(
        "/v1/novaid/authenticate",
        headers=headers,
        json={"email": "person@example.com", "password": "the original strong password"},
    ).json()
    store.connection.execute(
        "UPDATE novaid_otp_challenges SET created_at=? WHERE challenge_id=?",
        ((datetime.now(UTC).replace(year=2020)).isoformat(), login["challenge_id"]),
    )
    resent = client.post(
        "/v1/novaid/mfa/challenge",
        headers=headers,
        json={"session_id": login["session_id"]},
    ).json()
    token_result = client.post(
        "/v1/novaid/mfa/verify",
        headers=headers,
        json={
            "session_id": login["session_id"],
            "challenge_id": resent["challenge_id"],
            "code": resent["mfa_code"],
        },
    ).json()
    protected = {**headers, "authorization": f"Bearer {token_result['access_token']}"}
    assert (
        client.get("/v1/novaid/me", headers=protected).json()["identity_id"]
        == registered["identity_id"]
    )
    assert len(client.get("/v1/novaid/sessions", headers=protected).json()) == 1
    assert client.post("/v1/novaid/logout", headers=protected).json() == {"logged_out": True}
    assert client.get("/v1/novaid/me", headers=protected).status_code == 401
    keys = [
        (route.path, next(iter(route.methods)))
        for route in app.routes
        if getattr(route, "methods", None)
    ]
    assert not [item for item, count in Counter(keys).items() if count > 1]


def test_main_application_declares_authoritative_durable_mount() -> None:
    app_source = Path("afritech/api/app.py").read_text()
    assert "app.include_router(build_novaid_router())" in app_source
    assert "app.include_router(build_default_durable_router())" in app_source


def test_main_application_starts_and_publishes_authoritative_openapi(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("NOVATECH_RUNTIME_CONTROL_SQLITE_PATH", str(tmp_path / "runtime.db"))
    monkeypatch.setenv("NOVATECH_EVIDENCE_ROOT", str(tmp_path / "evidence"))
    monkeypatch.setenv("NOVAID_DURABLE_DB_PATH", str(tmp_path / "novaid.db"))
    from afritech.api.app import app

    with pytest.warns(UserWarning):
        paths = app.openapi()["paths"]
    assert "/v1/novaid/register" in paths
    assert "/v1/novaid/mfa/challenge" in paths
    assert "/v1/novaid/token/refresh" in paths
    assert "/v1/novaid/me" in paths


def test_legacy_router_has_no_authoritative_auth_or_session_collision() -> None:
    legacy = build_novaid_router()
    durable = build_default_durable_router()
    pairs = [
        (route.path, method)
        for route in [*legacy.routes, *durable.routes]
        for method in getattr(route, "methods", set())
        if route.path.startswith("/v1/novaid")
    ]
    assert ("/v1/novaid/register", "POST") in pairs
    assert ("/v1/novaid/me", "GET") in pairs
    assert ("/v1/novaid/sessions", "GET") in pairs
    assert ("/v1/novaid/legacy/sessions", "GET") in pairs
    assert ("/v1/novaid/legacy/auth", "POST") in pairs
    assert len(pairs) == len(set(pairs))


def test_observability_rejects_identity_labels_and_records_secret_free_spans() -> None:
    metrics = NovaIDMetrics()
    metrics.increment("novaid_authentication_attempts_total", outcome="success")
    with pytest.raises(ValueError, match="high_cardinality_metric_labels"):
        metrics.increment("unsafe", identity_id="identity-secret")
    tracer = NovaIDTracer()
    with tracer.span("novaid.authenticate", {"operation": "authenticate"}):
        pass
    assert tracer.spans[0].attributes == {"operation": "authenticate"}
    assert "password" not in repr(tracer.spans)
