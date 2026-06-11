from __future__ import annotations

from afriride_system.backend.receipt_engine import ReceiptEngine, _receipt_payload, _stable_hash
from afriride_system.backend.trace_enforcement import TraceEventLog, build_trace_log


def _append(log: TraceEventLog, *, event_id: str, actor_type: str, actor_id: str, action: str) -> None:
    log.append(
        {
            "event_id": event_id,
            "device_id": f"device-{actor_id}",
            "actor_type": actor_type,
            "actor_id": actor_id,
            "action": action,
            "payload": {"ride_id": "ride-receipt-1"},
            "local_timestamp": "2026-06-02T10:00:00Z",
            "app_version": "0.1",
            "test_mode": True,
        },
        ride_id="ride-receipt-1",
    )


def test_receipt_is_deterministic_before_and_after_rebuild(tmp_path) -> None:
    db_path = tmp_path / "receipt.sqlite3"
    log = build_trace_log(db_path=db_path)
    _append(log, event_id="receipt-request-1", actor_type="rider", actor_id="rider-1", action="POST /passenger/request-ride")
    _append(log, event_id="receipt-accept-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-receipt-1/accept")
    _append(log, event_id="receipt-arrive-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-receipt-1/arrive")
    _append(log, event_id="receipt-start-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-receipt-1/start")
    _append(log, event_id="receipt-complete-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-receipt-1/complete")

    engine = ReceiptEngine()
    first = engine.derive("ride-receipt-1", log.events_for_ride("ride-receipt-1"))

    rebuilt_log = build_trace_log(db_path=db_path)
    second = engine.derive("ride-receipt-1", rebuilt_log.events_for_ride("ride-receipt-1"))

    assert first.receipt_hash == second.receipt_hash
    assert first.trace_hash == second.trace_hash
    assert first.replay_hash == second.replay_hash
    payload = first.canonical_dict()
    assert payload["authority"]["doc_id"] == "DOC-ARCH-001"
    assert payload["authority"]["doc_version"] == "1.0.0"
    assert len(payload["authority"]["authority_hash"]) == 64
    assert payload["authority"]["surface"] == "receipt_record"
    evidence = engine.evidence_engine.derive(
        "ride-receipt-1",
        rebuilt_log.events_for_ride("ride-receipt-1"),
    )
    expected_payload = _receipt_payload(evidence)
    assert expected_payload["authority_hash"] == payload["authority"]["authority_hash"]
    assert first.receipt_hash == _stable_hash(expected_payload)
    evidence = engine.evidence_engine.derive(
        "ride-receipt-1",
        rebuilt_log.events_for_ride("ride-receipt-1"),
    )
    expected_payload = _receipt_payload(evidence)
    assert expected_payload["authority_hash"] == payload["authority"]["authority_hash"]
    assert first.receipt_hash == _stable_hash(expected_payload)
