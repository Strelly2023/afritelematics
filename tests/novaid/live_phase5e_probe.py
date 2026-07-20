"""Manual two-process local certificate probe; not collected as a unit test."""

from datetime import UTC, datetime
import os
from uuid import uuid4

import httpx
import psycopg


def uid() -> str:
    return str(uuid4())


dsn = os.environ["NOVAID_TEST_DATABASE_URL"]
tenant, now = uid(), datetime.now(UTC)
with psycopg.connect(dsn) as connection:
    connection.execute(
        "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at) "
        "VALUES(%s,'Two Process','ACTIVE',%s,%s)",
        (tenant, now, now),
    )

a, b = (
    httpx.Client(base_url="http://127.0.0.1:58101"),
    httpx.Client(base_url="http://127.0.0.1:58102"),
)
headers = {
    "x-tenant-id": tenant,
    "idempotency-key": "two-process",
    "x-correlation-id": uid(),
    "x-request-id": uid(),
}
assert a.get("/health/ready").status_code == 200
assert b.get("/health/ready").status_code == 200
registered_response = a.post(
    "/v1/novaid/register",
    headers=headers,
    json={"email": "two-process@example.com", "password": "a strong two process password"},
)
assert registered_response.status_code == 202, registered_response.text
registered = registered_response.json()
assert (
    a.post(
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
login = a.post(
    "/v1/novaid/authenticate",
    headers=headers,
    json={"email": "two-process@example.com", "password": "a strong two process password"},
).json()
issued_response = a.post(
    "/v1/novaid/mfa/verify",
    headers=headers,
    json={
        "session_id": login["session_id"],
        "challenge_id": login["challenge_id"],
        "code": login["mfa_code"],
    },
)
assert issued_response.status_code == 200, issued_response.text
issued = issued_response.json()
protected = {**headers, "authorization": f"Bearer {issued['access_token']}"}
assert b.get("/v1/novaid/me", headers=protected).status_code == 200
rotated = b.post(
    "/v1/novaid/token/refresh",
    headers=headers,
    json={"refresh_token": issued["refresh_token"]},
)
assert rotated.status_code == 200, rotated.text
assert a.post("/v1/novaid/logout", headers=protected).status_code == 200
assert b.get("/v1/novaid/me", headers=protected).status_code == 401
rejected_refresh = b.post(
    "/v1/novaid/token/refresh",
    headers=headers,
    json={"refresh_token": rotated.json()["refresh_token"]},
)
assert rejected_refresh.status_code == 401
print("LOCAL_TWO_PROCESS_VERIFIED ports=58101,58102 access_rejected=401 refresh_rejected=401")
