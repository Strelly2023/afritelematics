from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict


CHECKLIST_DOC = Path("docs/pilot/AFRIRIDE_PILOT_ACTIVATION_CHECKLIST.md")


REQUIRED_LIVE_GATES = (
    "backend_health_200",
    "events_endpoint_healthy",
    "cors_preflight_healthy",
    "websocket_or_fallback_ready",
    "driver_apk_installed",
    "rider_apk_installed",
    "operator_dashboard_observing",
    "signed_events_emitted",
    "replay_export_ready",
    "emergency_contact_ready",
    "manual_truth_editing_disabled",
)


def build_pilot_activation_checklist(
    live_gates: Dict[str, bool] | None = None,
) -> Dict[str, Any]:
    gates = {gate: False for gate in REQUIRED_LIVE_GATES}
    if live_gates:
        for key, value in live_gates.items():
            if key in gates:
                gates[key] = bool(value)

    phases = {
        "backend_gate": [
            "GET /health = 200",
            "POST /v1/events = 200/201",
            "OPTIONS /rides/active = 200",
            "websocket connects or fallback ready",
        ],
        "device_gate": [
            "driver_phone_001 registered",
            "rider_phone_001 registered",
            "operator_laptop_001 registered",
            "driver and rider APKs installed",
        ],
        "protocol_gate": [
            "hardening suite pass",
            "adversarial attack suite pass",
            "AfriRide ledger scenario pass",
        ],
        "evidence_gate": [
            "signed_event_log.jsonl",
            "ride_lifecycle_trace.json",
            "receipt.json",
            "replay_result.json",
            "evidence_bundle.json",
        ],
    }

    authorized = all(gates.values())
    payload = {
        "schema": "afriride.pilot_activation_checklist.v1",
        "checklist_doc": str(CHECKLIST_DOC),
        "pilot_run_id": "live_pilot_001",
        "authorized": authorized,
        "classification": "go_authorized" if authorized else "activation_prepared_hold",
        "live_gates": gates,
        "phases": phases,
    }
    payload["activation_hash"] = _canonical_hash(payload)
    return payload


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
