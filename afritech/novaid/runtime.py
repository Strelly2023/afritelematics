from __future__ import annotations

import json
import os
from pathlib import Path

from .api import build_durable_authentication_router
from .application import (
    AuthenticationLockoutService,
    DurableAuthenticationService,
    PasswordLifecycleService,
    SessionAdministrationService,
)
from .application.webauthn import WebAuthnService
from .application.recovery import AccountRecoveryService, RecoveryCodeService
from .application.recovery import TenantWebAuthnPolicyService
from .domain import AuthenticatorPolicy
from .config import NovaIDAuthenticationConfig
from .persistence import NovaIDUnitOfWork
from .persistence import PostgresNovaIdUnitOfWork
from .persistence.migrations import verify_migration_revisions
from .persistence.pool import NovaIDPostgresPool
from .revocation import ProcessLocalRevocationStore, RedisRevocationStore
from .tokens import AccessTokenService
from .otp_delivery import HTTPSOTPDeliveryProvider, OTPDeliveryProvider
from .observability import NovaIDMetrics, NovaIDTracer
from .outbox import RevocationOutbox
from .revocation_delivery import RevocationConsumer, RevocationPublisher
from .webauthn_coordination import RedisWebAuthnChallengeCoordinator
from .webauthn_delivery import (
    WebAuthnDistributedEventConsumer,
    WebAuthnOutboxPublisher,
    WebAuthnOutboxRepository,
)


def validate_runtime_environment(stage: str, backend: str) -> None:
    if stage not in {"production", "prod"}:
        return
    if backend != "postgres":
        raise RuntimeError("production_novaid_requires_postgres")
    database_url = os.getenv("NOVAID_DATABASE_URL", "")
    if not database_url:
        raise RuntimeError("missing_novaid_postgres_url")
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("invalid_novaid_postgres_url")
    issuer, audience = os.getenv("NOVAID_JWT_ISSUER", ""), os.getenv("NOVAID_JWT_AUDIENCE", "")
    if not issuer:
        raise RuntimeError("missing_novaid_issuer")
    if not audience:
        raise RuntimeError("missing_novaid_audience")
    if audience == "*":
        raise RuntimeError("wildcard_novaid_audience")
    if os.getenv("NOVAID_TOKEN_ALGORITHM", "HS256") != "HS256":
        raise RuntimeError("unsupported_novaid_token_algorithm")
    _load_signing_keyring(require_rotation=True)
    if os.getenv("NOVAID_REDIS_REQUIRED", "true").lower() == "true" and not os.getenv(
        "NOVAID_REDIS_URL"
    ):
        raise RuntimeError("required_novaid_redis_url_missing")
    endpoint = os.getenv("NOVAID_OTP_PROVIDER_ENDPOINT", "")
    if not endpoint:
        raise RuntimeError("missing_novaid_otp_provider_endpoint")
    if not endpoint.startswith("https://"):
        raise RuntimeError("novaid_otp_provider_requires_https")
    if not os.getenv("NOVAID_OTP_PROVIDER_API_KEY", ""):
        raise RuntimeError("missing_novaid_otp_provider_api_key")
    try:
        timeout = float(os.getenv("NOVAID_OTP_PROVIDER_TIMEOUT", "5"))
    except ValueError as exc:
        raise RuntimeError("invalid_novaid_otp_provider_timeout") from exc
    if timeout <= 0:
        raise RuntimeError("invalid_novaid_otp_provider_timeout")
    rp_id = os.getenv("NOVAID_WEBAUTHN_RP_ID", "").strip().lower()
    if not rp_id or rp_id in {"localhost", "127.0.0.1"}:
        raise RuntimeError("missing_production_novaid_webauthn_rp_id")
    if "://" in rp_id or "/" in rp_id or "*" in rp_id:
        raise RuntimeError("invalid_production_novaid_webauthn_rp_id")
    origins = tuple(
        item.strip()
        for item in os.getenv("NOVAID_WEBAUTHN_ORIGINS", "").split(",")
        if item.strip()
    )
    if not origins:
        raise RuntimeError("missing_production_novaid_webauthn_origins")
    if any(not origin.startswith("https://") or "*" in origin for origin in origins):
        raise RuntimeError("insecure_production_novaid_webauthn_origin")
    if os.getenv("NOVAID_WEBAUTHN_REQUIRE_UV", "true").lower() != "true":
        raise RuntimeError("production_novaid_webauthn_user_verification_required")


def build_default_durable_router(*, otp_delivery: OTPDeliveryProvider | None = None):
    stage = os.getenv("AFRITECH_ENV", "development").lower()
    backend = os.getenv("NOVAID_PERSISTENCE_BACKEND", "sqlite").lower()
    validate_runtime_environment(stage, backend)
    if backend not in {"sqlite", "postgres"}:
        raise RuntimeError("unsupported_novaid_persistence_backend")
    config = NovaIDAuthenticationConfig.from_environment(stage)
    pool = None
    if backend == "postgres":
        dsn = os.getenv("NOVAID_DATABASE_URL", "")
        if not dsn:
            raise RuntimeError("missing_novaid_postgres_url")
        pool = NovaIDPostgresPool(
            dsn,
            minimum_size=int(os.getenv("NOVAID_POSTGRES_POOL_MIN", "1")),
            maximum_size=int(os.getenv("NOVAID_POSTGRES_POOL_MAX", "8")),
            timeout=float(os.getenv("NOVAID_POSTGRES_POOL_TIMEOUT", "5")),
        )
        if not pool.check():
            raise RuntimeError("novaid_postgres_unavailable")
        with pool.connection() as connection:
            verify_migration_revisions(connection)
            connection.rollback()
        uow = PostgresNovaIdUnitOfWork(pool=pool)
    else:
        path = Path(os.getenv("NOVAID_DURABLE_DB_PATH", "/tmp/novaid-durable.sqlite3"))
        uow = NovaIDUnitOfWork(path)
    def c24_uow_provider():
        if pool is not None:
            return PostgresNovaIdUnitOfWork(pool=pool)
        return NovaIDUnitOfWork(path)

    pepper = os.getenv("NOVAID_TOKEN_PEPPER", "development-only-novaid-pepper-0001").encode()
    signing_keys, active_signing_key_id = _load_signing_keyring(
        require_rotation=stage in {"production", "prod"}
    )
    redis_url = os.getenv("NOVAID_REDIS_URL", "")
    if redis_url:
        import redis

        redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        try:
            redis_client.ping()
        except Exception as exc:
            if os.getenv("NOVAID_REDIS_REQUIRED", "false").lower() == "true":
                if pool:
                    pool.close()
                raise RuntimeError("required_novaid_redis_unavailable") from exc
            redis_client = None
        revocations = (
            RedisRevocationStore(redis_client) if redis_client else ProcessLocalRevocationStore()
        )
    else:
        revocations = ProcessLocalRevocationStore()
    trace_path = os.getenv("NOVAID_TRACE_EXPORT_PATH", "")
    metrics, tracer = (
        NovaIDMetrics(),
        NovaIDTracer(export_path=Path(trace_path) if trace_path else None),
    )
    outbox = RevocationOutbox(uow)
    lockout = AuthenticationLockoutService(uow, pepper=pepper)
    production = stage in {"production", "prod"}
    if production and otp_delivery is None:
        otp_delivery = HTTPSOTPDeliveryProvider(
            os.environ["NOVAID_OTP_PROVIDER_ENDPOINT"],
            os.environ["NOVAID_OTP_PROVIDER_API_KEY"],
            timeout_seconds=float(os.getenv("NOVAID_OTP_PROVIDER_TIMEOUT", "5")),
        )
    authentication = DurableAuthenticationService(
        uow,
        pepper=pepper,
        lockout=lockout,
        otp_delivery=otp_delivery,
        expose_otp_codes=not production,
    )
    passwords = PasswordLifecycleService(uow, revocations, pepper=pepper, outbox=outbox)
    sessions = SessionAdministrationService(
        uow, revocations, outbox=outbox, metrics=metrics, tracer=tracer
    )
    tokens = AccessTokenService(
        uow,
        revocations,
        signing_keys=signing_keys,
        active_key_id=active_signing_key_id,
        issuer=config.jwt_issuer or "novaid-development",
        audience=config.jwt_audience or "novaid-development-clients",
        lifetime_seconds=config.access_token_seconds,
    )
    from afritech.novaid.provisional_attestation_tokens import (
        ProvisionalAttestationTokenService,
    )

    provisional_tokens = ProvisionalAttestationTokenService(
        c24_uow_provider,
        signing_keys=signing_keys,
        active_key_id=active_signing_key_id,
        issuer=config.jwt_issuer or "novaid-development",
        lifetime_seconds=int(
            os.getenv(
                "NOVAID_DEVICE_ATTESTATION_BOOTSTRAP_SECONDS",
                "180",
            )
        ),
    )

    distributed_outbox = WebAuthnOutboxRepository(uow)
    webauthn_service = WebAuthnService(
        uow,
        AuthenticatorPolicy(
            rp_id=os.getenv("NOVAID_WEBAUTHN_RP_ID", "localhost"),
            rp_name=os.getenv("NOVAID_WEBAUTHN_RP_NAME", "NovaID"),
            origins=tuple(
                item.strip()
                for item in os.getenv("NOVAID_WEBAUTHN_ORIGINS", "http://localhost").split(",")
                if item.strip()
            ),
            require_user_verification=os.getenv("NOVAID_WEBAUTHN_REQUIRE_UV", "true").lower()
            == "true",
            attestation=os.getenv("NOVAID_WEBAUTHN_ATTESTATION", "none"),
        ),
        metrics=metrics,
        tracer=tracer,
        token_pepper=pepper,
        coordinator=(
            RedisWebAuthnChallengeCoordinator(
                redis_client,
                required=os.getenv("NOVAID_WEBAUTHN_REDIS_REQUIRED", "false").lower() == "true",
                metrics=metrics,
            )
            if redis_url and redis_client
            else None
        ),
        distributed_outbox=distributed_outbox,
    )
    recovery_codes = RecoveryCodeService(uow, pepper=pepper, metrics=metrics, tracer=tracer)
    account_recovery = AccountRecoveryService(uow, recovery_codes, outbox=outbox)
    webauthn_policies = TenantWebAuthnPolicyService(uow, distributed_outbox=distributed_outbox)
    router = build_durable_authentication_router(
        authentication,
        tokens=tokens,
        passwords=passwords,
        sessions=sessions,
        metrics=metrics,
        tracer=tracer,
        webauthn_service=webauthn_service,
        recovery_codes=recovery_codes,
        account_recovery=account_recovery,
        webauthn_policies=webauthn_policies,
        provisional_tokens=provisional_tokens,
    )
    setattr(
        router,
        "novaid_provisional_attestation_claims",
        lambda authorization, tenant_id: provisional_tokens.validate(
            authorization[7:] if authorization.startswith("Bearer ") else "",
            expected_tenant=tenant_id,
        ),
    )
    setattr(router, "novaid_c24_uow_provider", c24_uow_provider)

    from afritech.novaid.application.security_events import (
        SecurityEventAuthority,
    )
    from afritech.novaid.application.novatrust_identity_risk import (
        NovaTrustIdentityRiskAuthority,
    )
    from afritech.novaid.application.device_attestation import (
        PersistedDeviceTrustSignalResolver,
    )

    security_events = SecurityEventAuthority(uow)

    setattr(
        router,
        "novaid_security_events",
        security_events,
    )

    novatrust_identity_risk = NovaTrustIdentityRiskAuthority(
        signal_resolver=PersistedDeviceTrustSignalResolver(
            c24_uow_provider
        ),
        security_events=security_events,
        freshness_seconds=int(
            os.getenv(
                "NOVATRUST_IDENTITY_RISK_TTL_SECONDS",
                "300",
            )
        ),
    )

    setattr(
        router,
        "novaid_novatrust_identity_risk",
        novatrust_identity_risk,
    )

    def _activate_device_attestation(result, claims):
        from datetime import UTC, datetime
        from afritech.novaid.application.novatrust_identity_risk import (
            NovaTrustIdentityRiskRequest,
            NovaTrustOutcome,
        )

        request = NovaTrustIdentityRiskRequest(
            tenant_id=result.tenant_id,
            organization_id=result.tenant_id,
            subject_id=result.subject_id,
            session_id=str(claims["session_id"]),
            provider_id=result.provider,
            authentication_strength="PASSWORD_OTP",
            correlation_id=result.correlation_id,
            request_id=result.request_id,
            evaluated_at=datetime.now(UTC),
            device_id=result.device_id,
        )

        decision = novatrust_identity_risk.evaluate(request)

        if decision.outcome is not NovaTrustOutcome.ALLOW:
            raise RuntimeError(
                "NOVATRUST_DEVICE_ACTIVATION_DENIED"
            )

        activated = authentication.activate_device_attested_session(
            tenant_id=result.tenant_id,
            session_id=str(claims["session_id"]),
            identity_id=result.subject_id,
            device_id=result.device_id,
            challenge_id=result.challenge_id,
            trust_outcome=decision.outcome.value,
            correlation_id=result.correlation_id,
            request_id=result.request_id,
        )

        activated["access_token"] = tokens.issue(
            result.tenant_id,
            activated["session_id"],
            activated["membership_id"],
        )

        return activated

    setattr(
        router,
        "novaid_device_attestation_activate",
        _activate_device_attestation,
    )
    setattr(router, "novaid_postgres_pool", pool)
    setattr(router, "novaid_outbox", outbox)
    setattr(router, "novaid_metrics", metrics)
    setattr(router, "novaid_tracer", tracer)
    setattr(router, "novaid_redis_client", redis_client if redis_url else None)
    setattr(router, "novaid_webauthn_outbox", distributed_outbox)
    if redis_url and redis_client:
        publisher_uow = PostgresNovaIdUnitOfWork(pool=pool) if pool else uow
        consumer_uow = PostgresNovaIdUnitOfWork(pool=pool) if pool else uow
        distributed_publisher_outbox = WebAuthnOutboxRepository(publisher_uow)
        setattr(
            router,
            "novaid_webauthn_publisher",
            WebAuthnOutboxPublisher(
                distributed_publisher_outbox,
                redis_client,
                instance_id=os.getenv("NOVAID_SERVICE_INSTANCE_ID", "novaid-local"),
                metrics=metrics,
                tracer=tracer,
            ),
        )
        setattr(
            router,
            "novaid_webauthn_consumer",
            WebAuthnDistributedEventConsumer(
                redis_client,
                consumer_name=os.getenv("NOVAID_SERVICE_INSTANCE_ID", "novaid-local"),
                metrics=metrics,
                uow=consumer_uow,
            ),
        )
        setattr(
            router,
            "novaid_revocation_publisher",
            RevocationPublisher(
                outbox,
                redis_client,
                instance_id=os.getenv("NOVAID_INSTANCE_ID", "novaid-local"),
                metrics=metrics,
                tracer=tracer,
            ),
        )
        setattr(
            router,
            "novaid_revocation_consumer",
            RevocationConsumer(redis_client, uow=consumer_uow, metrics=metrics, tracer=tracer),
        )
    return router


def _load_signing_keyring(*, require_rotation: bool) -> tuple[dict[str, bytes], str]:
    encoded_registry = os.getenv("NOVAID_SIGNING_KEYS_JSON", "")
    active_key_id = os.getenv("NOVAID_ACTIVE_SIGNING_KEY_ID", "")
    if encoded_registry:
        try:
            parsed = json.loads(encoded_registry)
        except json.JSONDecodeError as exc:
            raise RuntimeError("invalid_novaid_signing_key_registry") from exc
        if not isinstance(parsed, dict) or not parsed:
            raise RuntimeError("invalid_novaid_signing_key_registry")
        keys = {
            str(key_id): str(secret).encode()
            for key_id, secret in parsed.items()
        }
        if (
            not active_key_id
            or active_key_id not in keys
            or any(len(secret) < 32 for secret in keys.values())
        ):
            raise RuntimeError("invalid_novaid_signing_key_registry")
        return keys, active_key_id
    if require_rotation:
        raise RuntimeError("missing_novaid_signing_key_registry")
    legacy_key = os.getenv(
        "NOVAID_SIGNING_KEY",
        "development-only-signing-key-00001",
    ).encode()
    if len(legacy_key) < 32:
        raise RuntimeError("invalid_novaid_signing_key")
    return {"development-v1": legacy_key}, "development-v1"
