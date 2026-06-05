from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = "docs/operations/AFRICONNECT_LOGISTICS_BUSINESS_STRATEGY.md"

REQUIRED_TEXT = (
    "AfriConnect Transport, Logistics & Warehouse",
    "Business layer: AfriConnect Transport, Logistics & Warehouse",
    "Technology layer: AfriTech and AfriConnectTL",
    "We do not just deliver goods. We are building systems that can prove delivery.",
    "Truth authority must come from replay receipts and evidence bundles",
    "AgroSolidarite",
    "Transport:",
    "Logistics:",
    "Warehousing:",
    "A warehouse should evolve into a state-controlled logistics node",
    "Agriculture:",
    "Small businesses:",
    "NGOs and aid organizations:",
    "Phase 1: Simple operations",
    "Phase 2: Proof-enabled rehearsal",
    "Phase 3: Scale discipline",
    "autonomous logistics network",
    "fully proven logistics system",
    "large-scale deployment",
    "guaranteed real-world reliability",
    "production-proven replay logistics",
    "protocol-backed claims require evidence bundles",
)


def validate() -> bool:
    path = ROOT / DOC
    if not path.exists():
        raise SystemExit(f"missing AfriConnect business strategy doc: {DOC}")

    text = path.read_text(encoding="utf-8")
    for needle in REQUIRED_TEXT:
        if needle not in text:
            raise SystemExit(f"missing AfriConnect business strategy text: {needle}")

    return True


def main() -> int:
    validate()
    print("AFRICONNECT_BUSINESS_STRATEGY_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
