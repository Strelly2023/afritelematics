from __future__ import annotations

from pathlib import Path
import yaml
import datetime
import uuid
from typing import Optional


# =====================================================
# ✅ CONFIGURATION
# =====================================================

AUDIT_FILE = Path(__file__).resolve().parent / "events.yaml"


# =====================================================
# ✅ CORE EMITTER
# =====================================================

def emit_event(
    *,
    event_type: str,
    severity_class: str,
    epoch: int,
    description: str,
    adr: Optional[str] = None,
) -> None:
    """
    Emit a non-authoritative audit event.

    ⚠️ NON-AUTHORITY LAYER
    This emitter is observational only and MUST NEVER:
    - raise exceptions
    - affect system control flow
    - enforce policy
    - mutate runtime decision logic

    ✅ SAFE USAGE:
    - logging
    - observability
    - diagnostics
    - trace reconstruction

    ❌ NOT FOR:
    - validation
    - enforcement
    - admission control
    """

    try:
        event = _build_event(
            event_type=event_type,
            severity_class=severity_class,
            epoch=epoch,
            description=description,
            adr=adr,
        )

        data = _load_events()
        data.setdefault("events", []).append(event)

        _persist_events(data)

    except Exception:
        # ✅ ABSOLUTELY SILENT FAILURE (by design)
        return


# =====================================================
# ✅ INTERNAL BUILDERS
# =====================================================

def _build_event(
    *,
    event_type: str,
    severity_class: str,
    epoch: int,
    description: str,
    adr: Optional[str],
) -> dict:
    """
    Builds a deterministic event payload.
    """

    timestamp = (
        datetime.datetime.utcnow()
        .replace(microsecond=0)
        .isoformat() + "Z"
    )

    return {
        "id": _generate_event_id(),
        "type": event_type,
        "severity_class": severity_class,
        "epoch": epoch,
        "authority": {"adr": adr} if adr else {},
        "description": description,
        "timestamp": timestamp,
    }


def _generate_event_id() -> str:
    """
    Generates a compact event identifier.
    """

    return f"EVT-{uuid.uuid4().hex[:8].upper()}"


# =====================================================
# ✅ STORAGE LAYER
# =====================================================

def _load_events() -> dict:
    """
    Loads existing events from YAML ledger.

    Returns empty structure if file is missing or invalid.
    """

    if not AUDIT_FILE.exists():
        return {"events": []}

    try:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            return {"events": []}

        data.setdefault("events", [])
        return data

    except Exception:
        # ✅ Corrupt file should NOT break system
        return {"events": []}


def _persist_events(data: dict) -> None:
    """
    Persists events safely to disk.
    """

    try:
        with open(AUDIT_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                sort_keys=False,
                allow_unicode=True
            )
    except Exception:
        # ✅ Silent failure (non-authoritative)
        return
