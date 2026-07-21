from __future__ import annotations

import pytest

from afritech.novaride_runtime.config import (
    EventFabricAdapter,
    KafkaSettings,
    NovaRideRuntimeSettings,
    PersistenceAdapter,
    RuntimeEnvironment,
    create_runtime_from_settings,
)


def _base_settings(**overrides):
    values = dict(
        environment=RuntimeEnvironment.DEVELOPMENT,
        region="AU",
        availability_zone="local-a",
        persistence_adapter=PersistenceAdapter.MEMORY,
        event_fabric_adapter=EventFabricAdapter.MEMORY,
        postgres_dsn="",
        redis_dsn="",
        kafka=KafkaSettings(bootstrap_servers="", security_protocol="SASL_SSL"),
        provider_probe_interval_seconds=30,
        provider_probe_timeout_seconds=2.0,
        outbox_poll_interval_seconds=1.0,
        outbox_batch_size=100,
        sync_batch_max_operations=100,
        sync_payload_max_bytes=256_000,
        retention_offline_operations_days=30,
        retention_evidence_days=365,
        evidence_signing_key_ref="test-key",
        metrics_enabled=True,
        otel_endpoint="",
        alert_webhook_ref="",
        emergency_mode_enabled=False,
        feature_flags={"real_payments": False, "ga_allowed": False},
    )
    values.update(overrides)
    return NovaRideRuntimeSettings(**values)


def test_production_rejects_memory_persistence() -> None:
    settings = _base_settings(environment=RuntimeEnvironment.PRODUCTION)
    with pytest.raises(ValueError, match="production_settings_missing"):
        settings.validate()


def test_runtime_factory_rejects_production_memory_persistence() -> None:
    settings = _base_settings(environment=RuntimeEnvironment.PRODUCTION)
    with pytest.raises(ValueError, match="production_settings_missing"):
        create_runtime_from_settings(settings)


def test_development_allows_memory_persistence() -> None:
    settings = _base_settings()
    runtime = create_runtime_from_settings(settings)
    assert runtime.policy.ga_allowed is False
