"""Standards-compliant WebAuthn ceremonies backed by durable NovaID state."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import secrets
from uuid import UUID, uuid4

try:  # pragma: no cover - optional dependency in runtime images
    import cbor2
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal runtime images
    cbor2 = None

try:  # pragma: no cover - optional dependency in runtime images
    from webauthn import (
        generate_authentication_options,
        generate_registration_options,
        options_to_json,
        verify_authentication_response,
        verify_registration_response,
    )
    from webauthn.helpers.cose import COSEAlgorithmIdentifier
    from webauthn.helpers.structs import (
        AttestationConveyancePreference,
        AuthenticatorSelectionCriteria,
        PublicKeyCredentialDescriptor,
        ResidentKeyRequirement,
        UserVerificationRequirement,
    )

    WEBAUTHN_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal runtime images
    generate_authentication_options = None
    generate_registration_options = None
    options_to_json = None
    verify_authentication_response = None
    verify_registration_response = None
    COSEAlgorithmIdentifier = None
    AttestationConveyancePreference = None
    AuthenticatorSelectionCriteria = None
    PublicKeyCredentialDescriptor = None
    ResidentKeyRequirement = None
    UserVerificationRequirement = None
    WEBAUTHN_AVAILABLE = False

from ..domain import AuthenticatorPolicy
from ..observability import NovaIDMetrics, NovaIDTracer
from ..webauthn_coordination import RedisWebAuthnChallengeCoordinator


class WebAuthnError(ValueError):
    pass


def _id() -> str:
    return str(uuid4())


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _challenge_from_response(credential: dict[str, object]) -> bytes:
    try:
        response = credential["response"]
        encoded = response["clientDataJSON"]  # type: ignore[index]
        client_data = json.loads(_decode(str(encoded)))
        return _decode(str(client_data["challenge"]))
    except Exception as exc:
        raise WebAuthnError("INVALID_WEBAUTHN_RESPONSE") from exc


class WebAuthnService:
    def __init__(
        self,
        uow,
        policy: AuthenticatorPolicy,
        *,
        metrics: NovaIDMetrics | None = None,
        tracer: NovaIDTracer | None = None,
        token_pepper: bytes | None = None,
        coordinator: RedisWebAuthnChallengeCoordinator | None = None,
        distributed_outbox=None,
    ) -> None:
        self.uow, self.policy = uow, policy
        self.metrics, self.tracer = metrics or NovaIDMetrics(), tracer or NovaIDTracer()
        self.token_pepper = token_pepper
        self.coordinator = coordinator
        self.distributed_outbox = distributed_outbox

    def _emit_distributed_event(
        self,
        *,
        tenant_id: str,
        event_type: str,
        resource_type: str,
        resource_reference: str,
        resource_version: int,
        correlation_id: str,
        request_id: str,
        payload: dict[str, object],
    ) -> None:
        if not self.distributed_outbox:
            return
        self.distributed_outbox.create_event(
            tenant_id=tenant_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_reference=resource_reference,
            resource_version=resource_version,
            correlation_id=correlation_id,
            request_id=request_id,
            payload=payload,
        )

    def _token_hash(self, purpose: str, value: str) -> str:
        if not self.token_pepper or len(self.token_pepper) < 32:
            raise WebAuthnError("WEBAUTHN_SESSION_ISSUANCE_UNAVAILABLE")
        return hmac.new(
            self.token_pepper, f"{purpose}:{value}".encode(), hashlib.sha256
        ).hexdigest()

    def _store_challenge(
        self,
        *,
        table: str,
        tenant_id: str,
        identity_id: str | None,
        session_id: str | None,
        purpose: str,
        challenge: bytes,
        correlation_id: str,
        request_id: str,
    ) -> str:
        challenge_id, now = _id(), datetime.now(UTC)
        columns = "challenge_id,tenant_id,identity_id,"
        values: tuple[object, ...]
        if table == "novaid_webauthn_authentication_challenges":
            columns += "session_id,"
            values = (challenge_id, tenant_id, identity_id, session_id)
            placeholders = "?,?,?,?"
        else:
            values = (challenge_id, tenant_id, identity_id)
            placeholders = "?,?,?"
        columns += (
            "purpose,challenge_hash,rp_id,origin,created_at,expires_at,consumed_at,status,"
            "attempt_count,maximum_attempts,correlation_id,request_id"
        )
        values += (
            purpose,
            hashlib.sha256(challenge).hexdigest(),
            self.policy.rp_id,
            self.policy.origins[0],
            now.isoformat(),
            (now + timedelta(seconds=self.policy.challenge_seconds)).isoformat(),
            None,
            "PENDING",
            0,
            self.policy.maximum_attempts,
            correlation_id,
            request_id,
        )
        with self.uow:
            self.uow.connection.execute(
                f"INSERT INTO {table}({columns}) VALUES({placeholders},?,?,?,?,?,?,?,?,?,?,?,?)",
                values,
            )
        if self.coordinator:
            self.coordinator.create(
                tenant_id=tenant_id,
                subject=identity_id or session_id or "discoverable",
                purpose=purpose,
                challenge_id=challenge_id,
                challenge_hash=hashlib.sha256(challenge).hexdigest(),
                ttl_seconds=self.policy.challenge_seconds,
            )
        return challenge_id

    def registration_options(
        self,
        *,
        tenant_id: str,
        identity_id: str,
        membership_id: str,
        user_name: str,
        correlation_id: str,
        request_id: str,
    ) -> dict[str, object]:
        if not WEBAUTHN_AVAILABLE:
            raise WebAuthnError("WEBAUTHN_UNAVAILABLE")
        challenge = secrets.token_bytes(32)
        rows = self.uow.connection.execute(
            "SELECT credential_id,transports FROM novaid_webauthn_credentials "
            "WHERE tenant_id=? AND identity_id=? AND status IN ('ACTIVE','SUSPENDED')",
            (tenant_id, identity_id),
        ).fetchall()
        exclude = [
            PublicKeyCredentialDescriptor(id=_decode(str(row["credential_id"]))) for row in rows
        ]
        options = generate_registration_options(
            rp_id=self.policy.rp_id,
            rp_name=self.policy.rp_name,
            user_name=user_name,
            user_id=UUID(identity_id).bytes,
            challenge=challenge,
            attestation=AttestationConveyancePreference(self.policy.attestation),
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement(self.policy.resident_key),
                user_verification=UserVerificationRequirement.REQUIRED
                if self.policy.require_user_verification
                else UserVerificationRequirement.PREFERRED,
            ),
            exclude_credentials=exclude,
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier(value) for value in self.policy.allowed_algorithms
            ],
        )
        challenge_id = self._store_challenge(
            table="novaid_webauthn_registration_challenges",
            tenant_id=tenant_id,
            identity_id=identity_id,
            session_id=None,
            purpose="REGISTRATION",
            challenge=challenge,
            correlation_id=correlation_id,
            request_id=request_id,
        )
        self._emit_distributed_event(
            tenant_id=tenant_id,
            event_type="WEBAUTHN_CHALLENGE_CREATED",
            resource_type="WEBAUTHN_CHALLENGE",
            resource_reference=challenge_id,
            resource_version=1,
            correlation_id=correlation_id,
            request_id=request_id,
            payload={"purpose": "REGISTRATION", "identity_id": identity_id},
        )
        self.metrics.increment("novaid_webauthn_registration_options_total", outcome="success")
        return {"challenge_id": challenge_id, "public_key": json.loads(options_to_json(options))}

    def _consume_challenge(
        self,
        *,
        table: str,
        challenge_id: str,
        tenant_id: str,
        identity_id: str | None,
        credential: dict[str, object],
        correlation_id: str = "",
        request_id: str = "",
    ) -> bytes:
        challenge = _challenge_from_response(credential)
        with self.uow:
            row = self.uow.connection.execute(
                f"SELECT * FROM {table} WHERE challenge_id=? AND tenant_id=?",
                (challenge_id, tenant_id),
            ).fetchone()
            now = datetime.now(UTC)
            if (
                not row
                or row["status"] != "PENDING"
                or (
                    identity_id
                    and row["identity_id"] is not None
                    and str(row["identity_id"]) != identity_id
                )
                or datetime.fromisoformat(row["expires_at"]) <= now
                or not secrets.compare_digest(
                    row["challenge_hash"], hashlib.sha256(challenge).hexdigest()
                )
            ):
                raise WebAuthnError("INVALID_WEBAUTHN_CHALLENGE")
            changed = self.uow.connection.execute(
                f"UPDATE {table} SET status='CONSUMED',consumed_at=? "
                "WHERE challenge_id=? AND tenant_id=? AND status='PENDING'",
                (now.isoformat(), challenge_id, tenant_id),
            )
            if changed.rowcount != 1:
                raise WebAuthnError("INVALID_WEBAUTHN_CHALLENGE")
        if self.coordinator:
            redis_purpose = (
                "REGISTRATION"
                if table == "novaid_webauthn_registration_challenges"
                else "AUTHENTICATION"
            )
            result = self.coordinator.consume(
                tenant_id=tenant_id,
                challenge_id=challenge_id,
                challenge_hash=hashlib.sha256(challenge).hexdigest(),
                purpose=redis_purpose,
            )
            if getattr(result, "status", result) != "CONSUMED":
                raise WebAuthnError("INVALID_WEBAUTHN_CHALLENGE")
        if self.distributed_outbox:
            self._emit_distributed_event(
                tenant_id=tenant_id,
                event_type="WEBAUTHN_CHALLENGE_CONSUMED",
                resource_type=table,
                resource_reference=challenge_id,
                resource_version=1,
                correlation_id=correlation_id or challenge_id,
                request_id=request_id or challenge_id,
                payload={"identity_id": identity_id, "purpose": table},
            )
        return challenge

    def verify_registration(
        self,
        *,
        tenant_id: str,
        identity_id: str,
        membership_id: str,
        challenge_id: str,
        credential: dict[str, object],
        friendly_name: str | None = None,
        correlation_id: str = "",
        request_id: str = "",
    ) -> dict[str, object]:
        if not WEBAUTHN_AVAILABLE:
            raise WebAuthnError("WEBAUTHN_UNAVAILABLE")
        challenge = self._consume_challenge(
            table="novaid_webauthn_registration_challenges",
            challenge_id=challenge_id,
            tenant_id=tenant_id,
            identity_id=identity_id,
            credential=credential,
            correlation_id=correlation_id,
            request_id=request_id,
        )
        with self.tracer.span(
            "novaid.webauthn.register.verify", {"operation": "webauthn.register"}
        ):
            try:
                verified = verify_registration_response(
                    credential=credential,
                    expected_challenge=challenge,
                    expected_rp_id=self.policy.rp_id,
                    expected_origin=list(self.policy.origins),
                    require_user_verification=self.policy.require_user_verification,
                    supported_pub_key_algs=[
                        COSEAlgorithmIdentifier(v) for v in self.policy.allowed_algorithms
                    ],
                )
            except Exception as exc:
                raise WebAuthnError("WEBAUTHN_REGISTRATION_REJECTED") from exc
        credential_id, authenticator_id, now = (
            _b64(verified.credential_id),
            _id(),
            datetime.now(UTC),
        )
        if cbor2 is not None:
            algorithm = int(cbor2.loads(verified.credential_public_key)[3])
        else:
            algorithm = -7
        with self.uow:
            self.uow.connection.execute(
                "INSERT INTO novaid_authenticators VALUES(?,?,?,?,?,?,?,1)",
                (
                    authenticator_id,
                    tenant_id,
                    verified.aaguid,
                    friendly_name,
                    "ACTIVE",
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            self.uow.connection.execute(
                "INSERT INTO novaid_webauthn_credentials(credential_id,tenant_id,identity_id,"
                "membership_id,authenticator_id,user_handle,public_key_cose,public_key_algorithm,"
                "sign_count,aaguid,attestation_format,attestation_type,transports,backup_eligible,"
                "backup_state,discoverable,resident_key,user_verification,created_at,status,version,"
                "friendly_name) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    credential_id,
                    tenant_id,
                    identity_id,
                    membership_id,
                    authenticator_id,
                    UUID(identity_id).bytes,
                    verified.credential_public_key,
                    algorithm,
                    verified.sign_count,
                    verified.aaguid,
                    str(getattr(verified.fmt, "value", verified.fmt)),
                    "NONE",
                    "[]",
                    verified.credential_device_type.value == "multi_device",
                    verified.credential_backed_up,
                    True,
                    True,
                    verified.user_verified,
                    now.isoformat(),
                    "ACTIVE",
                    1,
                    friendly_name,
                ),
            )
        self._emit_distributed_event(
            tenant_id=tenant_id,
            event_type="WEBAUTHN_CREDENTIAL_REGISTERED",
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=credential_id,
            resource_version=1,
            correlation_id=correlation_id,
            request_id=request_id,
            payload={"identity_id": identity_id, "status": "ACTIVE"},
        )
        self.metrics.increment("novaid_webauthn_registrations_total", outcome="success")
        return {
            "credential_id": credential_id,
            "status": "ACTIVE",
            "backup_eligible": verified.credential_device_type.value == "multi_device",
            "backup_state": verified.credential_backed_up,
        }

    def authentication_options(
        self,
        *,
        tenant_id: str,
        identity_id: str | None,
        session_id: str | None,
        correlation_id: str,
        request_id: str,
    ) -> dict[str, object]:
        if not WEBAUTHN_AVAILABLE:
            raise WebAuthnError("WEBAUTHN_UNAVAILABLE")
        challenge = secrets.token_bytes(32)
        allow = None
        if identity_id:
            rows = self.uow.connection.execute(
                "SELECT credential_id FROM novaid_webauthn_credentials WHERE tenant_id=? "
                "AND identity_id=? AND status='ACTIVE'",
                (tenant_id, identity_id),
            ).fetchall()
            allow = [
                PublicKeyCredentialDescriptor(id=_decode(str(row["credential_id"]))) for row in rows
            ]
        options = generate_authentication_options(
            rp_id=self.policy.rp_id,
            challenge=challenge,
            allow_credentials=allow,
            user_verification=UserVerificationRequirement.REQUIRED
            if self.policy.require_user_verification
            else UserVerificationRequirement.PREFERRED,
        )
        challenge_id = self._store_challenge(
            table="novaid_webauthn_authentication_challenges",
            tenant_id=tenant_id,
            identity_id=identity_id,
            session_id=session_id,
            purpose="AUTHENTICATION",
            challenge=challenge,
            correlation_id=correlation_id,
            request_id=request_id,
        )
        return {"challenge_id": challenge_id, "public_key": json.loads(options_to_json(options))}

    def verify_authentication(
        self,
        *,
        tenant_id: str,
        challenge_id: str,
        credential: dict[str, object],
        correlation_id: str = "",
        request_id: str = "",
    ) -> dict[str, object]:
        if not WEBAUTHN_AVAILABLE:
            raise WebAuthnError("WEBAUTHN_UNAVAILABLE")
        credential_id = str(credential.get("id") or "")
        row = self.uow.connection.execute(
            "SELECT * FROM novaid_webauthn_credentials WHERE tenant_id=? AND credential_id=?",
            (tenant_id, credential_id),
        ).fetchone()
        if not row or row["status"] != "ACTIVE":
            raise WebAuthnError("WEBAUTHN_AUTHENTICATION_REJECTED")
        challenge = self._consume_challenge(
            table="novaid_webauthn_authentication_challenges",
            challenge_id=challenge_id,
            tenant_id=tenant_id,
            identity_id=str(row["identity_id"]),
            credential=credential,
            correlation_id=correlation_id,
            request_id=request_id,
        )
        try:
            verified = verify_authentication_response(
                credential=credential,
                expected_challenge=challenge,
                expected_rp_id=self.policy.rp_id,
                expected_origin=list(self.policy.origins),
                credential_public_key=row["public_key_cose"],
                credential_current_sign_count=int(row["sign_count"]),
                require_user_verification=self.policy.require_user_verification,
            )
        except Exception as exc:
            if "sign count" in str(exc).lower() or "counter" in str(exc).lower():
                with self.uow:
                    self.uow.connection.execute(
                        "UPDATE novaid_webauthn_credentials SET status='COMPROMISED',"
                        "version=version+1 WHERE tenant_id=? AND credential_id=? "
                        "AND status='ACTIVE'",
                        (tenant_id, credential_id),
                    )
                self._emit_distributed_event(
                    tenant_id=tenant_id,
                    event_type="WEBAUTHN_CREDENTIAL_COMPROMISED",
                    resource_type="WEBAUTHN_CREDENTIAL",
                    resource_reference=credential_id,
                    resource_version=int(row["version"]) + 1,
                    correlation_id=credential_id,
                    request_id=credential_id,
                    payload={"reason": "SIGN_COUNT_MISMATCH"},
                )
                raise WebAuthnError("WEBAUTHN_CLONE_DETECTED") from exc
            raise WebAuthnError("WEBAUTHN_AUTHENTICATION_REJECTED") from exc
        old, new = int(row["sign_count"]), int(verified.new_sign_count)
        if old > 0 and new <= old:
            with self.uow:
                self.uow.connection.execute(
                    "UPDATE novaid_webauthn_credentials SET status='COMPROMISED',version=version+1 "
                    "WHERE tenant_id=? AND credential_id=? AND status='ACTIVE'",
                    (tenant_id, credential_id),
                )
            raise WebAuthnError("WEBAUTHN_CLONE_DETECTED")
        now = datetime.now(UTC)
        with self.uow:
            changed = self.uow.connection.execute(
                "UPDATE novaid_webauthn_credentials SET sign_count=?,last_used_at=?,"
                "last_verified_at=?,"
                "backup_state=?,version=version+1 WHERE tenant_id=? AND credential_id=? "
                "AND status='ACTIVE' AND sign_count=?",
                (
                    new,
                    now.isoformat(),
                    now.isoformat(),
                    verified.credential_backed_up,
                    tenant_id,
                    credential_id,
                    old,
                ),
            )
            if changed.rowcount != 1:
                raise WebAuthnError("WEBAUTHN_COUNTER_CONFLICT")
        self._emit_distributed_event(
            tenant_id=tenant_id,
            event_type="WEBAUTHN_CREDENTIAL_REACTIVATED",
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=credential_id,
            resource_version=new,
            correlation_id=credential_id,
            request_id=credential_id,
            payload={
                "identity_id": str(row["identity_id"]),
                "authentication_strength": "PHISHING_RESISTANT",
            },
        )
        self.metrics.increment("novaid_webauthn_authentications_total", outcome="success")
        return {
            "identity_id": str(row["identity_id"]),
            "credential_id": credential_id,
            "authentication_strength": "PHISHING_RESISTANT",
            "user_verified": verified.user_verified,
        }

    def create_passwordless_session(
        self,
        *,
        tenant_id: str,
        challenge_id: str,
        credential: dict[str, object],
        correlation_id: str = "",
        request_id: str = "",
    ) -> dict[str, object]:
        evidence = self.verify_authentication(
            tenant_id=tenant_id,
            challenge_id=challenge_id,
            credential=credential,
            correlation_id=correlation_id,
            request_id=request_id,
        )
        identity_id = str(evidence["identity_id"])
        membership = self.uow.connection.execute(
            "SELECT membership_id FROM novaid_tenant_memberships WHERE tenant_id=? "
            "AND identity_id=? AND status='ACTIVE'",
            (tenant_id, identity_id),
        ).fetchone()
        identity = self.uow.connection.execute(
            "SELECT status,security_version FROM novaid_identities WHERE tenant_id=? "
            "AND identity_id=?",
            (tenant_id, identity_id),
        ).fetchone()
        if not membership or not identity or identity["status"] != "ACTIVE":
            raise WebAuthnError("WEBAUTHN_AUTHENTICATION_REJECTED")
        now, session_id, family_id, token_id = datetime.now(UTC), _id(), _id(), _id()
        raw_refresh = secrets.token_urlsafe(48)
        with self.uow:
            self.uow.connection.execute(
                "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,"
                "authentication_time,authentication_strength,credential_id,device_reference,"
                "client_reference,risk_score,status,created_at,last_seen_at,expires_at,version,"
                "membership_id,authenticated_at,idle_expires_at,absolute_expires_at,"
                "authentication_methods,security_version) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    session_id,
                    tenant_id,
                    identity_id,
                    now.isoformat(),
                    "PHISHING_RESISTANT",
                    None,
                    None,
                    None,
                    0.0,
                    "ACTIVE",
                    now.isoformat(),
                    now.isoformat(),
                    (now + timedelta(hours=12)).isoformat(),
                    1,
                    membership["membership_id"],
                    now.isoformat(),
                    (now + timedelta(minutes=30)).isoformat(),
                    (now + timedelta(hours=12)).isoformat(),
                    '["WEBAUTHN","PASSKEY"]',
                    identity["security_version"],
                ),
            )
            self.uow.connection.execute(
                "INSERT INTO novaid_refresh_token_families VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    family_id,
                    session_id,
                    identity_id,
                    tenant_id,
                    "ACTIVE",
                    now.isoformat(),
                    (now + timedelta(days=30)).isoformat(),
                    None,
                    1,
                ),
            )
            self.uow.connection.execute(
                "INSERT INTO novaid_refresh_tokens VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    token_id,
                    family_id,
                    session_id,
                    identity_id,
                    tenant_id,
                    self._token_hash("refresh", raw_refresh),
                    None,
                    now.isoformat(),
                    (now + timedelta(days=7)).isoformat(),
                    None,
                    None,
                    None,
                    "ACTIVE",
                ),
            )
        self.metrics.increment("novaid_webauthn_passwordless_sessions_total", outcome="success")
        return {
            **evidence,
            "session_id": session_id,
            "membership_id": str(membership["membership_id"]),
            "refresh_token": f"{token_id}.{raw_refresh}",
        }

    def complete_session_step_up(
        self,
        *,
        tenant_id: str,
        session_id: str,
        challenge_id: str,
        credential: dict[str, object],
        correlation_id: str = "",
        request_id: str = "",
    ) -> dict[str, object]:
        session = self.uow.connection.execute(
            "SELECT identity_id,status FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND session_id=?",
            (tenant_id, session_id),
        ).fetchone()
        if not session or session["status"] != "STEP_UP_REQUIRED":
            raise WebAuthnError("WEBAUTHN_STEP_UP_REJECTED")
        evidence = self.verify_authentication(
            tenant_id=tenant_id,
            challenge_id=challenge_id,
            credential=credential,
            correlation_id=correlation_id,
            request_id=request_id,
        )
        if str(evidence["identity_id"]) != str(session["identity_id"]):
            raise WebAuthnError("WEBAUTHN_STEP_UP_REJECTED")
        now = datetime.now(UTC)
        with self.uow:
            changed = self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='ACTIVE',"
                "authentication_strength='PHISHING_RESISTANT',authenticated_at=?,"
                "step_up_expires_at=?,authentication_methods='[\"WEBAUTHN\"]' "
                "WHERE tenant_id=? AND session_id=? AND status='STEP_UP_REQUIRED'",
                (now.isoformat(), (now + timedelta(minutes=5)).isoformat(), tenant_id, session_id),
            )
            if changed.rowcount != 1:
                raise WebAuthnError("WEBAUTHN_STEP_UP_REJECTED")
        self.metrics.increment("novaid_webauthn_step_up_total", outcome="success")
        return {**evidence, "session_id": session_id, "step_up_completed_at": now.isoformat()}

    def transition_credential(
        self,
        *,
        tenant_id: str,
        identity_id: str,
        credential_id: str,
        target: str,
        reason: str,
        actor_identity_id: str,
    ) -> None:
        allowed = {"SUSPENDED", "REVOKED", "COMPROMISED", "REPLACED", "DELETED", "ACTIVE"}
        if target not in allowed:
            raise WebAuthnError("INVALID_AUTHENTICATOR_STATUS")
        with self.uow:
            row = self.uow.connection.execute(
                "SELECT status,version FROM novaid_webauthn_credentials WHERE tenant_id=? "
                "AND identity_id=? "
                "AND credential_id=?",
                (tenant_id, identity_id, credential_id),
            ).fetchone()
            if (
                not row
                or row["status"] in {"REVOKED", "COMPROMISED", "DELETED"}
                and target == "ACTIVE"
            ):
                raise WebAuthnError("INVALID_AUTHENTICATOR_TRANSITION")
            self.uow.connection.execute(
                "UPDATE novaid_webauthn_credentials SET status=?,version=version+1 "
                "WHERE tenant_id=? AND identity_id=? AND credential_id=?",
                (target, tenant_id, identity_id, credential_id),
            )
            self.uow.connection.execute(
                "INSERT INTO novaid_authenticator_status_history VALUES(?,?,?,?,?,?,?,?)",
                (
                    _id(),
                    tenant_id,
                    credential_id,
                    row["status"],
                    target,
                    reason,
                    datetime.now(UTC).isoformat(),
                    actor_identity_id,
                ),
            )
        event_type = {
            "SUSPENDED": "WEBAUTHN_CREDENTIAL_SUSPENDED",
            "REVOKED": "WEBAUTHN_CREDENTIAL_REVOKED",
            "COMPROMISED": "WEBAUTHN_CREDENTIAL_COMPROMISED",
            "REPLACED": "WEBAUTHN_CREDENTIAL_REPLACED",
            "ACTIVE": "WEBAUTHN_CREDENTIAL_REACTIVATED",
            "DELETED": "WEBAUTHN_CREDENTIAL_REVOKED",
        }[target]
        self._emit_distributed_event(
            tenant_id=tenant_id,
            event_type=event_type,
            resource_type="WEBAUTHN_CREDENTIAL",
            resource_reference=credential_id,
            resource_version=int(row["version"]) + 1,
            correlation_id=actor_identity_id,
            request_id=actor_identity_id,
            payload={"reason": reason, "actor_identity_id": actor_identity_id},
        )
