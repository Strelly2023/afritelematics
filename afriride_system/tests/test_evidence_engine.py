from __future__ import annotations

from afriride_system.backend.evidence_engine import EvidenceEngine
from afriride_system.backend.trace_enforcement import TraceEventLog, build_trace_log


def _append(log: TraceEventLog, *, event_id: str, actor_type: str, actor_id: str, action: str) -> None:
    log.append(
        {
            "event_id": event_id,
            "device_id": f"device-{actor_id}",
            "actor_type": actor_type,
            "actor_id": actor_id,
            "action": action,
            "payload": {"ride_id": "ride-evidence-1"},
            "local_timestamp": "2026-06-02T10:00:00Z",
            "app_version": "0.1",
            "test_mode": True,
        },
        ride_id="ride-evidence-1",
    )


def test_evidence_engine_derives_verified_record_from_completed_trace(tmp_path) -> None:
    log = build_trace_log(db_path=tmp_path / "evidence.sqlite3")
    _append(log, event_id="evidence-request-1", actor_type="rider", actor_id="rider-1", action="POST /passenger/request-ride")
    _append(log, event_id="evidence-accept-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-evidence-1/accept")
    _append(log, event_id="evidence-arrive-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-evidence-1/arrive")
    _append(log, event_id="evidence-start-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-evidence-1/start")
    _append(log, event_id="evidence-complete-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-evidence-1/complete")

    evidence = EvidenceEngine().derive("ride-evidence-1", log.events_for_ride("ride-evidence-1"))

    assert evidence.ride_id == "ride-evidence-1"
    assert evidence.verification_status == "VERIFIED"
    assert evidence.replay.replay_verified is True
    assert evidence.replay.status == "COMPLETED"
    payload = evidence.canonical_dict()
    assert payload["authority"]["doc_id"] == "DOC-ARCH-001"
    assert len(payload["authority"]["authority_hash"]) == 64
    assert payload["authority"]["surface"] == "evidence_record"
