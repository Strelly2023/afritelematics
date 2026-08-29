"""NovaRide production runtime settings and runtime factory."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

from afritech.novaride_runtime.services import NovaRideRuntime, create_runtime


class RuntimeEnvironment(StrEnum):
    TEST = "test"
    DEVELOPMENT = "development"
    QA = "qa"
    STAGING = "staging"
    CONTROLLED_PILOT = "controlled_pilot"
    PUBLIC_PILOT = "public_pilot"
    PRODUCTION = "production"

    @property
    def promotion_rank(self) -> int:
        return _PROMOTION_RANK[self]

    @property
    def is_pilot(self) -> bool:
        return self in {
            RuntimeEnvironment.CONTROLLED_PILOT,
            RuntimeEnvironment.PUBLIC_PILOT,
        }

    @property
    def production_like(self) -> bool:
        return self in {
            RuntimeEnvironment.CONTROLLED_PILOT,
            RuntimeEnvironment.PUBLIC_PILOT,
            RuntimeEnvironment.PRODUCTION,
        }


_PROMOTION_RANK = {
    RuntimeEnvironment.DEVELOPMENT: 10,
    RuntimeEnvironment.TEST: 20,
    RuntimeEnvironment.QA: 30,
    RuntimeEnvironment.STAGING: 40,
    RuntimeEnvironment.CONTROLLED_PILOT: 50,
    RuntimeEnvironment.PUBLIC_PILOT: 60,
    RuntimeEnvironment.PRODUCTION: 70,
}

_ENVIRONMENT_ALIASES = {
    "dev": RuntimeEnvironment.DEVELOPMENT,
    "development": RuntimeEnvironment.DEVELOPMENT,
    "local": RuntimeEnvironment.DEVELOPMENT,
    "test": RuntimeEnvironment.TEST,
    "testing": RuntimeEnvironment.TEST,
    "qa": RuntimeEnvironment.QA,
    "quality-assurance": RuntimeEnvironment.QA,
    "quality_assurance": RuntimeEnvironment.QA,
    "stage": RuntimeEnvironment.STAGING,
    "staging": RuntimeEnvironment.STAGING,
    "controlled-pilot": RuntimeEnvironment.CONTROLLED_PILOT,
    "controlled_pilot": RuntimeEnvironment.CONTROLLED_PILOT,
    "controlledpilot": RuntimeEnvironment.CONTROLLED_PILOT,
    "public-pilot": RuntimeEnvironment.PUBLIC_PILOT,
    "public_pilot": RuntimeEnvironment.PUBLIC_PILOT,
    "publicpilot": RuntimeEnvironment.PUBLIC_PILOT,
    "prod": RuntimeEnvironment.PRODUCTION,
    "production": RuntimeEnvironment.PRODUCTION,
}


class NovaRideEnvironmentError(ValueError):
    """Base error for invalid NovaRide environment configuration."""


class NovaRideEnvironmentIsolationError(NovaRideEnvironmentError):
    """Raised when one environment attempts to consume another scope."""


@dataclass(frozen=True, slots=True)
class NovaRideEnvironmentProfile:
    """Immutable logical authorities assigned to one runtime environment.

    Scope values are identifiers only. They never contain credentials or
    secret material.
    """

    environment: RuntimeEnvironment
    namespace: str
    secret_scope: str
    api_credential_scope: str
    payment_credential_scope: str
    database_credential_scope: str
    signing_scope: str
    feature_flag_scope: str

    def __post_init__(self) -> None:
        for field_name in (
            "namespace",
            "secret_scope",
            "api_credential_scope",
            "payment_credential_scope",
            "database_credential_scope",
            "signing_scope",
            "feature_flag_scope",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise NovaRideEnvironmentError(
                    f"{field_name} must be a non-empty logical scope"
                )
            if value != value.strip():
                raise NovaRideEnvironmentError(
                    f"{field_name} must not contain surrounding whitespace"
                )


def normalize_novaride_environment(
    value: RuntimeEnvironment | str,
) -> RuntimeEnvironment:
    """Resolve an explicit environment without defaulting to production."""

    if isinstance(value, RuntimeEnvironment):
        return value
    if not isinstance(value, str):
        raise NovaRideEnvironmentError(
            "NovaRide environment must be a string or RuntimeEnvironment"
        )

    normalized = value.strip().lower()
    if not normalized:
        raise NovaRideEnvironmentError("NovaRide environment must not be empty")

    environment = _ENVIRONMENT_ALIASES.get(normalized)
    if environment is None:
        allowed = ", ".join(item.value for item in RuntimeEnvironment)
        raise NovaRideEnvironmentError(
            f"Unsupported NovaRide environment {value!r}; expected one of: {allowed}"
        )
    return environment


def environment_profile(
    environment: RuntimeEnvironment | str,
) -> NovaRideEnvironmentProfile:
    """Build the canonical isolated logical scopes for an environment."""

    resolved = normalize_novaride_environment(environment)
    scope = resolved.value
    return NovaRideEnvironmentProfile(
        environment=resolved,
        namespace=f"novaride-{scope}",
        secret_scope=scope,
        api_credential_scope=scope,
        payment_credential_scope=scope,
        database_credential_scope=scope,
        signing_scope=scope,
        feature_flag_scope=scope,
    )


def validate_environment_isolation(profile: NovaRideEnvironmentProfile) -> None:
    """Reject logical authorities that cross environment boundaries."""

    expected = profile.environment.value
    scoped_fields = {
        "secret_scope": profile.secret_scope,
        "api_credential_scope": profile.api_credential_scope,
        "payment_credential_scope": profile.payment_credential_scope,
        "database_credential_scope": profile.database_credential_scope,
        "signing_scope": profile.signing_scope,
        "feature_flag_scope": profile.feature_flag_scope,
    }
    mismatches = sorted(
        field_name
        for field_name, value in scoped_fields.items()
        if value != expected
    )
    if mismatches:
        raise NovaRideEnvironmentIsolationError(
            "NovaRide cross-environment authority rejected: "
            f"{', '.join(mismatches)} do not match environment {expected!r}"
        )

    expected_namespace = f"novaride-{expected}"
    if profile.namespace != expected_namespace:
        raise NovaRideEnvironmentIsolationError(
            "NovaRide namespace isolation rejected: "
            f"expected {expected_namespace!r}"
        )


def assert_promotion(
    source: RuntimeEnvironment | str,
    destination: RuntimeEnvironment | str,
) -> None:
    """Require a strictly forward environment promotion."""

    source_environment = normalize_novaride_environment(source)
    destination_environment = normalize_novaride_environment(destination)
    if destination_environment.promotion_rank <= source_environment.promotion_rank:
        raise NovaRideEnvironmentIsolationError(
            "NovaRide environment promotion must move forward: "
            f"{source_environment.value!r} -> {destination_environment.value!r}"
        )


class ManagedCredentialKind(StrEnum):
    SIGNING = "signing"
    PAYMENT = "payment"
    DATABASE = "database"
    CERTIFICATE = "certificate"


_MANAGED_CREDENTIAL_PROVIDERS = {
    "aws-secrets-manager",
    "azure-key-vault",
    "gcp-secret-manager",
    "kms",
    "vault",
}


@dataclass(frozen=True, slots=True)
class ManagedCredentialReference:
    """Opaque reference to credential material held outside source control."""

    kind: ManagedCredentialKind
    provider: str
    environment_scope: str
    resource: str

    def __post_init__(self) -> None:
        for field_name in ("provider", "environment_scope", "resource"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise NovaRideEnvironmentError(f"{field_name} must be non-empty")
            if value != value.strip():
                raise NovaRideEnvironmentError(
                    f"{field_name} must not contain surrounding whitespace"
                )

        if "://" in self.resource or any(
            marker in self.resource.lower()
            for marker in ("password=", "secret=", "token=", "private_key=")
        ):
            raise NovaRideEnvironmentError(
                "credential resource must be an opaque identifier, not credential material"
            )

    @property
    def reference(self) -> str:
        return f"{self.provider}://{self.environment_scope}/{self.resource}"


@dataclass(frozen=True, slots=True)
class NovaRideCredentialCustody:
    """Managed credential and certificate authorities for one environment."""

    environment: RuntimeEnvironment
    signing: ManagedCredentialReference
    payment: ManagedCredentialReference
    database: ManagedCredentialReference
    certificate: ManagedCredentialReference
    certificate_rotation_days: int


def managed_credential_reference(
    *,
    kind: ManagedCredentialKind,
    provider: str,
    environment: RuntimeEnvironment | str,
    resource: str,
) -> ManagedCredentialReference:
    """Create a typed opaque reference bound to one environment scope."""

    resolved = normalize_novaride_environment(environment)
    return ManagedCredentialReference(
        kind=kind,
        provider=provider.strip().lower(),
        environment_scope=resolved.value,
        resource=resource,
    )


def validate_credential_custody(custody: NovaRideCredentialCustody) -> None:
    """Fail closed on cross-environment or unmanaged credential custody."""

    expected_kinds = {
        "signing": ManagedCredentialKind.SIGNING,
        "payment": ManagedCredentialKind.PAYMENT,
        "database": ManagedCredentialKind.DATABASE,
        "certificate": ManagedCredentialKind.CERTIFICATE,
    }
    for field_name, expected_kind in expected_kinds.items():
        reference = getattr(custody, field_name)
        if reference.kind is not expected_kind:
            raise NovaRideEnvironmentIsolationError(
                f"{field_name} credential kind must be {expected_kind.value!r}"
            )
        if reference.environment_scope != custody.environment.value:
            raise NovaRideEnvironmentIsolationError(
                f"{field_name} credential scope does not match "
                f"environment {custody.environment.value!r}"
            )
        if (
            custody.environment.production_like
            and reference.provider not in _MANAGED_CREDENTIAL_PROVIDERS
        ):
            raise NovaRideEnvironmentIsolationError(
                f"{field_name} credential requires managed custody in "
                f"environment {custody.environment.value!r}"
            )

    if custody.certificate_rotation_days <= 0:
        raise NovaRideEnvironmentError(
            "certificate_rotation_days must be positive"
        )
    if custody.environment.production_like and custody.certificate_rotation_days > 90:
        raise NovaRideEnvironmentIsolationError(
            "production-like certificate rotation must not exceed 90 days"
        )


class PersistenceAdapter(StrEnum):
    MEMORY = "memory"
    POSTGRESQL = "postgresql"


class EventFabricAdapter(StrEnum):
    MEMORY = "memory"
    KAFKA_OUTBOX = "kafka_outbox"


@dataclass(frozen=True, slots=True)
class KafkaSettings:
    bootstrap_servers: str = ""
    security_protocol: str = "SASL_SSL"
    topics: dict[str, str] = field(
        default_factory=lambda: {
            "runtime": "novaride.runtime.events",
            "resilience": "novaride.resilience.events",
            "mobile_sync": "novaride.mobile.sync.events",
            "provider_health": "novaride.provider.health.events",
            "failover": "novaride.failover.events",
            "evidence": "novaride.evidence.events",
            "deadletter": "novaride.deadletter.events",
        }
    )


@dataclass(frozen=True, slots=True)
class NovaRideRuntimeSettings:
    environment: RuntimeEnvironment
    region: str
    availability_zone: str
    persistence_adapter: PersistenceAdapter
    event_fabric_adapter: EventFabricAdapter
    postgres_dsn: str = ""
    redis_dsn: str = ""
    kafka: KafkaSettings = field(default_factory=KafkaSettings)
    provider_probe_interval_seconds: int = 30
    provider_probe_timeout_seconds: float = 2.0
    outbox_poll_interval_seconds: float = 1.0
    outbox_batch_size: int = 100
    sync_batch_max_operations: int = 100
    sync_payload_max_bytes: int = 256_000
    retention_offline_operations_days: int = 30
    retention_evidence_days: int = 365
    evidence_signing_key_ref: str = ""
    metrics_enabled: bool = True
    otel_endpoint: str = ""
    alert_webhook_ref: str = ""
    emergency_mode_enabled: bool = False
    feature_flags: dict[str, bool] = field(default_factory=dict)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "NovaRideRuntimeSettings":
        values = env or os.environ
        environment = RuntimeEnvironment(values.get("NOVARIDE_ENVIRONMENT", "development"))
        persistence = PersistenceAdapter(values.get("NOVARIDE_PERSISTENCE_ADAPTER", "memory"))
        event_adapter = EventFabricAdapter(values.get("NOVARIDE_EVENT_FABRIC_ADAPTER", "memory"))
        topics = {
            "runtime": values.get("NOVARIDE_KAFKA_TOPIC_RUNTIME", "novaride.runtime.events"),
            "resilience": values.get(
                "NOVARIDE_KAFKA_TOPIC_RESILIENCE", "novaride.resilience.events"
            ),
            "mobile_sync": values.get(
                "NOVARIDE_KAFKA_TOPIC_MOBILE_SYNC", "novaride.mobile.sync.events"
            ),
            "provider_health": values.get(
                "NOVARIDE_KAFKA_TOPIC_PROVIDER_HEALTH", "novaride.provider.health.events"
            ),
            "failover": values.get("NOVARIDE_KAFKA_TOPIC_FAILOVER", "novaride.failover.events"),
            "evidence": values.get("NOVARIDE_KAFKA_TOPIC_EVIDENCE", "novaride.evidence.events"),
            "deadletter": values.get(
                "NOVARIDE_KAFKA_TOPIC_DEADLETTER", "novaride.deadletter.events"
            ),
        }
        settings = cls(
            environment=environment,
            region=values.get("NOVARIDE_REGION", "AU"),
            availability_zone=values.get("NOVARIDE_AVAILABILITY_ZONE", "local-a"),
            persistence_adapter=persistence,
            event_fabric_adapter=event_adapter,
            postgres_dsn=values.get("NOVARIDE_POSTGRES_DSN", ""),
            redis_dsn=values.get("NOVARIDE_REDIS_DSN", ""),
            kafka=KafkaSettings(
                bootstrap_servers=values.get("NOVARIDE_KAFKA_BOOTSTRAP_SERVERS", ""),
                security_protocol=values.get("NOVARIDE_KAFKA_SECURITY_PROTOCOL", "SASL_SSL"),
                topics=topics,
            ),
            provider_probe_interval_seconds=int(
                values.get("NOVARIDE_PROVIDER_PROBE_INTERVAL_SECONDS", "30")
            ),
            provider_probe_timeout_seconds=float(
                values.get("NOVARIDE_PROVIDER_PROBE_TIMEOUT_SECONDS", "2.0")
            ),
            outbox_poll_interval_seconds=float(
                values.get("NOVARIDE_OUTBOX_POLL_INTERVAL_SECONDS", "1.0")
            ),
            outbox_batch_size=int(values.get("NOVARIDE_OUTBOX_BATCH_SIZE", "100")),
            sync_batch_max_operations=int(values.get("NOVARIDE_SYNC_BATCH_MAX_OPERATIONS", "100")),
            sync_payload_max_bytes=int(values.get("NOVARIDE_SYNC_PAYLOAD_MAX_BYTES", "256000")),
            retention_offline_operations_days=int(
                values.get("NOVARIDE_RETENTION_OFFLINE_OPERATIONS_DAYS", "30")
            ),
            retention_evidence_days=int(values.get("NOVARIDE_RETENTION_EVIDENCE_DAYS", "365")),
            evidence_signing_key_ref=values.get("NOVARIDE_EVIDENCE_SIGNING_KEY_REF", ""),
            metrics_enabled=values.get("NOVARIDE_METRICS_ENABLED", "true").lower() == "true",
            otel_endpoint=values.get("NOVARIDE_OTEL_ENDPOINT", ""),
            alert_webhook_ref=values.get("NOVARIDE_ALERT_WEBHOOK_REF", ""),
            emergency_mode_enabled=values.get("NOVARIDE_EMERGENCY_MODE_ENABLED", "false").lower()
            == "true",
            feature_flags={
                "real_payments": values.get("NOVARIDE_REAL_PAYMENTS_ENABLED", "false").lower()
                == "true",
                "ga_allowed": values.get("NOVARIDE_GA_ALLOWED", "false").lower() == "true",
            },
        )
        settings.validate()
        return settings

    def evidence_signing_provider(
        self,
        env: Mapping[str, str] | None = None,
    ):
        """Resolve NovaRide's configured replay-evidence signing authority.

        Production is fail-closed: the configured key reference must identify
        an explicit secret source and may never fall back to the deterministic
        development signing key.

        Supported reference syntax:
            env://VARIABLE_NAME

        The referenced value is a 32-byte Ed25519 seed encoded as exactly
        64 hexadecimal characters.
        """
        from afritech.security.key_manager import (
            DeterministicLocalSigningProvider,
        )

        if self.environment is not RuntimeEnvironment.PRODUCTION:
            return DeterministicLocalSigningProvider(
                signer_id="NOVARIDE_REPLAY_EVIDENCE",
            )

        key_ref = self.evidence_signing_key_ref.strip()

        if not key_ref:
            raise RuntimeError(
                "novaride_evidence_signing_key_ref_required"
            )

        prefix = "env://"

        if not key_ref.startswith(prefix):
            raise RuntimeError(
                "novaride_evidence_signing_key_ref_unsupported"
            )

        env_var = key_ref[len(prefix):].strip()

        if not env_var:
            raise RuntimeError(
                "novaride_evidence_signing_env_name_required"
            )

        values = env or os.environ
        seed_hex = values.get(env_var, "").strip()

        if not seed_hex:
            raise RuntimeError(
                "novaride_evidence_signing_secret_missing"
            )

        try:
            seed = bytes.fromhex(seed_hex)
        except ValueError as exc:
            raise RuntimeError(
                "novaride_evidence_signing_secret_invalid_hex"
            ) from exc

        if len(seed) != 32:
            raise RuntimeError(
                "novaride_evidence_signing_secret_invalid_length"
            )

        return DeterministicLocalSigningProvider(
            signer_id="NOVARIDE_REPLAY_EVIDENCE",
            seed=seed,
        )

    def validate(self) -> None:
        if not self.region:
            raise ValueError("novaride_region_required")
        if self.sync_batch_max_operations <= 0:
            raise ValueError("sync_batch_max_operations_must_be_positive")
        if self.sync_payload_max_bytes <= 0:
            raise ValueError("sync_payload_max_bytes_must_be_positive")
        if self.environment == RuntimeEnvironment.PRODUCTION:
            missing: list[str] = []
            if self.persistence_adapter != PersistenceAdapter.POSTGRESQL:
                missing.append("NOVARIDE_PERSISTENCE_ADAPTER=postgresql")
            if self.event_fabric_adapter != EventFabricAdapter.KAFKA_OUTBOX:
                missing.append("NOVARIDE_EVENT_FABRIC_ADAPTER=kafka_outbox")
            if not self.postgres_dsn:
                missing.append("NOVARIDE_POSTGRES_DSN")
            if not self.redis_dsn:
                missing.append("NOVARIDE_REDIS_DSN")
            elif not self.redis_dsn.lower().startswith("rediss://"):
                raise ValueError("production_redis_tls_required")
            if not self.kafka.bootstrap_servers:
                missing.append("NOVARIDE_KAFKA_BOOTSTRAP_SERVERS")
            if not self.evidence_signing_key_ref:
                missing.append("NOVARIDE_EVIDENCE_SIGNING_KEY_REF")
            if missing:
                raise ValueError("production_settings_missing:" + ",".join(missing))


def create_runtime_from_settings(
    settings: NovaRideRuntimeSettings,
) -> NovaRideRuntime:
    """Create the legacy non-operated runtime from validated settings.

    Production PostgreSQL persistence is operation-scoped and therefore
    cannot be represented safely by this long-lived runtime return type.
    Call ``create_postgres_runtime_bridge_from_settings`` for production
    PostgreSQL operations.
    """

    settings.validate()

    if (
        settings.environment
        == RuntimeEnvironment.PRODUCTION
        and settings.persistence_adapter
        == PersistenceAdapter.MEMORY
    ):
        raise RuntimeError(
            "production_memory_persistence_forbidden"
        )

    if (
        settings.environment
        == RuntimeEnvironment.PRODUCTION
        and settings.persistence_adapter
        == PersistenceAdapter.POSTGRESQL
    ):
        raise RuntimeError(
            "production_operated_runtime_required"
        )

    real_payments_enabled = (
        settings.feature_flags.get(
            "real_payments",
            False,
        )
    )

    if real_payments_enabled:
        raise RuntimeError(
            "novapay_production_provider_required"
        )

    runtime = create_runtime()

    runtime.policy.ga_allowed = (
        settings.feature_flags.get(
            "ga_allowed",
            False,
        )
    )

    return runtime


def create_postgres_runtime_bridge_from_settings(
    settings: NovaRideRuntimeSettings,
):
    """Compose the canonical tenant-scoped PostgreSQL operation bridge.

    Selection creates no database connection. Each business operation must
    supply its authoritative tenant identifier to ``PostgresRuntimeBridge``,
    which owns the short-lived session / transaction boundary.
    """

    settings.validate()

    if (
        settings.environment
        is not RuntimeEnvironment.PRODUCTION
    ):
        raise RuntimeError(
            "operated_runtime_requires_production"
        )

    if (
        settings.persistence_adapter
        is not PersistenceAdapter.POSTGRESQL
    ):
        raise RuntimeError(
            "production_postgres_persistence_required"
        )

    from afritech.novaride_runtime.persistence.runtime_selection import (
        PostgresRuntimeSelection,
        select_runtime_persistence,
    )
    from afritech.novaride_runtime.persistence.postgres.runtime_bridge import (
        PostgresRuntimeBridge,
    )

    selection = select_runtime_persistence(
        settings
    )

    if not isinstance(
        selection,
        PostgresRuntimeSelection,
    ):
        raise RuntimeError(
            "postgres_runtime_selection_required"
        )

    return PostgresRuntimeBridge(
        selection.session_factory
    )


def create_runtime_from_environment() -> NovaRideRuntime:
    return create_runtime_from_settings(NovaRideRuntimeSettings.from_env())
