"""Guard the public-pilot geography restrictions."""

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
    approved_regions = list(approval.get("approved_regions", []))
    if config.get("environment") != "PUBLIC_PILOT":
        raise RuntimeError("public pilot environment required")
    if not config.get("pilot_geography_restricted", False):
        raise RuntimeError("public pilot geography restrictions required")
    if not approved_regions:
        raise RuntimeError("approved regions required")
    return {
        "status": "PASS",
        "approved_regions": approved_regions,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = validate()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"PUBLIC_PILOT_GEOGRAPHY_GUARD: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
