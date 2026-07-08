"""Guard the canonical release stage ordering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/release.json"
STAGE_ORDER = [
    "PRIVATE_DEVELOPMENT",
    "INTERNAL_QA",
    "CONTROLLED_PILOT",
    "PUBLIC_PILOT",
    "PRODUCTION_READINESS_REVIEW",
    "GENERAL_AVAILABILITY",
    "REGIONAL_EXPANSION",
    "GLOBAL_MULTI_REGION_PLATFORM",
]


def validate() -> dict[str, object]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    stage = config.get("releaseStage")
    if stage not in STAGE_ORDER:
      raise RuntimeError("invalid release stage")
    return {
        "status": "PASS",
        "release_stage": stage,
        "stage_index": STAGE_ORDER.index(stage),
        "ga_enabled": bool(config.get("gaEnabled")),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = validate()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"RELEASE_STAGE_GUARD: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

