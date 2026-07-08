"""Guard GA enablement against missing PRR approval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/release.json"
PRR = ROOT / "docs/prr/PRR-001-production-readiness-review.yaml"


def validate() -> dict[str, object]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    prr_text = PRR.read_text(encoding="utf-8")
    if config.get("gaEnabled"):
        if "status: APPROVED" not in prr_text:
            raise RuntimeError("ga cannot be enabled before prr approval")
    if config.get("generalAvailabilityAllowed") and not config.get("gaEnabled"):
        raise RuntimeError("ga allowance requires ga enabled")
    return {
        "status": "PASS",
        "environment": config.get("environment"),
        "ga_enabled": bool(config.get("gaEnabled")),
        "prr_approved": "status: APPROVED" in prr_text,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = validate()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"GA_ENABLEMENT_GUARD: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

