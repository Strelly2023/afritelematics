"""Schema-validated Phase 3 authentication routes."""
# ruff: noqa: E501

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .application.authentication import AuthenticationError, DurableAuthenticationService
from .application.passwords import PasswordLifecycleService
from .application.sessions import SessionAdministrationService
from .tokens import AccessTokenError, AccessTokenService
from .observability import NovaIDMetrics, NovaIDTracer
from .application.webauthn import WebAuthnError, WebAuthnService
from .application.recovery import AccountRecoveryService, RecoveryCodeService, RecoveryError
from .application.recovery import TenantWebAuthnPolicyService


class RegisterRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    password: str = Field(min_length=12, max_length=1024)


class VerifyRequest(BaseModel):
    identity_id: str
    challenge_id: str
    code: str = Field(pattern=r"^[0-9]{6}$")


class AuthenticateRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class MfaRequest(BaseModel):
    session_id: str
    challenge_id: str
    code: str = Field(pattern=r"^[0-9]{6}$")
    device_id: str | None = Field(default=None, min_length=1, max_length=512)


class MfaChallengeRequest(BaseModel):
    session_id: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=12, max_length=1024)


class ResetRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)


class ResetCompleteRequest(BaseModel):
    challenge_id: str
    code: str = Field(pattern=r"^[0-9]{6}$")
    new_password: str = Field(min_length=12, max_length=1024)


class WebAuthnRegistrationOptionsRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=320)


class WebAuthnRegistrationVerifyRequest(BaseModel):
    challenge_id: str
    credential: dict[str, object]
    friendly_name: str | None = Field(default=None, max_length=100)


class WebAuthnAuthenticationOptionsRequest(BaseModel):
    identity_id: str | None = None
    session_id: str | None = None


class WebAuthnAuthenticationVerifyRequest(BaseModel):
    challenge_id: str
    credential: dict[str, object]


class WebAuthnStepUpRequest(BaseModel):
    session_id: str


class WebAuthnStepUpVerifyRequest(BaseModel):
    session_id: str
    challenge_id: str
    credential: dict[str, object]


class RecoveryCodeGenerateRequest(BaseModel):
    count: int | None = Field(default=None, ge=1, le=20)


class RecoveryRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=320)
    recovery_method: str = Field(pattern=r"^(RECOVERY_CODE|WEBAUTHN|ADMIN_ASSISTED)$")
    device_reference: str | None = Field(default=None, max_length=200)
    network_reference: str | None = Field(default=None, max_length=200)


class RecoveryVerifyRequest(BaseModel):
    recovery_request_id: str
    code: str = Field(min_length=10, max_length=100)


class RecoveryDecisionRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class TenantPolicyRequest(BaseModel):
    policy: dict[str, object]
    expected_version: int | None = Field(default=None, ge=1)
    reason: str = Field(min_length=3, max_length=500)


def build_durable_authentication_router(
    service: DurableAuthenticationService,
    *,
    tokens: AccessTokenService | None = None,
    passwords: PasswordLifecycleService | None = None,
    sessions: SessionAdministrationService | None = None,
    metrics: NovaIDMetrics | None = None,
    tracer: NovaIDTracer | None = None,
    webauthn_service: WebAuthnService | None = None,
    recovery_codes: RecoveryCodeService | None = None,
    account_recovery: AccountRecoveryService | None = None,
    webauthn_policies: TenantWebAuthnPolicyService | None = None,
    provisional_tokens=None,
) -> APIRouter:
    router = APIRouter(prefix="/v1/novaid", tags=["novaid-authentication"])

    metrics = metrics or NovaIDMetrics()
    tracer = tracer or NovaIDTracer()

    def invoke(call, *, operation: str | None = None, **kwargs):
        operation = operation or call.__name__.replace("_", ".")
        with tracer.span(f"novaid.{operation}", {"operation": operation}):
            metrics.increment(f"novaid_{operation.replace('.', '_')}_attempts_total")
            try:
                result = call(**kwargs)
                metrics.increment(
                    f"novaid_{operation.replace('.', '_')}_success_total", outcome="success"
                )
                return result
            except AuthenticationError as exc:
                metrics.increment(
                    f"novaid_{operation.replace('.', '_')}_failures_total", outcome="denied"
                )
                public = (
                    str(exc)
                    if str(exc) in {"IDEMPOTENCY_CONFLICT", "TOKEN_REPLAY_DETECTED"}
                    else "AUTHENTICATION_DENIED"
                )
                raise HTTPException(
                    status_code=409 if public == "IDEMPOTENCY_CONFLICT" else 401,
                    detail={"code": public},
                ) from None

    def claims(
        authorization: str, tenant_id: str, minimum_strength: str = "PASSWORD_OTP"
    ) -> dict[str, object]:
        if not tokens or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"})
        try:
            return tokens.validate(
                authorization[7:], expected_tenant=tenant_id, minimum_strength=minimum_strength
            )
        except AccessTokenError as exc:
            raise HTTPException(status_code=401, detail={"code": str(exc)}) from None

    def invoke_webauthn(method: str, **kwargs):
        if not webauthn_service:
            raise HTTPException(status_code=503, detail={"code": "WEBAUTHN_UNAVAILABLE"})
        try:
            return getattr(webauthn_service, method)(**kwargs)
        except WebAuthnError:
            raise HTTPException(
                status_code=401, detail={"code": "WEBAUTHN_CEREMONY_REJECTED"}
            ) from None

    @router.post("/register", status_code=202)
    def register(
        payload: RegisterRequest,
        x_tenant_id: str = Header(),
        idempotency_key: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, str]:
        return invoke(
            service.register,
            operation="register",
            tenant_id=x_tenant_id,
            email=str(payload.email),
            password=payload.password,
            idempotency_key=idempotency_key,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/verify", status_code=204)
    def verify(
        payload: VerifyRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> None:
        invoke(
            service.verify_identity,
            operation="verify",
            tenant_id=x_tenant_id,
            identity_id=payload.identity_id,
            challenge_id=payload.challenge_id,
            code=payload.code,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/authenticate")
    def authenticate(
        payload: AuthenticateRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, str]:
        return invoke(
            service.authenticate,
            operation="authenticate",
            tenant_id=x_tenant_id,
            email=str(payload.email),
            password=payload.password,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/mfa/verify")
    def mfa_verify(
        payload: MfaRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, str]:
        result = invoke(
            service.complete_mfa,
            operation="mfa.verify",
            tenant_id=x_tenant_id,
            session_id=payload.session_id,
            challenge_id=payload.challenge_id,
            code=payload.code,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
            device_id=payload.device_id,
        )
        if payload.device_id and provisional_tokens:
            result["provisional_token"] = provisional_tokens.issue(
                tenant_id=x_tenant_id,
                subject_id=result.pop("identity_id"),
                session_id=payload.session_id,
                membership_id=result.pop("membership_id"),
                device_id=payload.device_id,
                security_version=int(result.pop("security_version")),
            )
        elif tokens:
            row = service.uow.connection.execute(
                "SELECT m.membership_id FROM novaid_authentication_sessions s "
                "JOIN novaid_tenant_memberships m ON m.identity_id=s.identity_id AND m.tenant_id=s.tenant_id "
                "WHERE s.session_id=? AND s.tenant_id=? AND m.status='ACTIVE'",
                (payload.session_id, x_tenant_id),
            ).fetchone()
            result["access_token"] = tokens.issue(
                x_tenant_id, payload.session_id, row["membership_id"]
            )
        return result

    @router.post("/mfa/challenge", status_code=202)
    def mfa_challenge(
        payload: MfaChallengeRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, str]:
        return invoke(
            service.issue_mfa_challenge,
            operation="mfa.issue",
            tenant_id=x_tenant_id,
            session_id=payload.session_id,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/token/refresh")
    def refresh(
        payload: RefreshRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, str]:
        token = invoke(
            service.refresh,
            operation="token.refresh",
            tenant_id=x_tenant_id,
            presented_token=payload.refresh_token,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )
        return {"refresh_token": token}

    @router.get("/me")
    def me(x_tenant_id: str = Header(), authorization: str = Header()) -> dict[str, object]:
        token = claims(authorization, x_tenant_id)
        row = service.uow.connection.execute(
            "SELECT i.status identity_status,i.security_version,m.status membership_status,"
            "s.status session_status,s.authentication_time,s.expires_at "
            "FROM novaid_identities i JOIN novaid_tenant_memberships m ON m.identity_id=i.identity_id "
            "JOIN novaid_authentication_sessions s ON s.identity_id=i.identity_id "
            "WHERE i.tenant_id=? AND i.identity_id=? AND m.membership_id=? AND s.session_id=?",
            (x_tenant_id, token["sub"], token["membership_id"], token["session_id"]),
        ).fetchone()
        return {
            "identity_id": token["sub"],
            "tenant_id": x_tenant_id,
            "membership_id": token["membership_id"],
            "session_id": token["session_id"],
            "authentication_strength": token["authentication_strength"],
            **dict(row),
        }

    @router.get("/sessions")
    def list_sessions(
        x_tenant_id: str = Header(), authorization: str = Header()
    ) -> list[dict[str, object]]:
        token = claims(authorization, x_tenant_id)
        if not sessions:
            raise HTTPException(status_code=503, detail={"code": "SERVICE_UNAVAILABLE"})
        return sessions.list_own(x_tenant_id, str(token["sub"]))

    @router.delete("/sessions/{session_id}")
    @router.post("/sessions/{session_id}/revoke")
    def revoke_session(
        session_id: str, x_tenant_id: str = Header(), authorization: str = Header()
    ) -> dict[str, bool]:
        token = claims(authorization, x_tenant_id)
        if not sessions:
            raise HTTPException(status_code=503, detail={"code": "SERVICE_UNAVAILABLE"})
        return {"revoked": sessions.revoke(x_tenant_id, str(token["sub"]), session_id)}

    @router.post("/logout")
    def logout(x_tenant_id: str = Header(), authorization: str = Header()) -> dict[str, bool]:
        token = claims(authorization, x_tenant_id)
        if not sessions:
            raise HTTPException(status_code=503, detail={"code": "SERVICE_UNAVAILABLE"})
        sessions.revoke(x_tenant_id, str(token["sub"]), str(token["session_id"]))
        return {"logged_out": True}

    @router.post("/logout-all")
    def logout_all(x_tenant_id: str = Header(), authorization: str = Header()) -> dict[str, int]:
        token = claims(authorization, x_tenant_id)
        if not sessions:
            raise HTTPException(status_code=503, detail={"code": "SERVICE_UNAVAILABLE"})
        return {"revoked_sessions": sessions.logout_all(x_tenant_id, str(token["sub"]))}

    @router.post("/password/change", status_code=204)
    def password_change(
        payload: PasswordChangeRequest, x_tenant_id: str = Header(), authorization: str = Header()
    ) -> None:
        token = claims(authorization, x_tenant_id)
        if not passwords:
            raise HTTPException(status_code=503, detail={"code": "SERVICE_UNAVAILABLE"})
        passwords.change(
            tenant_id=x_tenant_id,
            identity_id=str(token["sub"]),
            session_id=str(token["session_id"]),
            current_password=payload.current_password,
            new_password=payload.new_password,
        )

    @router.post("/password/reset/request", status_code=202)
    def reset_request(
        payload: ResetRequest, x_tenant_id: str = Header(), x_correlation_id: str = Header()
    ) -> dict[str, str]:
        if not passwords:
            raise HTTPException(status_code=503, detail={"code": "SERVICE_UNAVAILABLE"})
        return passwords.request_reset(
            tenant_id=x_tenant_id, email=payload.email, correlation_id=x_correlation_id
        )

    @router.post("/password/reset/complete", status_code=204)
    def reset_complete(payload: ResetCompleteRequest, x_tenant_id: str = Header()) -> None:
        if not passwords:
            raise HTTPException(status_code=503, detail={"code": "SERVICE_UNAVAILABLE"})
        passwords.complete_reset(
            tenant_id=x_tenant_id,
            challenge_id=payload.challenge_id,
            code=payload.code,
            new_password=payload.new_password,
        )

    @router.post("/webauthn/registration/options")
    def webauthn_registration_options(
        payload: WebAuthnRegistrationOptionsRequest,
        x_tenant_id: str = Header(),
        authorization: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, object]:
        token = claims(authorization, x_tenant_id)
        return invoke_webauthn(
            "registration_options",
            tenant_id=x_tenant_id,
            identity_id=str(token["sub"]),
            membership_id=str(token["membership_id"]),
            user_name=payload.user_name,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/webauthn/registration/verify", status_code=201)
    def webauthn_registration_verify(
        payload: WebAuthnRegistrationVerifyRequest,
        x_tenant_id: str = Header(),
        authorization: str = Header(),
        x_correlation_id: str = Header(default=""),
        x_request_id: str = Header(default=""),
    ) -> dict[str, object]:
        token = claims(authorization, x_tenant_id)
        return invoke_webauthn(
            "verify_registration",
            tenant_id=x_tenant_id,
            identity_id=str(token["sub"]),
            membership_id=str(token["membership_id"]),
            challenge_id=payload.challenge_id,
            credential=payload.credential,
            friendly_name=payload.friendly_name,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/webauthn/authentication/options")
    def webauthn_authentication_options(
        payload: WebAuthnAuthenticationOptionsRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, object]:
        return invoke_webauthn(
            "authentication_options",
            tenant_id=x_tenant_id,
            identity_id=payload.identity_id,
            session_id=payload.session_id,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/webauthn/authentication/verify")
    def webauthn_authentication_verify(
        payload: WebAuthnAuthenticationVerifyRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(default=""),
        x_request_id: str = Header(default=""),
    ) -> dict[str, object]:
        return invoke_webauthn(
            "verify_authentication",
            tenant_id=x_tenant_id,
            challenge_id=payload.challenge_id,
            credential=payload.credential,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/webauthn/passwordless/verify")
    def webauthn_passwordless_verify(
        payload: WebAuthnAuthenticationVerifyRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(default=""),
        x_request_id: str = Header(default=""),
    ) -> dict[str, object]:
        result = invoke_webauthn(
            "create_passwordless_session",
            tenant_id=x_tenant_id,
            challenge_id=payload.challenge_id,
            credential=payload.credential,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )
        if tokens:
            result["access_token"] = tokens.issue(
                x_tenant_id, str(result["session_id"]), str(result["membership_id"])
            )
        return result

    @router.post("/webauthn/step-up/options")
    def webauthn_step_up_options(
        payload: WebAuthnStepUpRequest,
        x_tenant_id: str = Header(),
        authorization: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, object]:
        token = claims(authorization, x_tenant_id)
        if str(token["session_id"]) != payload.session_id or not sessions:
            raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_DENIED"})
        sessions.require_step_up(
            x_tenant_id,
            str(token["sub"]),
            payload.session_id,
            until=datetime.now(UTC) + timedelta(minutes=5),
        )
        return invoke_webauthn(
            "authentication_options",
            tenant_id=x_tenant_id,
            identity_id=str(token["sub"]),
            session_id=payload.session_id,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )

    @router.post("/webauthn/step-up/verify")
    def webauthn_step_up_verify(
        payload: WebAuthnStepUpVerifyRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(default=""),
        x_request_id: str = Header(default=""),
    ) -> dict[str, object]:
        result = invoke_webauthn(
            "complete_session_step_up",
            tenant_id=x_tenant_id,
            session_id=payload.session_id,
            challenge_id=payload.challenge_id,
            credential=payload.credential,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
        )
        if tokens:
            membership = service.uow.connection.execute(
                "SELECT membership_id FROM novaid_authentication_sessions "
                "WHERE tenant_id=? AND session_id=?",
                (x_tenant_id, payload.session_id),
            ).fetchone()
            result["access_token"] = tokens.issue(
                x_tenant_id, payload.session_id, str(membership["membership_id"])
            )
        return result

    @router.post("/recovery-codes", status_code=201)
    def generate_recovery_codes(
        payload: RecoveryCodeGenerateRequest,
        x_tenant_id: str = Header(),
        authorization: str = Header(),
    ) -> dict[str, object]:
        token = claims(authorization, x_tenant_id)
        if not recovery_codes:
            raise HTTPException(status_code=503, detail={"code": "RECOVERY_UNAVAILABLE"})
        try:
            return recovery_codes.generate_codes(
                tenant_id=x_tenant_id,
                identity_id=str(token["sub"]),
                session_id=str(token["session_id"]),
                count=payload.count,
            )
        except RecoveryError:
            raise HTTPException(
                status_code=403, detail={"code": "RECOVERY_OPERATION_DENIED"}
            ) from None

    @router.get("/recovery-codes")
    def remaining_recovery_codes(
        x_tenant_id: str = Header(), authorization: str = Header()
    ) -> dict[str, int]:
        token = claims(authorization, x_tenant_id)
        if not recovery_codes:
            raise HTTPException(status_code=503, detail={"code": "RECOVERY_UNAVAILABLE"})
        return {
            "remaining": recovery_codes.remaining(
                tenant_id=x_tenant_id, identity_id=str(token["sub"])
            )
        }

    @router.delete("/recovery-codes")
    def revoke_recovery_codes(
        x_tenant_id: str = Header(), authorization: str = Header()
    ) -> dict[str, int]:
        token = claims(authorization, x_tenant_id)
        if not recovery_codes:
            raise HTTPException(status_code=503, detail={"code": "RECOVERY_UNAVAILABLE"})
        try:
            count = recovery_codes.revoke_all(
                tenant_id=x_tenant_id,
                identity_id=str(token["sub"]),
                session_id=str(token["session_id"]),
            )
        except RecoveryError:
            raise HTTPException(
                status_code=403, detail={"code": "RECOVERY_OPERATION_DENIED"}
            ) from None
        return {"revoked": count}

    @router.post("/account-recovery", status_code=202)
    def request_account_recovery(
        payload: RecoveryRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> dict[str, object]:
        if not account_recovery:
            raise HTTPException(status_code=503, detail={"code": "RECOVERY_UNAVAILABLE"})
        account_recovery.request_recovery(
            tenant_id=x_tenant_id,
            identifier=payload.identifier,
            recovery_method=payload.recovery_method,
            correlation_id=x_correlation_id,
            request_id=x_request_id,
            device_reference=payload.device_reference,
            network_reference=payload.network_reference,
        )
        return {"accepted": True}

    @router.post("/account-recovery/verify", status_code=204)
    def verify_account_recovery(
        payload: RecoveryVerifyRequest,
        x_tenant_id: str = Header(),
        x_correlation_id: str = Header(),
        x_request_id: str = Header(),
    ) -> None:
        if not account_recovery:
            raise HTTPException(status_code=503, detail={"code": "RECOVERY_UNAVAILABLE"})
        try:
            account_recovery.verify_recovery_code(
                tenant_id=x_tenant_id,
                recovery_request_id=payload.recovery_request_id,
                code=payload.code,
                correlation_id=x_correlation_id,
                request_id=x_request_id,
            )
        except RecoveryError:
            raise HTTPException(
                status_code=401, detail={"code": "ACCOUNT_RECOVERY_DENIED"}
            ) from None

    @router.post("/account-recovery/{recovery_request_id}/approve", status_code=204)
    def approve_account_recovery(
        recovery_request_id: str,
        payload: RecoveryDecisionRequest,
        x_tenant_id: str = Header(),
        authorization: str = Header(),
    ) -> None:
        token = claims(authorization, x_tenant_id, minimum_strength="PHISHING_RESISTANT")
        if not account_recovery:
            raise HTTPException(status_code=503, detail={"code": "RECOVERY_UNAVAILABLE"})
        try:
            account_recovery.approve(
                tenant_id=x_tenant_id,
                recovery_request_id=recovery_request_id,
                approver_identity_id=str(token["sub"]),
                reason=payload.reason,
            )
        except RecoveryError:
            raise HTTPException(
                status_code=403, detail={"code": "ACCOUNT_RECOVERY_DENIED"}
            ) from None

    @router.post("/account-recovery/{recovery_request_id}/complete", status_code=204)
    def complete_account_recovery(
        recovery_request_id: str, x_tenant_id: str = Header(), authorization: str = Header()
    ) -> None:
        claims(authorization, x_tenant_id, minimum_strength="PHISHING_RESISTANT")
        if not account_recovery:
            raise HTTPException(status_code=503, detail={"code": "RECOVERY_UNAVAILABLE"})
        try:
            account_recovery.complete(
                tenant_id=x_tenant_id, recovery_request_id=recovery_request_id
            )
        except RecoveryError:
            raise HTTPException(
                status_code=403, detail={"code": "ACCOUNT_RECOVERY_DENIED"}
            ) from None

    @router.get("/webauthn/policy")
    def get_webauthn_policy(
        x_tenant_id: str = Header(), authorization: str = Header()
    ) -> dict[str, object]:
        claims(authorization, x_tenant_id)
        if not webauthn_policies:
            raise HTTPException(status_code=503, detail={"code": "POLICY_UNAVAILABLE"})
        return webauthn_policies.get_policy(x_tenant_id)

    @router.put("/webauthn/policy")
    def set_webauthn_policy(
        payload: TenantPolicyRequest, x_tenant_id: str = Header(), authorization: str = Header()
    ) -> dict[str, object]:
        token = claims(authorization, x_tenant_id, minimum_strength="PHISHING_RESISTANT")
        if not webauthn_policies:
            raise HTTPException(status_code=503, detail={"code": "POLICY_UNAVAILABLE"})
        try:
            return webauthn_policies.set_policy(
                tenant_id=x_tenant_id,
                actor_identity_id=str(token["sub"]),
                session_id=str(token["session_id"]),
                policy=payload.policy,
                expected_version=payload.expected_version,
                reason=payload.reason,
            )
        except RecoveryError:
            raise HTTPException(status_code=403, detail={"code": "POLICY_CHANGE_DENIED"}) from None

    @router.get("/internal/webauthn/outbox/dead-letters")
    def list_webauthn_dead_letters(
        x_tenant_id: str = Header(), authorization: str = Header(), limit: int = 100
    ) -> list[dict[str, object]]:
        claims(authorization, x_tenant_id, minimum_strength="PHISHING_RESISTANT")
        outbox = getattr(router, "novaid_webauthn_outbox", None)
        if not outbox:
            raise HTTPException(status_code=503, detail={"code": "OUTBOX_UNAVAILABLE"})
        rows = outbox.list_dead_letters(tenant_id=x_tenant_id, limit=max(1, min(limit, 100)))
        return [dict(row) for row in rows]

    @router.post("/internal/webauthn/outbox/{event_id}/replay")
    def replay_webauthn_dead_letter(
        event_id: str,
        payload: RecoveryDecisionRequest,
        x_tenant_id: str = Header(),
        authorization: str = Header(),
    ) -> dict[str, object]:
        token = claims(authorization, x_tenant_id, minimum_strength="PHISHING_RESISTANT")
        outbox = getattr(router, "novaid_webauthn_outbox", None)
        if not outbox:
            raise HTTPException(status_code=503, detail={"code": "OUTBOX_UNAVAILABLE"})
        try:
            return outbox.replay_dead_letter(
                event_id=event_id,
                tenant_id=x_tenant_id,
                reason=payload.reason,
                actor_identity_id=str(token["sub"]),
            )
        except ValueError as exc:
            code = str(exc)
            if code == "dead_letter_stale":
                raise HTTPException(status_code=409, detail={"code": code}) from None
            if code == "dead_letter_not_found":
                raise HTTPException(status_code=404, detail={"code": code}) from None
            raise HTTPException(status_code=400, detail={"code": code}) from None

    return router
