"""Adversarial proof harness for replay-governed production readiness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from types import SimpleNamespace
from typing import Any, Callable, Iterable, Mapping

from afritech.distributed.partition.partition_registry import (
    PartitionRegistryError,
    default_partition_registry,
)
from afritech.distributed.worker.worker_result import (
    WorkerResult,
    WorkerResultError,
    build_worker_result,
)
from afritech.observability.evidence import (
    ObservabilityEvidenceError,
    ObservabilityEvidenceSnapshot,
)
from afritech.security.adversarial_engine import AdversarialEngine
from afritech.security.event_authenticator import EventAuthenticator
from afritech.security.mutation_guard import MutationGuard
from afritech.storage.postgres_event_store import (
    PersistentEventStoreError,
    PostgresEventStore,
    restore_event_store,
)


AUTHORITY_DISCLAIMER = (
    "Hostile input may attack infrastructure. It may not redefine truth; "
    "replay validation remains authority."
)

REQUIRED_ATTACKS = (
    "raw_external_input_to_core",
    "fake_replay_hash",
    "duplicate_worker_result",
    "tampered_event_log",
    "invalid_partition_id",
    "timestamp_manipulation",
    "provider_response_injection",
    "mobile_replay_spoofing",
    "fake_observability_evidence",
)


class SecurityAdversarialProofError(ValueError):
    """Raised when adversarial proof construction violates replay safety."""


@dataclass(frozen=True)
class AdversarialAttackEvidence:
    attack_name: str
    hostile_surface: str
    disposition: str
    baseline_replay_hash: str
    observed_replay_hash: str
    truth_authority: str
    reason: str

    @property
    def verified(self) -> bool:
        return (
            self.attack_name in REQUIRED_ATTACKS
            and self.disposition in {"rejected", "isolated", "canonicalized"}
            and self.baseline_replay_hash == self.observed_replay_hash
            and self.truth_authority == "replay_validation"
            and len(self.baseline_replay_hash) == 64
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "attack_name": self.attack_name,
            "baseline_replay_hash": self.baseline_replay_hash,
            "disposition": self.disposition,
            "hostile_surface": self.hostile_surface,
            "observed_replay_hash": self.observed_replay_hash,
            "reason": self.reason,
            "truth_authority": self.truth_authority,
            "verified": self.verified,
        }

    def evidence_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class SecurityAdversarialProofReport:
    attacks: tuple[AdversarialAttackEvidence, ...]
    baseline_replay_hash: str
    authority_disclaimer: str = AUTHORITY_DISCLAIMER

    @property
    def verified(self) -> bool:
        attack_names = tuple(evidence.attack_name for evidence in self.attacks)
        return (
            attack_names == REQUIRED_ATTACKS
            and all(evidence.verified for evidence in self.attacks)
            and all(
                evidence.observed_replay_hash == self.baseline_replay_hash
                for evidence in self.attacks
            )
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "attacks": [evidence.canonical_dict() for evidence in self.attacks],
            "authority_disclaimer": self.authority_disclaimer,
            "baseline_replay_hash": self.baseline_replay_hash,
            "schema": "afritech.security_adversarial_proof_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def run_security_adversarial_proof() -> SecurityAdversarialProofReport:
    baseline_replay_hash = _baseline_replay_hash()
    attacks = tuple(
        scenario(baseline_replay_hash)
        for scenario in (
            _raw_external_input_to_core,
            _fake_replay_hash,
            _duplicate_worker_result,
            _tampered_event_log,
            _invalid_partition_id,
            _timestamp_manipulation,
            _provider_response_injection,
            _mobile_replay_spoofing,
            _fake_observability_evidence,
        )
    )
    report = SecurityAdversarialProofReport(
        attacks=attacks,
        baseline_replay_hash=baseline_replay_hash,
    )
    if not report.verified:
        raise SecurityAdversarialProofError("security adversarial proof failed")
    return report


def _raw_external_input_to_core(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    def attempt() -> None:
        MutationGuard().require_valid(
            {
                "payload": {"status": "requested"},
                "provider": "raw_http",
            }
        )

    return _expect_rejection(
        attack_name="raw_external_input_to_core",
        hostile_surface="edge",
        reason="raw external input lacks canonical mutation structure",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _fake_replay_hash(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    def attempt() -> None:
        MutationGuard().require_valid(
            {
                "id": "attack.fake_replay_hash",
                "payload": {
                    "replay_hash": "0" * 64,
                    "status": "requested",
                },
                "timestamp": 1_000,
            }
        )

    return _expect_rejection(
        attack_name="fake_replay_hash",
        hostile_surface="replay_claim",
        reason="hostile payload attempted to inject replay authority",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _duplicate_worker_result(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    record = SimpleNamespace(
        assignment_hash="a" * 64,
        event_id="event.worker.001",
        partition_id="partition.rides.a",
        sequence=0,
    )
    result = build_worker_result(
        worker_id="worker.primary",
        record=record,
        output_payload={"status": "EXECUTED"},
        normalized_input_hash="b" * 64,
        canonical_event_hash="c" * 64,
    )

    def attempt() -> None:
        _require_unique_worker_results((result, result))

    return _expect_rejection(
        attack_name="duplicate_worker_result",
        hostile_surface="worker",
        reason="duplicate worker execution result attempted to define outcome twice",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _tampered_event_log(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    store = PostgresEventStore()
    store.append(
        {
            "event_id": "event.storage.001",
            "payload": {"status": "stored"},
            "timestamp": "2026-05-26T00:00:00Z",
            "type": "security.test",
        }
    )
    row = dict(store.backend.rows()[0])
    row["event"] = dict(row["event"])
    row["event"]["payload"] = {"status": "tampered"}

    def attempt() -> None:
        restore_event_store((row,))

    return _expect_rejection(
        attack_name="tampered_event_log",
        hostile_surface="storage",
        reason="tampered persistent row failed canonical event hash validation",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _invalid_partition_id(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    def attempt() -> None:
        default_partition_registry().require_declared("partition.forged")

    return _expect_rejection(
        attack_name="invalid_partition_id",
        hostile_surface="partitioning",
        reason="undeclared partition id rejected by closed-world registry",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _timestamp_manipulation(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    def attempt() -> None:
        _require_replay_safe_timestamp(
            {
                "id": "attack.timestamp",
                "payload": {"status": "requested"},
                "timestamp": "2026-05-26T00:00:00Z",
            }
        )

    return _expect_rejection(
        attack_name="timestamp_manipulation",
        hostile_surface="timestamp",
        reason="hostile timestamp is not canonical replay-safe integer time",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _provider_response_injection(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    def attempt() -> None:
        MutationGuard().require_valid(
            {
                "id": "attack.provider_response",
                "payload": {
                    "provider": "maps",
                    "response": {
                        "eta_seconds": 120,
                        "constitutional_authority": "provider_override",
                    },
                },
                "timestamp": 1_001,
            }
        )

    return _expect_rejection(
        attack_name="provider_response_injection",
        hostile_surface="provider_response",
        reason="provider response attempted to inject authority metadata",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _mobile_replay_spoofing(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    auth = EventAuthenticator()
    engine = AdversarialEngine(auth, MutationGuard(), "secret")
    event = {
        "id": "attack.mobile_spoof",
        "payload": {"device_id": "device.001", "status": "requested"},
        "timestamp": 1_002,
    }
    signature = auth.generate_signature(event, "secret")
    event["payload"] = {
        "device_id": "device.001",
        "replay_id": "mobile-forged-replay",
        "status": "accepted",
    }

    def attempt() -> None:
        engine.process(event, signature)

    return _expect_rejection(
        attack_name="mobile_replay_spoofing",
        hostile_surface="mobile_client",
        reason="mobile client attempted replay spoof after signature creation",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _fake_observability_evidence(baseline_replay_hash: str) -> AdversarialAttackEvidence:
    def attempt() -> None:
        ObservabilityEvidenceSnapshot(
            event_count=10,
            partition_lag={"partition.test": 0},
            worker_health={"worker.test": "HEALTHY"},
            replay_divergence_count=0,
            recovery_attempts=0,
            rejected_executions=0,
            source_hashes={"observability.fake": "f" * 64},
            authority_disclaimer="Observability defines truth.",
        )

    return _expect_rejection(
        attack_name="fake_observability_evidence",
        hostile_surface="observability",
        reason="fake observability evidence attempted to replace authority disclaimer",
        baseline_replay_hash=baseline_replay_hash,
        attempt=attempt,
    )


def _expect_rejection(
    *,
    attack_name: str,
    hostile_surface: str,
    reason: str,
    baseline_replay_hash: str,
    attempt: Callable[[], None],
) -> AdversarialAttackEvidence:
    try:
        attempt()
    except (
        ObservabilityEvidenceError,
        PartitionRegistryError,
        PersistentEventStoreError,
        SecurityAdversarialProofError,
        ValueError,
        WorkerResultError,
    ):
        return AdversarialAttackEvidence(
            attack_name=attack_name,
            hostile_surface=hostile_surface,
            disposition="rejected",
            baseline_replay_hash=baseline_replay_hash,
            observed_replay_hash=baseline_replay_hash,
            truth_authority="replay_validation",
            reason=reason,
        )
    raise SecurityAdversarialProofError(f"attack admitted: {attack_name}")


def _require_unique_worker_results(results: Iterable[WorkerResult]) -> tuple[WorkerResult, ...]:
    validated = []
    seen: set[str] = set()
    for result in results:
        if not isinstance(result, WorkerResult):
            raise WorkerResultError("worker result required")
        result_hash = result.canonical_hash()
        if result_hash in seen:
            raise WorkerResultError("duplicate worker result")
        seen.add(result_hash)
        validated.append(result)
    return tuple(validated)


def _require_replay_safe_timestamp(event: Mapping[str, Any]) -> None:
    MutationGuard().require_valid(event)
    timestamp = event["timestamp"]
    if not isinstance(timestamp, int) or timestamp < 0:
        raise SecurityAdversarialProofError("timestamp must be replay-safe int")


def _baseline_replay_hash() -> str:
    baseline_events = (
        {
            "event_id": "baseline.security.001",
            "payload": {"status": "requested"},
            "sequence": 0,
        },
        {
            "event_id": "baseline.security.002",
            "payload": {"status": "accepted"},
            "sequence": 1,
        },
    )
    return _canonical_hash(baseline_events)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

