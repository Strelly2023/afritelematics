from __future__ import annotations

from pathlib import Path

from afritech.ci.afriride_app_store_deployment_validator import validate as validate_store


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/pilot/AFRIRIDE_GA_ELITE_READINESS_MATRIX.md",
    "docs/pilot/AFRIRIDE_REAL_WORLD_ACTIVATION_PLAYBOOK.md",
    "docs/pilot/AFRIRIDE_DEPLOYMENT_TOPOLOGY.md",
    "docs/pilot/AFRIRIDE_RISK_CONTROL_REGISTER.md",
    "docs/pilot/AFRIRIDE_PILOT_ACTIVATION_CHECKLIST.md",
    "docs/mobile/afriride_app_store_master_plan.md",
)

REQUIRED_TEXT = (
    (
        "docs/pilot/AFRIRIDE_GA_ELITE_READINESS_MATRIX.md",
        "live_pilot_authorized = false",
    ),
    (
        "docs/pilot/AFRIRIDE_REAL_WORLD_ACTIVATION_PLAYBOOK.md",
        "go_authorized = false",
    ),
    (
        "docs/pilot/AFRIRIDE_DEPLOYMENT_TOPOLOGY.md",
        "Mobile apps are interface-only",
    ),
    (
        "docs/pilot/AFRIRIDE_RISK_CONTROL_REGISTER.md",
        "production-proven",
    ),
)


def validate() -> bool:
    validate_store()

    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"missing final deployment phase files: {missing}")

    for path, needle in REQUIRED_TEXT:
        text = (ROOT / path).read_text(encoding="utf-8")
        if needle not in text:
            raise SystemExit(f"missing required text in {path}: {needle}")

    return True


def main() -> int:
    validate()
    print("AFRIRIDE_FINAL_DEPLOYMENT_PHASE_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
