"""Guard the public-pilot release and GA boundary."""

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
    if config.get("environment") != "PUBLIC_PILOT":
        raise RuntimeError("public pilot environment required")
    if config.get("ga_enabled") or config.get("general_availability_allowed"):
        raise RuntimeError("ga must remain disabled")
    if not config.get("prr_required", False):
        raise RuntimeError("prr required")
    if approval.get("ga_enabled"):
        raise RuntimeError("approval claims ga enabled")
    return {
        "environment": config["environment"],
        "ga_enabled": bool(config.get("ga_enabled")),
        "general_availability_allowed": bool(config.get("general_availability_allowed")),
        "unrestricted_signup_allowed": bool(config.get("unrestricted_signup_allowed")),
        "approval": approval,
        "ready_for_prr": bool(approval.get("production_readiness_review_required", False)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = validate()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(
        "PUBLIC_PILOT_RELEASE_GUARD: PASS "
        f"(env={report['environment']}, ga_enabled={report['ga_enabled']}, prr_required={report['approval']['production_readiness_review_required']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
