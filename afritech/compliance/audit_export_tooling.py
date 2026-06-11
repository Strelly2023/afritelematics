"""Enterprise-grade audit export tooling for partner and launch evidence."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
from typing import Any

from afritech.monitoring.realtime_anomaly_alerting import RealtimeAnomalyAlert
from afritech.partner_verification import PartnerVerificationPacket


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def export_enterprise_audit_bundle(
    *,
    output_dir: str | Path,
    verification_packet: PartnerVerificationPacket,
    launch_artifact_id: str,
    anomaly_alerts: tuple[RealtimeAnomalyAlert, ...] = (),
) -> Path:
    bundle_dir = Path(output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema": "afritech.enterprise_audit_bundle.v1",
        "launch_artifact_id": launch_artifact_id,
        "verification_packet": verification_packet.canonical_dict(),
        "anomaly_alerts": [alert.canonical_dict() for alert in anomaly_alerts],
        "authority_boundary": (
            "bundle exports evidence only; trace and replay remain authority"
        ),
    }
    payload["bundle_hash"] = _canonical_hash(payload)
    output_path = bundle_dir / f"enterprise_audit_bundle_{payload['bundle_hash'][:12]}.json"
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


__all__ = ["export_enterprise_audit_bundle"]
