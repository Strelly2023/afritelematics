"""Guard the canonical activation gate registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/release.json"
EXPECTED_GATES = (
    "publicRegistration",
    "publicOnboarding",
    "realPayments",
    "countryActivation",
    "featureActivation",
    "merchantActivation",
    "agentActivation",
    "driverActivation",
)


def validate() -> dict[str, object]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    gates = config.get("activationGates", {})
    if not isinstance(gates, dict):
        raise RuntimeError("activation gates must be a mapping")
    missing = [gate for gate in EXPECTED_GATES if gate not in gates]
    if missing:
        raise RuntimeError(f"missing activation gates: {', '.join(missing)}")
    return {
        "status": "PASS",
        "environment": config.get("environment"),
        "enabled_gates": [gate for gate, enabled in gates.items() if enabled],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        report = validate()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"ACTIVATION_GATE_GUARD: {report['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

