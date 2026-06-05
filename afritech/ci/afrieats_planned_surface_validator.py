from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = "docs/operations/AFRIEATS_PLANNED_ECOSYSTEM_SURFACE.md"

REQUIRED_TEXT = (
    "AfriEats is the food delivery and meal logistics ecosystem",
    "AfriEats Architecture: Conceptual",
    "AfriEats Product Surface: Definable",
    "AfriEats Field Evidence: None",
    "AfriEats Operational Truth: Not Yet Established",
    "AfriEats exists today as a planned ecosystem domain.",
    "real restaurants, real customers, real drivers, and real deliveries",
    "Customer",
    "Restaurant",
    "Driver",
    "Operator",
    "Customer places order",
    "Restaurant accepts",
    "Food is prepared",
    "Driver is assigned",
    "Pickup is completed",
    "Delivery is completed",
    "Receipt is generated",
    "Order ID:",
    "Date + Time:",
    "Preparation Time:",
    "Pickup Time:",
    "Delivery Time:",
    "Restaurant Closed",
    "Customer Unavailable",
    "Driver Reassigned",
    "Order Delayed",
    "AfriEats       -> Food Delivery",
    "AfriConnectTL  -> Transportation & Logistics",
    "Structure proven does not mean reality proven.",
    "observe\nrecord\npreserve",
)

FORBIDDEN_ABSENT_TEXT = (
    "AfriEats is operationally proven outside the forbidden section",
)


def validate() -> bool:
    path = ROOT / DOC
    if not path.exists():
        raise SystemExit(f"missing AfriEats planned surface doc: {DOC}")

    text = path.read_text(encoding="utf-8")
    for needle in REQUIRED_TEXT:
        if needle not in text:
            raise SystemExit(f"missing AfriEats planned surface text: {needle}")

    for needle in FORBIDDEN_ABSENT_TEXT:
        if needle in text:
            raise SystemExit(f"forbidden AfriEats claim text present: {needle}")

    return True


def main() -> int:
    validate()
    print("AFRIEATS_PLANNED_SURFACE_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
