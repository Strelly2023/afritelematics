#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from afritech.novaride_runtime.events.registry import REQUIRED_EVENTS
from afritech.novaride_runtime.events.schema_registry import default_event_schema_registry

REPORT = ROOT / "reports" / "novaride" / "deployment" / "event-schema-compatibility.json"


def main() -> int:
    registry = default_event_schema_registry()
    missing = [
        event_type for event_type in REQUIRED_EVENTS if registry.get(event_type, "2026.2") is None
    ]
    report = {
        "status": "PASS" if not missing else "FAIL",
        "schema_version": "2026.2",
        "registered_event_count": len(registry.schemas),
        "missing_required_events": missing,
        "compatibility_policy": "additive_fields_allowed_required_field_removal_forbidden",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
