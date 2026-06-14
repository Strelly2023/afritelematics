from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = "docs/operations/AFRIPAY_GA_ELITE_IMPLEMENTATION.md"

REQUIRED_TEXT = (
    "AfriPay GA Elite Implementation Surface",
    "Implementation: ACTIVE CORE",
    "Live Settlement: FORBIDDEN BY DEFAULT",
    "Provider Mode: deterministic adapter unless compliance activation is explicit",
    "wallet",
    "double-entry ledger",
    "adaptive multi-rail routing",
    "FX rate locking",
    "escrow",
    "bulk payouts",
    "billing",
    "KYC/AML compliance",
    "intelligence hooks",
    "event outbox",
    "No live-money movement may occur from deterministic adapters.",
    "Provider callbacks never define ledger truth.",
    "Ledger journals must balance per currency.",
    "Payment references must be idempotent.",
    "Authority fields are rejected.",
    "ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> CI",
    "AfriPay remains bounded by observed economic evidence.",
    "No transaction means no AfriPay.",
    "AfriTech does not create money flows. It observes, records, and proves them.",
    "afritech/afripay",
    "afritech/tests/afripay",
)


def validate() -> bool:
    path = ROOT / DOC
    if not path.exists():
        raise SystemExit(f"missing AfriPay implementation surface doc: {DOC}")

    text = path.read_text(encoding="utf-8")
    for needle in REQUIRED_TEXT:
        if needle not in text:
            raise SystemExit(f"missing AfriPay implementation surface text: {needle}")

    return True


def main() -> int:
    validate()
    print("AFRIPAY_GA_ELITE_IMPLEMENTATION_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
