from __future__ import annotations

from pathlib import Path
import yaml
import datetime
import uuid


AUDIT_FILE = Path(__file__).resolve().parent / "events.yaml"


def emit_event(
    *,
    event_type: str,
    severity_class: str,
    epoch: int,
    adr: str | None,
    description: str,
) -> None:
    """
    Emit a non-authoritative audit event.

    This function MUST NEVER:
    - raise on failure
    - affect control flow
    - enforce policy
    """

    try:
        timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        event = {
            "id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
            "type": event_type,
            "severity_class": severity_class,
            "epoch": epoch,
            "authority": {"adr": adr} if adr else {},
            "description": description,
            "timestamp": timestamp,
        }

        # Load existing ledger
        if AUDIT_FILE.exists():
            with open(AUDIT_FILE, "r") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        data.setdefault("events", []).append(event)

        with open(AUDIT_FILE, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False)

    except Exception:
        # ABSOLUTELY SILENT FAILURE
        pass