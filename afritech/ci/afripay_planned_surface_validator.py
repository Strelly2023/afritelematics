from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = "docs/operations/AFRIPAY_PLANNED_FINANCIAL_SURFACE.md"

REQUIRED_TEXT = (
    "AfriPay is the planned financial services and digital payments ecosystem domain",
    "replay-governed financial continuity layer",
    "It begins only when real transaction evidence exists.",
    "mobile money",
    "wallets",
    "merchant payments",
    "cross-border payments",
    "lending",
    "savings",
    "insurance",
    "Execution precedes payment.",
    "AfriRide ride payments",
    "AfriConnect delivery payments",
    "AfriEats food order payments",
    "AfriPay = Conceptual Financial Surface",
    "Execution: NONE",
    "Evidence: NONE",
    "Activation: FORBIDDEN",
    "real paid transactions exist",
    "payments are exchanged between parties",
    "financial records are captured",
    "receipts are recorded",
    "This format is not active yet.",
    "Transaction ID:",
    "Date + Time:",
    "Payer:",
    "Payee:",
    "Service:",
    "Amount:",
    "Currency:",
    "Method (cash/mobile/etc):",
    "Outcome:",
    "Notes:",
    "no implementation",
    "no API",
    "no wallet",
    "no payment platform claims",
    "No transaction means no AfriPay.",
    "AfriTech does not create money flows. It observes, records, and proves them.",
    "AfriPay       -> finance",
    "AfriPay -> conceptual frozen",
)


def validate() -> bool:
    path = ROOT / DOC
    if not path.exists():
        raise SystemExit(f"missing AfriPay planned financial surface doc: {DOC}")

    text = path.read_text(encoding="utf-8")
    for needle in REQUIRED_TEXT:
        if needle not in text:
            raise SystemExit(f"missing AfriPay planned surface text: {needle}")

    return True


def main() -> int:
    validate()
    print("AFRIPAY_PLANNED_SURFACE_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
