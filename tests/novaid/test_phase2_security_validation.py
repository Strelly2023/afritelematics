from __future__ import annotations

import base64
import hashlib
import hmac
import json

import pytest

from afritech.novaid.revocation import ProcessLocalRevocationStore
from afritech.novaid.tokens import AccessTokenError, AccessTokenService
from tests.novaid.test_phase4_access_tokens import active_runtime


OLD_KEY = b"phase2-old-signing-key-at-least-32-bytes"
NEW_KEY = b"phase2-new-signing-key-at-least-32-bytes"


def _decode(part: str):
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


def _encode(value: dict[str, object]) -> str:
    return base64.urlsafe_b64encode(
        json.dumps(value, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()


def _service(store, *, active: str, keys: dict[str, bytes]) -> AccessTokenService:
    return AccessTokenService(
        store,
        ProcessLocalRevocationStore(),
        signing_keys=keys,
        active_key_id=active,
        issuer="phase2-security",
        audience="phase2-clients",
    )


def _resign(token: str, key: bytes, *, header=None, payload=None) -> str:
    encoded_header, encoded_payload, _ = token.split(".")
    if header is not None:
        encoded_header = _encode(header)
    if payload is not None:
        encoded_payload = _encode(payload)
    signing_input = f"{encoded_header}.{encoded_payload}"
    signature = hmac.new(key, signing_input.encode(), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{signing_input}.{encoded_signature}"


def test_rotation_overlap_and_retirement_are_key_id_bound(tmp_path) -> None:
    tenant, store, registration, login = active_runtime(tmp_path)
    old_service = _service(store, active="2026-q2", keys={"2026-q2": OLD_KEY})
    old_token = old_service.issue(
        tenant,
        login["session_id"],
        registration["membership_id"],
    )
    assert _decode(old_token.split(".")[0])["kid"] == "2026-q2"

    overlap = _service(
        store,
        active="2026-q3",
        keys={"2026-q2": OLD_KEY, "2026-q3": NEW_KEY},
    )
    assert overlap.validate(old_token, expected_tenant=tenant)["tenant_id"] == tenant
    new_token = overlap.issue(
        tenant,
        login["session_id"],
        registration["membership_id"],
    )
    assert _decode(new_token.split(".")[0])["kid"] == "2026-q3"

    retired = _service(store, active="2026-q3", keys={"2026-q3": NEW_KEY})
    assert retired.validate(new_token, expected_tenant=tenant)["tenant_id"] == tenant
    with pytest.raises(AccessTokenError, match="INVALID_ACCESS_TOKEN"):
        retired.validate(old_token, expected_tenant=tenant)


@pytest.mark.parametrize(
    "mutator",
    (
        lambda token: token + ".extra",
        lambda token: token.rsplit(".", 1)[0] + ".***",
        lambda token: "A" * 16_385,
    ),
)
def test_malformed_token_inputs_fail_closed(tmp_path, mutator) -> None:
    tenant, store, registration, login = active_runtime(tmp_path)
    service = _service(store, active="2026-q3", keys={"2026-q3": NEW_KEY})
    token = service.issue(tenant, login["session_id"], registration["membership_id"])

    with pytest.raises(AccessTokenError, match="INVALID_ACCESS_TOKEN"):
        service.validate(mutator(token), expected_tenant=tenant)


def test_algorithm_key_id_and_claim_type_attacks_fail_closed(tmp_path) -> None:
    tenant, store, registration, login = active_runtime(tmp_path)
    service = _service(store, active="2026-q3", keys={"2026-q3": NEW_KEY})
    token = service.issue(tenant, login["session_id"], registration["membership_id"])
    header = _decode(token.split(".")[0])
    payload = _decode(token.split(".")[1])

    attacks = (
        _resign(token, NEW_KEY, header={**header, "alg": "none"}),
        _resign(token, NEW_KEY, header={**header, "kid": "attacker"}),
        _resign(token, NEW_KEY, payload={**payload, "exp": "never"}),
        _resign(token, NEW_KEY, payload={**payload, "token_version": 999}),
    )
    for attack in attacks:
        with pytest.raises(AccessTokenError, match="INVALID_ACCESS_TOKEN"):
            service.validate(attack, expected_tenant=tenant)


def test_cross_tenant_signed_token_is_still_denied(tmp_path) -> None:
    tenant, store, registration, login = active_runtime(tmp_path)
    service = _service(store, active="2026-q3", keys={"2026-q3": NEW_KEY})
    token = service.issue(tenant, login["session_id"], registration["membership_id"])

    with pytest.raises(AccessTokenError, match="TENANT_ACCESS_DENIED"):
        service.validate(token, expected_tenant="00000000-0000-0000-0000-000000000000")
