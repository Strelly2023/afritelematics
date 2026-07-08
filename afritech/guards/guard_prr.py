"""Guard the PRR certification boundary."""

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
    if not config.get("prrRequired", False):
        raise RuntimeError("prr must be required")
    if "status: BLOCKED" not in prr_text and "status: APPROVED" not in prr_text:
        raise RuntimeError("prr placeholder must state a status")
    return {
        "status": "PASS",
        "prr_required": bool(config.get("prrRequired")),
        "prr_blocked": "status: BLOCKED" in prr_text,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = validate()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"PRR_GUARD: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

