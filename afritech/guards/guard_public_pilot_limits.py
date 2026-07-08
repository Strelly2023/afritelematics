"""Guard the public-pilot payment limits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/public_pilot.json"
APPROVAL = ROOT / "docs/public_pilot/PUBLIC_PILOT_APPROVAL.json"


def validate() -> dict[str, object]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    if config.get("payment_mode") != "PILOT_REAL_LIMITED":
        raise RuntimeError("public pilot limited payment mode required")
    if config.get("ga_enabled") or config.get("general_availability_allowed"):
        raise RuntimeError("ga must remain disabled")
    if int(config.get("max_transaction_amount_aud", 0)) != 50:
        raise RuntimeError("max transaction amount must remain 50 AUD")
    if int(approval.get("max_transaction_amount_aud", 0)) != 50:
        raise RuntimeError("approved max transaction amount must remain 50 AUD")
    return {"status": "PASS", "limit_checked_aud": 1, "environment": config.get("environment")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = validate()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"PUBLIC_PILOT_LIMITS_GUARD: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
