from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = "docs/operations/AFRICONNECT_BURUNDI_PHASE1_OPERATIONS_PLAN.md"

REQUIRED_TEXT = (
    "Start a real logistics operation",
    "without claiming protocol validation yet",
    "Bujumbura urban pilot zone",
    "Bujumbura -> Uvira cross-border route",
    "one motorcycle",
    "one trusted driver",
    "local shops",
    "small traders",
    "farm-to-market transport",
    "AgroSolidarite-linked producers",
    "short urban delivery: 1 to 3 USD",
    "longer local delivery: 3 to 7 USD",
    "delivery_id",
    "customer_name",
    "pickup_location",
    "dropoff_location",
    "driver_name",
    "customer_confirmation",
    "paper notebook",
    "WhatsApp log",
    "Google Sheet",
    "request -> confirm -> dispatch -> deliver -> confirm",
    "no unrecorded delivery",
    "lost goods",
    "wrong delivery",
    "late delivery",
    "driver fraud",
    "number_of_deliveries",
    "delivery_time",
    "customer_feedback",
    "revenue",
    "no live protocol claims",
    "no automatic proof claims",
    "no production-proven claims",
    "no autonomous logistics claims",
    "10 to 20 deliveries are completed",
    "Business first. Protocol later. Truth after evidence.",
)


def validate() -> bool:
    path = ROOT / DOC
    if not path.exists():
        raise SystemExit(f"missing AfriConnect Burundi Phase 1 operations plan: {DOC}")

    text = path.read_text(encoding="utf-8")
    for needle in REQUIRED_TEXT:
        if needle not in text:
            raise SystemExit(f"missing Burundi Phase 1 operations text: {needle}")

    return True


def main() -> int:
    validate()
    print("AFRICONNECT_BURUNDI_PHASE1_OPERATIONS_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
