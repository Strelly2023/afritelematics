from __future__ import annotations

from pathlib import Path

from afritech.services.africonnecttl.registry import (
    EVIDENCE_FIELDS,
    SHIPMENT_LIFECYCLE,
    STOP_CONDITIONS,
    SURFACE_DEFINITION,
    validate_surface_contract,
)


ROOT = Path(__file__).resolve().parents[2]

SPEC = "docs/pilot/AFRICONNECTTL_PHASE2_LOGISTICS_EXECUTION_SPEC.md"
REQUIRED_FILES = (
    SPEC,
    "afritech/services/africonnecttl/models.py",
    "afritech/services/africonnecttl/execution.py",
    "afritech/services/africonnecttl/reducers.py",
    "afritech/services/africonnecttl/registry.py",
)

REQUIRED_TEXT = (
    "AfriTech Ecosystem Expansion - Phase 2 (Logistics)",
    "Status: PLANNED",
    "Operational proof: NONE",
    "Field execution: NONE",
    "Live deployment: FORBIDDEN",
    "truth_source = replay receipts only",
    "One canonical state transition per consensus result.",
    "Controlled Field Rehearsal",
    "NOT production",
    "NOT open pilot",
    "NOT public release",
)


def validate() -> bool:
    validate_surface_contract()

    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"missing AfriConnectTL Phase 2 files: {missing}")

    text = (ROOT / SPEC).read_text(encoding="utf-8")
    for needle in REQUIRED_TEXT:
        if needle not in text:
            raise SystemExit(f"missing AfriConnectTL Phase 2 text: {needle}")

    for fn_id, status in SHIPMENT_LIFECYCLE:
        if fn_id not in text or status not in text:
            raise SystemExit(f"missing lifecycle binding: {fn_id} -> {status}")

    for field in EVIDENCE_FIELDS:
        if field not in text:
            raise SystemExit(f"missing evidence field: {field}")

    for condition in STOP_CONDITIONS:
        if condition not in text:
            raise SystemExit(f"missing stop condition: {condition}")

    if SURFACE_DEFINITION["status"] != "PLANNED":
        raise SystemExit("AfriConnectTL status must remain PLANNED")

    return True


def main() -> int:
    validate()
    print("AFRICONNECTTL_PHASE2_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
