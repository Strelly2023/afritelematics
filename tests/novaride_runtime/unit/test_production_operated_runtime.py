from __future__ import annotations

from afritech.novaride_runtime.config import NovaRideRuntimeSettings
from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.events.outbox import InMemoryOutboxStore, OutboxState
from afritech.novaride_runtime.kafka import InMemoryKafkaProducer, KafkaEventPublisher
from afritech.novaride_runtime.outbox import ProductionOutboxPublisher
from afritech.novaride_runtime.readiness import ReadinessEvidence, generate_readiness_certificate
from afritech.novaride_runtime.redis_coordination import (
    InMemoryKeyValueClient,
    RedisCoordinationService,
)
from afritech.novaride_runtime.sync_security import DeviceRegistry, sign_sync_payload


def test_production_settings_fail_closed_without_durable_dependencies() -> None:
    try:
        NovaRideRuntimeSettings.from_env({"NOVARIDE_ENVIRONMENT": "production"})
    except ValueError as exc:
        assert "production_settings_missing" in str(exc)
        assert "NOVARIDE_PERSISTENCE_ADAPTER=postgresql" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("production settings accepted missing durable dependencies")


def test_device_signature_rejects_replay_nonce() -> None:
    registry = DeviceRegistry({"device_123": "secret"}, max_clock_skew_seconds=999999999)
    payload = {"device_id": "device_123", "operations": []}
    timestamp = "2000000000"
    signature = sign_sync_payload(
        secret="secret", timestamp=timestamp, nonce="nonce-1", payload=payload
    )

    registry.validate(
        device_id="device_123",
        tenant_id="tenant",
        timestamp=timestamp,
        nonce="nonce-1",
        signature=signature,
        payload=payload,
    )
    try:
        registry.validate(
            device_id="device_123",
            tenant_id="tenant",
            timestamp=timestamp,
            nonce="nonce-1",
            signature=signature,
            payload=payload,
        )
    except ValueError as exc:
        assert str(exc) == "reused_nonce"
    else:  # pragma: no cover
        raise AssertionError("replayed nonce accepted")


def test_production_outbox_publishes_once_and_marks_ack() -> None:
    outbox = InMemoryOutboxStore()
    event = MobilityEvent(
        event_type="ResilienceEvidenceRecorded",
        aggregate_id="evidence_1",
        aggregate_type="ResilienceEvidence",
        aggregate_version=1,
        tenant_id="tenant",
        region="KE",
        actor_type="SYSTEM",
        actor_id="system",
        correlation_id="corr",
        causation_id=None,
        payload={"evidence_id": "evidence_1"},
    )
    outbox.append(event)
    producer = InMemoryKafkaProducer([])
    publisher = KafkaEventPublisher(
        __import__("afritech.novaride_runtime.config", fromlist=["KafkaSettings"]).KafkaSettings(),
        producer,
    )

    result = ProductionOutboxPublisher(outbox, publisher, "worker_1").run_once()

    assert result.published == 1
    assert outbox.records[event.event_id].state == OutboxState.PUBLISHED
    assert producer.sent[0]["topic"] == "novaride.resilience.events"


def test_redis_coordination_is_non_authoritative_and_rebuildable() -> None:
    coordination = RedisCoordinationService(InMemoryKeyValueClient())

    assert coordination.acquire_sync_lock("device_1", "nonce_1") is True
    assert coordination.acquire_sync_lock("device_1", "nonce_1") is False
    coordination.set_circuit_state("payment:primary", "OPEN")
    assert coordination.get_circuit_state("payment:primary") == "OPEN"
    coordination.broadcast_emergency_mode("KE", "EMERGENCY_ONLY")
    assert coordination.region_degraded_mode("KE") == "EMERGENCY_ONLY"


def test_readiness_certificate_cannot_overstate_ga_without_live_evidence() -> None:
    certificate = generate_readiness_certificate(
        ReadinessEvidence(
            environment="production",
            regions=("KE",),
            zones=("a", "b", "c"),
            test_results={"focused": "passed"},
            emergency_path_verified=True,
            unresolved_risks=("live_kafka_not_verified",),
        )
    )

    assert certificate["final_status"] != "READY_FOR_GA"
    assert certificate["evidence_hash"].startswith("sha256:")
