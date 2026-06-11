"""Replay-linked real-time anomaly alerting service."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from afritech.runtime_monitoring.anomaly_detector import detect_anomalies


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _severity_for(anomaly_type: str) -> str:
    if anomaly_type == "replay_mismatch":
        return "CRITICAL"
    if anomaly_type == "contract_mismatch":
        return "HIGH"
    if anomaly_type == "validation_failure":
        return "HIGH"
    return "MEDIUM"


@dataclass(frozen=True)
class RealtimeAnomalyAlert:
    alert_id: str
    alert_type: str
    ride_id: str
    trace_id: str
    event_id: str
    replay_hash: str
    receipt_hash_optional: str | None
    evidence_pointer: str
    severity: str
    opened_at: str
    anomaly_type: str
    actor_id: str
    device_id: str
    authority_boundary: str = "trace_and_replay_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.realtime_anomaly_alert.v1",
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "ride_id": self.ride_id,
            "trace_id": self.trace_id,
            "event_id": self.event_id,
            "replay_hash": self.replay_hash,
            "receipt_hash_optional": self.receipt_hash_optional,
            "evidence_pointer": self.evidence_pointer,
            "severity": self.severity,
            "opened_at": self.opened_at,
            "anomaly_type": self.anomaly_type,
            "actor_id": self.actor_id,
            "device_id": self.device_id,
            "authority_boundary": self.authority_boundary,
        }


def build_realtime_anomaly_alerts(
    events: dict[str, object],
    *,
    ride_id: str,
    trace_id: str,
    event_id: str,
    actor_id: str,
    device_id: str,
    replay_hash: str,
    opened_at: str,
    receipt_hash: str | None = None,
) -> tuple[RealtimeAnomalyAlert, ...]:
    anomalies = detect_anomalies(events)
    alerts: list[RealtimeAnomalyAlert] = []
    for anomaly in anomalies:
        anomaly_type = str(anomaly["type"])
        severity = _severity_for(anomaly_type)
        alert_type = f"{anomaly_type.upper()}_ALERT"
        evidence_pointer = f"trace:{trace_id}:event:{event_id}:ride:{ride_id}"
        alert_id = f"alert-{_canonical_hash({'evidence_pointer': evidence_pointer, 'anomaly_type': anomaly_type, 'replay_hash': replay_hash})[:12]}"
        alerts.append(
            RealtimeAnomalyAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                ride_id=ride_id,
                trace_id=trace_id,
                event_id=event_id,
                replay_hash=replay_hash,
                receipt_hash_optional=receipt_hash,
                evidence_pointer=evidence_pointer,
                severity=severity,
                opened_at=opened_at,
                anomaly_type=anomaly_type,
                actor_id=actor_id,
                device_id=device_id,
            )
        )
    return tuple(alerts)


__all__ = ["RealtimeAnomalyAlert", "build_realtime_anomaly_alerts"]
