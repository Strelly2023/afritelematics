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
    CONTROLLED_PILOT = "controlled_pilot"
    PUBLIC_PILOT = "public_pilot"
    PRODUCTION = "production"


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
            if not self.kafka.bootstrap_servers:
                missing.append("NOVARIDE_KAFKA_BOOTSTRAP_SERVERS")
            if not self.evidence_signing_key_ref:
                missing.append("NOVARIDE_EVIDENCE_SIGNING_KEY_REF")
            if missing:
                raise ValueError("production_settings_missing:" + ",".join(missing))


def create_runtime_from_settings(settings: NovaRideRuntimeSettings) -> NovaRideRuntime:
    settings.validate()
    if (
        settings.environment == RuntimeEnvironment.PRODUCTION
        and settings.persistence_adapter == PersistenceAdapter.MEMORY
    ):
        raise RuntimeError("production_memory_persistence_forbidden")
    runtime = create_runtime()
    runtime.policy.ga_allowed = settings.feature_flags.get("ga_allowed", False)
    runtime.policy.real_payments_enabled = settings.feature_flags.get("real_payments", False)
    return runtime


def create_runtime_from_environment() -> NovaRideRuntime:
    return create_runtime_from_settings(NovaRideRuntimeSettings.from_env())
