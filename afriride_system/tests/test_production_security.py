from __future__ import annotations

import base64
import json

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from afriride_system.api.auth import (
    IdentityRecord,
    IdentityStore,
    JWTService,
    build_auth_router,
    password_hash,
)
from afriride_system.api.main import app
from afriride_system.api.runtime_security import assert_secure_startup, internal_qa_routes_enabled


def _configured_jwt() -> JWTService:
    return JWTService("a" * 48, issuer="https://identity.novaride.test", audience="novaride-test")


def _rewrite_claim(token: str, name: str, value: object) -> str:
    header, payload, signature = token.split(".")
    decoded = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    decoded[name] = value
    changed = base64.urlsafe_b64encode(json.dumps(decoded).encode()).rstrip(b"=").decode()
    return f"{header}.{changed}.{signature}"


def test_mounted_app_rejects_anonymous_and_privileged_token_minting() -> None:
    client = TestClient(app)
    assert client.post("/auth/token", json={}).status_code == 401
    assert client.post("/auth/token", json={"user_id": "attacker", "role": "ADMIN"}).status_code == 403
    assert client.post("/auth/token", json={"identifier": "unknown", "password": "wrong"}).status_code == 401


@pytest.mark.parametrize("path", ["/auth/login", "/novaid/profile", "/novapay/wallet"])
def test_internal_qa_contracts_are_not_anonymously_reachable(path: str) -> None:
    response = TestClient(app).request("POST" if path == "/auth/login" else "GET", path)
    assert response.status_code in {401, 403, 404}
    assert "qa-mock-token" not in response.text
    assert '"mocked":true' not in response.text


def test_unknown_route_fails_closed_before_routing() -> None:
    assert TestClient(app).get("/new-unregistered-sensitive-route").status_code == 401


def test_every_mounted_http_route_has_complete_authorization_metadata() -> None:
    from afriride_system.api.auth import authorization_policy

    routes = [route for route in app.routes if isinstance(route, APIRoute)]
    assert routes
    for route in routes:
        for method in route.methods or set():
            policy = authorization_policy(method, route.path)
            assert isinstance(policy["public"], bool)
            assert policy["authentication_required"] is not policy["public"]
            if not policy["public"]:
                assert policy["allowed_roles"], f"missing roles for {method} {route.path}"


def test_identity_authority_rejects_invalid_disabled_and_membership_accounts() -> None:
    records = {
        "valid": IdentityRecord("rider-1", password_hash("correct", salt="1" * 32), "CUSTOMER", "tenant-1"),
        "disabled": IdentityRecord("rider-2", password_hash("correct", salt="2" * 32), "CUSTOMER", "tenant-1", status="DISABLED"),
        "detached": IdentityRecord("rider-3", password_hash("correct", salt="3" * 32), "CUSTOMER", "tenant-1", membership_status="REVOKED"),
    }
    store = IdentityStore(records)
    assert store.authenticate("valid", "correct").role == "CUSTOMER"
    for identifier, password, error in (
        ("unknown", "correct", "invalid_credentials"),
        ("valid", "wrong", "invalid_credentials"),
        ("disabled", "correct", "account_disabled"),
        ("detached", "correct", "tenant_membership_invalid"),
    ):
        with pytest.raises(ValueError, match=error):
            store.authenticate(identifier, password)


def test_authenticated_identity_receives_only_server_resolved_claims() -> None:
    jwt = _configured_jwt()
    store = IdentityStore({
        "rider@example.test": IdentityRecord(
            "rider-1", password_hash("correct", salt="4" * 32), "CUSTOMER", "tenant-1"
        )
    })
    isolated = FastAPI()
    isolated.include_router(build_auth_router(jwt, store))
    response = TestClient(isolated).post(
        "/auth/token", json={"identifier": "rider@example.test", "password": "correct"}
    )
    assert response.status_code == 200
    claims = jwt.verify_token(response.json()["token"])
    assert (claims.sub, claims.role, claims.tenant_id) == ("rider-1", "CUSTOMER", "tenant-1")


@pytest.mark.parametrize(
    "authorization",
    ["", "Bearer", "Basic abc", "Bearer malformed", "Bearer unsigned.payload"],
)
def test_malformed_or_missing_authorization_is_rejected(authorization: str) -> None:
    headers = {"Authorization": authorization} if authorization else {}
    assert TestClient(app).get("/system/health", headers=headers).status_code == 401


def test_tokens_enforce_signature_issuer_audience_time_and_revocation() -> None:
    jwt = _configured_jwt()
    token = jwt.create_token("rider-1", "CUSTOMER", tenant_id="tenant-1", issued_at=1_000)
    claims = jwt.verify_token(token, now=1_001)
    assert claims.role == "CUSTOMER"
    assert claims.tenant_id == "tenant-1"
    for changed, error in (
        (_rewrite_claim(token, "iss", "wrong"), "invalid_signature"),
        (_rewrite_claim(token, "aud", "wrong"), "invalid_signature"),
        (_rewrite_claim(token, "role", "ADMIN"), "invalid_signature"),
        (token + "x", "invalid_signature"),
    ):
        with pytest.raises(ValueError, match=error):
            jwt.verify_token(changed, now=1_001)
    future = jwt.create_token("rider-1", "CUSTOMER", issued_at=2_000)
    with pytest.raises(ValueError, match="token_not_yet_valid"):
        jwt.verify_token(future, now=1_000)
    with pytest.raises(ValueError, match="token_expired"):
        jwt.verify_token(token, now=2_000)
    jwt.sessions.revoke(claims.session_id)
    with pytest.raises(ValueError, match="session_revoked"):
        jwt.verify_token(token, now=1_001)


def test_wrong_issuer_and_audience_fail_even_with_valid_signature() -> None:
    issuer_token = JWTService("a" * 48, issuer="wrong", audience="novaride-test").create_token("rider-1", "CUSTOMER")
    audience_token = JWTService("a" * 48, issuer="https://identity.novaride.test", audience="wrong").create_token("rider-1", "CUSTOMER")
    verifier = _configured_jwt()
    with pytest.raises(ValueError, match="invalid_issuer"):
        verifier.verify_token(issuer_token)
    with pytest.raises(ValueError, match="invalid_audience"):
        verifier.verify_token(audience_token)


def test_production_startup_rejects_qa_and_incomplete_security_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AFRIRIDE_ENV", "production")
    monkeypatch.setenv("ENABLE_INTERNAL_QA_ROUTES", "true")
    with pytest.raises(RuntimeError, match="internal_qa_routes_forbidden"):
        internal_qa_routes_enabled()
    with pytest.raises(RuntimeError, match="insecure_production_configuration"):
        assert_secure_startup()
