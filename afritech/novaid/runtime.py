from __future__ import annotations

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
    if len(os.getenv("NOVAID_SIGNING_KEY", "").encode()) < 32:
        raise RuntimeError("invalid_novaid_signing_key")
    if os.getenv("NOVAID_REDIS_REQUIRED", "true").lower() == "true" and not os.getenv(
        "NOVAID_REDIS_URL"
    ):
        raise RuntimeError("required_novaid_redis_url_missing")


def build_default_durable_router():
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
    pepper = os.getenv("NOVAID_TOKEN_PEPPER", "development-only-novaid-pepper-0001").encode()
    signing = os.getenv("NOVAID_SIGNING_KEY", "development-only-signing-key-00001").encode()
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
    authentication = DurableAuthenticationService(uow, pepper=pepper, lockout=lockout)
    passwords = PasswordLifecycleService(uow, revocations, pepper=pepper, outbox=outbox)
    sessions = SessionAdministrationService(
        uow, revocations, outbox=outbox, metrics=metrics, tracer=tracer
    )
    tokens = AccessTokenService(
        uow,
        revocations,
        signing_key=signing,
        issuer=config.jwt_issuer or "novaid-development",
        audience=config.jwt_audience or "novaid-development-clients",
        lifetime_seconds=config.access_token_seconds,
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
