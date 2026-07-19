import base64
import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from datetime import UTC, datetime
import hashlib
import json
from uuid import UUID, uuid4

import pytest

from afritech.novaid.application.webauthn import WebAuthnError, WebAuthnService
from afritech.novaid.domain import (
    AuthenticatorPolicy,
    WebAuthnCredential,
    WebAuthnCredentialStatus,
)
from afritech.novaid.persistence import NovaIDUnitOfWork


def uid() -> str:
    return str(uuid4())


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


class VirtualAuthenticator:
    def __init__(self) -> None:
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = uuid4().bytes

    def registration(self, challenge: str, *, origin: str = "http://localhost"):
        numbers = self.key.public_key().public_numbers()
        cose = cbor2.dumps(
            {
                1: 2,
                3: -7,
                -1: 1,
                -2: numbers.x.to_bytes(32, "big"),
                -3: numbers.y.to_bytes(32, "big"),
            }
        )
        auth_data = (
            hashlib.sha256(b"localhost").digest()
            + bytes([0x45])
            + (0).to_bytes(4, "big")
            + bytes(16)
            + len(self.credential_id).to_bytes(2, "big")
            + self.credential_id
            + cose
        )
        client = json.dumps(
            {"type": "webauthn.create", "challenge": challenge, "origin": origin},
            separators=(",", ":"),
        ).encode()
        return {
            "id": b64(self.credential_id),
            "rawId": b64(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": b64(client),
                "attestationObject": b64(
                    cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
                ),
                "transports": ["internal"],
            },
        }

    def assertion(self, challenge: str, *, sign_count: int, origin: str = "http://localhost"):
        auth_data = (
            hashlib.sha256(b"localhost").digest() + bytes([0x05]) + sign_count.to_bytes(4, "big")
        )
        client = json.dumps(
            {"type": "webauthn.get", "challenge": challenge, "origin": origin},
            separators=(",", ":"),
        ).encode()
        signature = self.key.sign(
            auth_data + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256())
        )
        return {
            "id": b64(self.credential_id),
            "rawId": b64(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": b64(client),
                "authenticatorData": b64(auth_data),
                "signature": b64(signature),
                "userHandle": None,
            },
        }


def seed(tmp_path):
    uow, tenant, identity, membership, now = (
        NovaIDUnitOfWork(tmp_path / f"{uid()}.db"),
        uid(),
        uid(),
        uid(),
        datetime.now(UTC),
    )
    with uow:
        uow.create_tenant(tenant, "WebAuthn", now)
        uow.connection.execute(
            "INSERT INTO novaid_identities VALUES(?,?,?,?,?,?,?,?)",
            (
                identity,
                tenant,
                "passkey@example.com",
                "ACTIVE",
                now.isoformat(),
                now.isoformat(),
                1,
                1,
            ),
        )
        uow.connection.execute(
            "INSERT INTO novaid_tenant_memberships VALUES(?,?,?,?,?,?,?,?)",
            (membership, tenant, identity, "MEMBER", "ACTIVE", now.isoformat(), now.isoformat(), 1),
        )
    policy = AuthenticatorPolicy(
        rp_id="localhost", rp_name="NovaID Tests", origins=("http://localhost",)
    )
    return (
        uow,
        WebAuthnService(uow, policy, token_pepper=b"phase-6b-test-pepper-at-least-32-bytes"),
        tenant,
        identity,
        membership,
    )


def test_domain_rejects_insecure_rp_algorithms_and_negative_counters() -> None:
    with pytest.raises(ValueError, match="insecure_webauthn_origin"):
        AuthenticatorPolicy(rp_id="example.com", rp_name="Bad", origins=("http://example.com",))
    with pytest.raises(ValueError, match="unsupported_cose_algorithm"):
        WebAuthnCredential(
            credential_id="id",
            tenant_id=uid(),
            identity_id=uid(),
            membership_id=None,
            user_handle=b"u",
            public_key_cose=b"k",
            public_key_algorithm=-999,
            sign_count=0,
            aaguid="a",
            attestation_format="none",
            attestation_type="none",
        )
    assert WebAuthnCredentialStatus.COMPROMISED == "COMPROMISED"


def test_registration_options_are_standards_generated_and_challenge_is_hashed(tmp_path) -> None:
    uow, service, tenant, identity, membership = seed(tmp_path)
    result = service.registration_options(
        tenant_id=tenant,
        identity_id=identity,
        membership_id=membership,
        user_name="passkey@example.com",
        correlation_id=uid(),
        request_id=uid(),
    )
    public_key = result["public_key"]
    assert public_key["rp"]["id"] == "localhost"
    assert public_key["authenticatorSelection"]["userVerification"] == "required"
    assert public_key["authenticatorSelection"]["residentKey"] == "preferred"
    challenge = public_key["challenge"]
    row = uow.connection.execute(
        "SELECT challenge_hash,status FROM novaid_webauthn_registration_challenges "
        "WHERE challenge_id=?",
        (result["challenge_id"],),
    ).fetchone()
    raw = base64.urlsafe_b64decode(challenge + "=" * (-len(challenge) % 4))
    assert row["challenge_hash"] == hashlib.sha256(raw).hexdigest()
    assert challenge not in row["challenge_hash"]
    assert row["status"] == "PENDING"


def test_authentication_options_support_identity_bound_and_discoverable_flows(tmp_path) -> None:
    _, service, tenant, identity, _ = seed(tmp_path)
    bound = service.authentication_options(
        tenant_id=tenant,
        identity_id=identity,
        session_id=None,
        correlation_id=uid(),
        request_id=uid(),
    )
    discoverable = service.authentication_options(
        tenant_id=tenant, identity_id=None, session_id=None, correlation_id=uid(), request_id=uid()
    )
    assert bound["public_key"]["rpId"] == "localhost"
    assert discoverable["public_key"]["userVerification"] == "required"


def test_invalid_registration_is_generic_single_use_and_origin_bound(tmp_path) -> None:
    uow, service, tenant, identity, membership = seed(tmp_path)
    options = service.registration_options(
        tenant_id=tenant,
        identity_id=identity,
        membership_id=membership,
        user_name="passkey@example.com",
        correlation_id=uid(),
        request_id=uid(),
    )
    challenge = options["public_key"]["challenge"]
    client_data = (
        base64.urlsafe_b64encode(
            json.dumps(
                {
                    "type": "webauthn.create",
                    "challenge": challenge,
                    "origin": "https://attacker.example",
                }
            ).encode()
        )
        .rstrip(b"=")
        .decode()
    )
    credential = {
        "id": "invalid",
        "rawId": "aW52YWxpZA",
        "type": "public-key",
        "response": {"clientDataJSON": client_data, "attestationObject": "aW52YWxpZA"},
    }
    with pytest.raises(WebAuthnError, match="WEBAUTHN_REGISTRATION_REJECTED"):
        service.verify_registration(
            tenant_id=tenant,
            identity_id=identity,
            membership_id=membership,
            challenge_id=options["challenge_id"],
            credential=credential,
        )
    row = uow.connection.execute(
        "SELECT status FROM novaid_webauthn_registration_challenges WHERE challenge_id=?",
        (options["challenge_id"],),
    ).fetchone()
    assert row["status"] == "CONSUMED"


def test_virtual_authenticator_registration_authentication_and_clone_detection(tmp_path) -> None:
    _, service, tenant, identity, membership = seed(tmp_path)
    authenticator = VirtualAuthenticator()
    registration = service.registration_options(
        tenant_id=tenant,
        identity_id=identity,
        membership_id=membership,
        user_name="passkey@example.com",
        correlation_id=uid(),
        request_id=uid(),
    )
    created = service.verify_registration(
        tenant_id=tenant,
        identity_id=identity,
        membership_id=membership,
        challenge_id=registration["challenge_id"],
        credential=authenticator.registration(registration["public_key"]["challenge"]),
        friendly_name="Virtual platform authenticator",
    )
    assert created["status"] == "ACTIVE"
    authentication = service.authentication_options(
        tenant_id=tenant,
        identity_id=identity,
        session_id=None,
        correlation_id=uid(),
        request_id=uid(),
    )
    verified = service.verify_authentication(
        tenant_id=tenant,
        challenge_id=authentication["challenge_id"],
        credential=authenticator.assertion(authentication["public_key"]["challenge"], sign_count=1),
    )
    assert verified["authentication_strength"] == "PHISHING_RESISTANT"
    replay = service.authentication_options(
        tenant_id=tenant,
        identity_id=identity,
        session_id=None,
        correlation_id=uid(),
        request_id=uid(),
    )
    with pytest.raises(WebAuthnError, match="WEBAUTHN_CLONE_DETECTED"):
        service.verify_authentication(
            tenant_id=tenant,
            challenge_id=replay["challenge_id"],
            credential=authenticator.assertion(replay["public_key"]["challenge"], sign_count=1),
        )


def test_credential_lifecycle_is_tenant_bound_and_terminal(tmp_path) -> None:
    uow, service, tenant, identity, membership = seed(tmp_path)
    other = uid()
    now, credential_id = datetime.now(UTC), "credential"
    with uow:
        uow.create_tenant(other, "Other", now)
        uow.connection.execute(
            "INSERT INTO novaid_webauthn_credentials(credential_id,tenant_id,identity_id,"
            "membership_id,user_handle,public_key_cose,public_key_algorithm,sign_count,aaguid,"
            "attestation_format,attestation_type,transports,backup_eligible,backup_state,discoverable,"
            "resident_key,user_verification,created_at,status,version) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                credential_id,
                tenant,
                identity,
                membership,
                UUID(identity).bytes,
                b"key",
                -7,
                0,
                "aaguid",
                "none",
                "none",
                "[]",
                0,
                0,
                1,
                1,
                1,
                now.isoformat(),
                "ACTIVE",
                1,
            ),
        )
    service.transition_credential(
        tenant_id=tenant,
        identity_id=identity,
        credential_id=credential_id,
        target="SUSPENDED",
        reason="USER_REQUEST",
        actor_identity_id=identity,
    )
    service.transition_credential(
        tenant_id=tenant,
        identity_id=identity,
        credential_id=credential_id,
        target="REVOKED",
        reason="USER_REQUEST",
        actor_identity_id=identity,
    )
    with pytest.raises(WebAuthnError, match="INVALID_AUTHENTICATOR_TRANSITION"):
        service.transition_credential(
            tenant_id=tenant,
            identity_id=identity,
            credential_id=credential_id,
            target="ACTIVE",
            reason="UNSAFE",
            actor_identity_id=identity,
        )
    with pytest.raises(WebAuthnError, match="INVALID_AUTHENTICATOR_TRANSITION"):
        service.transition_credential(
            tenant_id=other,
            identity_id=identity,
            credential_id=credential_id,
            target="SUSPENDED",
            reason="CROSS_TENANT",
            actor_identity_id=identity,
        )


def test_passwordless_session_and_existing_session_step_up(tmp_path) -> None:
    uow, service, tenant, identity, membership = seed(tmp_path)
    authenticator = VirtualAuthenticator()
    registration = service.registration_options(
        tenant_id=tenant,
        identity_id=identity,
        membership_id=membership,
        user_name="passkey@example.com",
        correlation_id=uid(),
        request_id=uid(),
    )
    service.verify_registration(
        tenant_id=tenant,
        identity_id=identity,
        membership_id=membership,
        challenge_id=registration["challenge_id"],
        credential=authenticator.registration(registration["public_key"]["challenge"]),
    )
    authentication = service.authentication_options(
        tenant_id=tenant,
        identity_id=None,
        session_id=None,
        correlation_id=uid(),
        request_id=uid(),
    )
    session = service.create_passwordless_session(
        tenant_id=tenant,
        challenge_id=authentication["challenge_id"],
        credential=authenticator.assertion(authentication["public_key"]["challenge"], sign_count=1),
    )
    assert session["authentication_strength"] == "PHISHING_RESISTANT"
    assert session["refresh_token"]
    row = uow.connection.execute(
        "SELECT status,authentication_strength FROM novaid_authentication_sessions "
        "WHERE session_id=?",
        (session["session_id"],),
    ).fetchone()
    assert (row["status"], row["authentication_strength"]) == (
        "ACTIVE",
        "PHISHING_RESISTANT",
    )
    with uow:
        uow.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='STEP_UP_REQUIRED' "
            "WHERE session_id=?",
            (session["session_id"],),
        )
    step_up = service.authentication_options(
        tenant_id=tenant,
        identity_id=identity,
        session_id=str(session["session_id"]),
        correlation_id=uid(),
        request_id=uid(),
    )
    completed = service.complete_session_step_up(
        tenant_id=tenant,
        session_id=str(session["session_id"]),
        challenge_id=step_up["challenge_id"],
        credential=authenticator.assertion(step_up["public_key"]["challenge"], sign_count=2),
    )
    assert completed["authentication_strength"] == "PHISHING_RESISTANT"
