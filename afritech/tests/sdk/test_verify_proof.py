from __future__ import annotations

import json

import pytest

from afritech.verify.verify_proof import (
    VerificationError,
    render_verification_report,
    verify_packet,
    verify_packet_file,
)
from afriride_system.backend.determinism import collect_ride_snapshot
from afriride_system.backend.storage import AfriRideStorage
from afriride_system.backend.trace_enforcement import build_trace_log


def _append(log, *, event_id: str, actor_type: str, actor_id: str, action: str, ride_id: str) -> None:
    log.append(
        {
            "event_id": event_id,
            "device_id": f"device-{actor_id}",
            "actor_type": actor_type,
            "actor_id": actor_id,
            "action": action,
            "payload": {"ride_id": ride_id},
            "local_timestamp": "2026-06-02T10:00:00Z",
            "app_version": "1.0.0",
            "test_mode": True,
        },
        ride_id,
    )


def test_verify_proof_accepts_authority_bound_packet(tmp_path) -> None:
    db_path = tmp_path / "verify.sqlite3"
    log = build_trace_log(db_path=db_path)
    ride_id = "ride-verify-1"
    _append(log, event_id="verify-request-1", actor_type="rider", actor_id="rider-1", action="POST /passenger/request-ride", ride_id=ride_id)
    _append(log, event_id="verify-accept-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-verify-1/accept", ride_id=ride_id)
    _append(log, event_id="verify-arrive-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-verify-1/arrive", ride_id=ride_id)
    _append(log, event_id="verify-start-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-verify-1/start", ride_id=ride_id)
    _append(log, event_id="verify-complete-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-verify-1/complete", ride_id=ride_id)

    storage = AfriRideStorage(db_path)
    snapshot = collect_ride_snapshot(storage, ride_id)
    packet = {
        "ride_id": ride_id,
        "events": [event.canonical_dict() for event in log.events_for_ride(ride_id)],
        "replay": snapshot.replay.canonical_dict(),
        "evidence": snapshot.evidence.canonical_dict(),
        "receipt": snapshot.receipt.canonical_dict(),
        "authority": snapshot.receipt.canonical_dict()["authority"],
    }

    result = verify_packet(packet)

    assert result["valid"] is True
    assert result["authority_verified"] is True
    assert result["execution_verified"] is True
    assert len(result["execution_fingerprint"]) == 64
    assert result["compatibility"]["supported"] is True


def test_verify_proof_file_and_text_report_are_public_tool_ready(tmp_path) -> None:
    db_path = tmp_path / "verify-report.sqlite3"
    log = build_trace_log(db_path=db_path)
    ride_id = "ride-verify-report"
    _append(log, event_id="verify-report-1", actor_type="rider", actor_id="rider-1", action="POST /passenger/request-ride", ride_id=ride_id)
    _append(log, event_id="verify-report-2", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-verify-report/accept", ride_id=ride_id)

    storage = AfriRideStorage(db_path)
    snapshot = collect_ride_snapshot(storage, ride_id)
    packet = {
        "ride_id": ride_id,
        "events": [event.canonical_dict() for event in log.events_for_ride(ride_id)],
        "replay": snapshot.replay.canonical_dict(),
        "evidence": snapshot.evidence.canonical_dict(),
        "receipt": snapshot.receipt.canonical_dict(),
        "authority": snapshot.receipt.canonical_dict()["authority"],
    }
    packet_path = tmp_path / "proof-bundle.json"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    result = verify_packet_file(packet_path)
    text = render_verification_report(result)

    assert result["packet_path"] == str(packet_path)
    assert "AfriTech Public Verifier: VALID" in text
    assert "protocol_version: 1.0.0" in text


def test_verify_proof_rejects_replay_mismatch(tmp_path) -> None:
    db_path = tmp_path / "verify-mismatch.sqlite3"
    log = build_trace_log(db_path=db_path)
    ride_id = "ride-verify-2"
    _append(log, event_id="verify2-request-1", actor_type="rider", actor_id="rider-1", action="POST /passenger/request-ride", ride_id=ride_id)
    _append(log, event_id="verify2-accept-1", actor_type="driver", actor_id="driver-1", action="POST /ride/ride-verify-2/accept", ride_id=ride_id)

    storage = AfriRideStorage(db_path)
    snapshot = collect_ride_snapshot(storage, ride_id)
    replay = snapshot.replay.canonical_dict()
    replay["replay_hash"] = "0" * 64
    packet = {
        "ride_id": ride_id,
        "events": [event.canonical_dict() for event in log.events_for_ride(ride_id)],
        "replay": replay,
        "evidence": snapshot.evidence.canonical_dict(),
        "receipt": snapshot.receipt.canonical_dict(),
        "authority": snapshot.receipt.canonical_dict()["authority"],
    }

    with pytest.raises(VerificationError, match="replay mismatch"):
        verify_packet(packet)
