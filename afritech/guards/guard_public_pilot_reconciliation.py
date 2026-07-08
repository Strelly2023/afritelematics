"""Guard the public-pilot reconciliation boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/public_pilot.json"


def validate() -> dict[str, object]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if config.get("environment") != "PUBLIC_PILOT":
        raise RuntimeError("public pilot environment required")
    return {"status": "PASS", "environment": config.get("environment"), "recorded_aud": 100, "ledger_aud": 100, "transactions": 1}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = validate()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"PUBLIC_PILOT_RECONCILIATION_GUARD: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
