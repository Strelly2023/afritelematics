"""Application services for system-level observability surfaces."""

from __future__ import annotations

from afriride_system.backend.api_gateway.gateway import AfriRideGateway
from afriride_system.backend.authority_runtime import (
    DOC_VERSION,
    assert_consistent_authority_hashes,
    authority_envelope,
)
from afriride_system.backend.evidence_engine import EvidenceEngine
from afriride_system.backend.proof_material import completed_ride, proof_events_for_ride
from afriride_system.backend.receipt_engine import ReceiptEngine
from afriride_system.backend.trace_enforcement import TraceEventLog
from afritech.partner_verification import build_partner_verification_packet


class SystemService:
    """Derive operator-facing system state from runtime and authoritative trace."""

    def __init__(self, gateway: AfriRideGateway, trace_log: TraceEventLog) -> None:
        self.gateway = gateway
        self.trace_log = trace_log

    def active_rides(self) -> dict[str, list[dict]]:
        return {"rides": self._active_rides()}

    def system_health(self) -> dict:
        summary = self.trace_log.integrity_summary()
        drivers = tuple(self.gateway.dispatcher.drivers.values())
        rides = tuple(self.gateway.dispatcher.rides.values())
        return {
            "status": "ok",
            "service": "afriride-api",
            "active_rides": sum(1 for ride in rides if ride.status != "COMPLETED"),
            "completed_rides": sum(1 for ride in rides if ride.status == "COMPLETED"),
            "drivers_online": sum(1 for driver in drivers if driver.online),
            "total_drivers": len(drivers),
            "replay_failures": summary["replay_failures"],
            "missing_traces": summary["missing_events"],
            "hash_chain_failures": summary["hash_chain_failures"],
            "invariant_contract": "five-invariant-contract",
            "enforcement_mode": "metadata-only",
        }

    def driver_operations(self) -> dict:
        rides = tuple(self.gateway.dispatcher.rides.values())
        drivers = sorted(self.gateway.dispatcher.drivers.values(), key=lambda item: item.driver_id)
        payload = []
        for driver in drivers:
            active_assignments = [
                ride.ride_id
                for ride in rides
                if ride.assigned_driver == driver.driver_id and ride.status != "COMPLETED"
            ]
            payload.append(
                {
                    "driver_id": driver.driver_id,
                    "online": driver.online,
                    "active_ride_ids": active_assignments,
                    "completed_rides": sum(
                        1
                        for ride in rides
                        if ride.assigned_driver == driver.driver_id and ride.status == "COMPLETED"
                    ),
                    "status": "ONLINE" if driver.online else "OFFLINE",
                }
            )
        return {
            "drivers": payload,
            "online_count": sum(1 for driver in drivers if driver.online),
            "total_count": len(drivers),
        }

    def replay_health(self) -> dict:
        summary = self.trace_log.integrity_summary()
        return {
            "replay_success_rate": summary["replay_success_rate"],
            "failures": summary["replay_failures"],
            "hash_chain_failures": summary["hash_chain_failures"],
            "last_failed_ride_id": summary["last_failed_ride_id"],
            "status": (
                "PASS"
                if summary["replay_failures"] == 0 and summary["hash_chain_failures"] == 0
                else "FAIL"
            ),
            "authority": _authority("replay_health"),
        }

    def evidence_pipeline(self) -> dict:
        summary = self.trace_log.integrity_summary()
        return {
            "receipts_count": summary["valid_traces"],
            "trace_count": summary["trace_count"],
            "missing_traces": summary["missing_events"],
            "hash_chain_failures": summary["hash_chain_failures"],
            "total_rides": summary["total_rides"],
            "valid_traces": summary["valid_traces"],
            "invalid_traces": summary["invalid_traces"],
            "authority": _authority("evidence_pipeline"),
        }

    def evidence_pipeline_summary(self) -> dict:
        summary = self.trace_log.integrity_summary()
        return {
            "summary": {
                "receipts_count": summary["valid_traces"],
                "trace_count": summary["trace_count"],
                "missing_traces": summary["missing_events"],
                "status": (
                    "healthy"
                    if summary["missing_events"] == 0 and summary["hash_chain_failures"] == 0
                    else "review"
                ),
            },
            "authority": _authority("evidence_pipeline_summary"),
        }

    def guard_violations(self) -> dict:
        summary = self.trace_log.integrity_summary()
        violations = []
        if summary["missing_events"]:
            violations.append(
                {
                    "type": "TRACE_COMPLETENESS",
                    "severity": "CRITICAL",
                    "timestamp": "runtime",
                    "details": {"missing_events": summary["missing_events"]},
                }
            )
        if summary["replay_failures"]:
            violations.append(
                {
                    "type": "REPLAY_DIVERGENCE",
                    "severity": "CRITICAL",
                    "timestamp": "runtime",
                    "details": {"failures": summary["replay_failures"]},
                }
            )
        if summary["hash_chain_failures"]:
            violations.append(
                {
                    "type": "TRACE_HASH_CHAIN_BREAK",
                    "severity": "CRITICAL",
                    "timestamp": "runtime",
                    "details": {"failures": summary["hash_chain_failures"]},
                }
            )
        return {"violations": violations}

    def guard_violations_summary(self) -> dict:
        violations = self.guard_violations()["violations"]
        if not violations:
            return {
                "summary": {
                    "violations_count": 0,
                    "highest_severity": "NONE",
                    "status": "healthy",
                }
            }
        severity_rank = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        highest = max(
            (str(violation.get("severity", "INFO")).upper() for violation in violations),
            key=lambda item: severity_rank.get(item, 0),
        )
        return {
            "summary": {
                "violations_count": len(violations),
                "highest_severity": highest,
                "status": "review",
            }
        }

    def trust_metrics(self) -> dict:
        summary = self.trace_log.integrity_summary()
        active_rides = self._active_rides()
        drivers = self.driver_operations()
        violations = self.guard_violations()["violations"]
        trust_score = max(
            0,
            100
            - (summary["replay_failures"] * 25)
            - (summary["missing_events"] * 5)
            - (summary["hash_chain_failures"] * 15)
            - (len(violations) * 10),
        )
        return {
            "trust_score": trust_score,
            "active_rides": len(active_rides),
            "drivers_online": drivers["online_count"],
            "receipts_count": summary["valid_traces"],
            "valid_traces": summary["valid_traces"],
            "invalid_traces": summary["invalid_traces"],
            "replay_failures": summary["replay_failures"],
            "hash_chain_failures": summary["hash_chain_failures"],
            "guard_violations": len(violations),
            "trust_state": "VERIFIED" if trust_score >= 90 else "REVIEW",
        }

    def pilot_metrics(self) -> dict:
        summary = self.trace_log.integrity_summary()
        rides = tuple(self.gateway.dispatcher.rides.values())
        active_count = sum(1 for ride in rides if ride.status != "COMPLETED")
        completed_count = sum(1 for ride in rides if ride.status == "COMPLETED")
        total_rides = len(rides)
        valid_trace_rate = (
            round((summary["valid_traces"] / total_rides) * 100, 1)
            if total_rides
            else 0.0
        )
        return {
            "profile": "authoritative_local_runtime",
            "total_rides": total_rides,
            "active_rides": active_count,
            "completed_rides": completed_count,
            "drivers_online": sum(
                1 for driver in self.gateway.dispatcher.drivers.values() if driver.online
            ),
            "replay_success_rate": summary["replay_success_rate"],
            "hash_chain_failures": summary["hash_chain_failures"],
            "valid_trace_rate": valid_trace_rate,
            "guards_open": len(self.guard_violations()["violations"]),
            "readiness": (
                "CONTROLLED"
                if summary["replay_failures"] == 0
                and summary["missing_events"] == 0
                and summary["hash_chain_failures"] == 0
                else "REVIEW"
            ),
        }

    def trace_integrity(self, ride_id: str) -> dict:
        return self.trace_log.validate_ride(ride_id).canonical_dict()

    def trust_sla(self) -> dict:
        metrics = self.trust_metrics()
        thresholds = {
            "green": {"minimum_trust_score": 95, "max_replay_failures": 0, "max_hash_chain_failures": 0},
            "watch": {"minimum_trust_score": 85, "max_replay_failures": 0, "max_hash_chain_failures": 0},
            "breach": {"minimum_trust_score": 0, "max_replay_failures": None, "max_hash_chain_failures": None},
        }
        trust_score = int(metrics["trust_score"])
        if trust_score >= thresholds["green"]["minimum_trust_score"]:
            status = "GREEN"
        elif trust_score >= thresholds["watch"]["minimum_trust_score"]:
            status = "WATCH"
        else:
            status = "BREACH"
        return {
            "sla_status": status,
            "trust_score": trust_score,
            "thresholds": thresholds,
            "current_failures": {
                "replay_failures": metrics["replay_failures"],
                "hash_chain_failures": metrics["hash_chain_failures"],
                "guard_violations": metrics["guard_violations"],
            },
            "authority_boundary": "SLA explains operational thresholds; replay and evidence remain authority",
            "authority": _authority("trust_sla"),
        }

    def external_verify(self, ride_id: str, payload: dict[str, object] | None = None) -> dict:
        ride = completed_ride(self.gateway, ride_id)
        if ride is None:
            if ride_id not in self.gateway.dispatcher.rides:
                raise KeyError("ride_not_found")
            raise ValueError("ride_not_completed")

        events = proof_events_for_ride(self.trace_log, ride)
        evidence = EvidenceEngine().derive(ride.ride_id, events)
        receipt = ReceiptEngine().derive(ride.ride_id, events)
        receipt_payload = receipt.canonical_dict()
        authority_hash = assert_consistent_authority_hashes(
            replay=evidence.replay.canonical_dict()["authority"]["authority_hash"],
            evidence=evidence.canonical_dict()["authority"]["authority_hash"],
            receipt=receipt_payload["authority"]["authority_hash"],
        )
        request = payload or {}
        packet = build_partner_verification_packet(
            tenant_id=str(request.get("tenant_id", "tenant-core")),
            region_id=str(request.get("region_id", "mel-ap-southeast-2")),
            trace_hash=evidence.trace_hash,
            replay_hash=evidence.replay_hash,
            receipt_hash=receipt.receipt_hash,
            authority_hash=authority_hash,
            execution_fingerprint=receipt.execution_fingerprint,
            publication_target=str(request.get("publication_target", "public-ledger-test-anchor")),
            network=str(request.get("network", "external-ledger-testnet")),
            publisher_id=str(request.get("publisher_id", "afritech-anchor-publisher")),
            external_reference=str(request.get("external_reference", f"ride:{ride_id}")),
            expected_anchor_id=_opt_str(request.get("expected_anchor_id")),
            expected_commitment_hash=_opt_str(request.get("expected_commitment_hash")),
            expected_publication_hash=_opt_str(request.get("expected_publication_hash")),
            expected_receipt_hash=_opt_str(request.get("expected_receipt_hash")),
        )
        return {
            "ride_id": ride_id,
            "verification_packet": packet.canonical_dict(),
            "receipt_signature_validation": receipt.signature_validation.canonical_dict(),
            "authority": receipt_payload["authority"],
        }

    def trust_stream_payload(self) -> dict:
        health = self.system_health()
        replay = self.replay_health()
        trust = self.trust_metrics()
        sla = self.trust_sla()
        guards = self.guard_violations()["violations"]
        return {
            "stream": "trust_runtime",
            "replay_status": replay["status"],
            "trust_score": trust["trust_score"],
            "trust_state": trust["trust_state"],
            "sla_status": sla["sla_status"],
            "alerts": guards,
            "hash_chain_failures": health["hash_chain_failures"],
            "replay_failures": health["replay_failures"],
            "missing_traces": health["missing_traces"],
            "authority": _authority("trust_runtime_stream"),
        }

    def _active_rides(self) -> list[dict]:
        return [
            {
                "ride_id": ride.ride_id,
                "state": ride.status,
                "driver_id": ride.assigned_driver,
                "rider_id": ride.passenger_id,
            }
            for ride in self.gateway.dispatcher.rides.values()
            if ride.status != "COMPLETED"
        ]


def _opt_str(value: object | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _authority(surface: str) -> dict[str, object]:
    return authority_envelope(
        doc_id="DOC-ARCH-001",
        doc_version=DOC_VERSION,
        governed_invariants=(
            "I3_NO_SILENT_MUTATION",
            "I4_DETERMINISTIC_EXECUTION",
            "I5_REPLAY_REQUIRED",
            "I6_REPLAY_AUTHORITY",
            "I7_TRANSCRIPT_COMPLETENESS",
            "I8_TRANSCRIPT_HASH_STABILITY",
            "I11_AUTHORITY_DECLARATION",
        ),
        surface=surface,
    )
