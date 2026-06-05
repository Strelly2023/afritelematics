from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from afritech.ci.afritech_check_classification_status import (
    ClassificationEngine,
    SystemSignals,
)


ROOT = Path(__file__).resolve().parents[2]


def resolve_signals() -> SystemSignals:
    """
    Resolve classification signals from repo-side evidence.

    This deliberately does not infer live field evidence. Live pilot and
    production proof stay false unless an explicit external activation surface
    is added later.
    """

    return SystemSignals(
        constitutional_pass=_exists("afritech/ci/constitutional_validation.py"),
        replay_valid=_exists("afritech/distributed/replay/replay_verifier.py"),
        proof_surface_valid=_exists("afritech/distributed/proof.py"),
        consensus_valid=_exists("afritech/distributed/consensus/consensus_engine.py"),
        hardening_implemented=_exists("afritech/distributed/testing/hardening_suite.py"),
        adversarial_implemented=_exists(
            "afritech/distributed/testing/adversarial_attack_suite.py"
        ),
        multi_domain_validation=_exists(
            "afritech/distributed/testing/protocol_scenarios.py"
        ),
        observability_ready=_exists("afritech/runtime/observability/exporter.py"),
        deployment_control_ready=_exists(
            "docs/pilot/AFRIRIDE_GA_ELITE_READINESS_MATRIX.md"
        )
        and _contains(
            "docs/pilot/AFRIRIDE_GA_ELITE_READINESS_MATRIX.md",
            "live_pilot_authorized = false",
        ),
        app_surface_ready=_exists("docs/mobile/afriride_app_store_master_plan.md")
        and _exists("afritech/ci/afriride_app_store_deployment_validator.py"),
        controlled_pilot_prepared=_exists(
            "docs/pilot/AFRIRIDE_MULTI_NODE_PRODUCTION_PILOT_PREP.md"
        ),
        live_pilot_authorized=False,
        production_proven=False,
    )


def run_classification_ci_validation() -> Dict[str, Any]:
    print("\nRunning Classification CI Validator")
    print("=" * 60)

    signals = resolve_signals()
    engine = ClassificationEngine(signals)
    result = engine.classify()

    _print_summary(result)
    _enforce_rules(result)

    print("\nClassification CI validation PASSED")
    print("=" * 60)
    return result


def _enforce_rules(result: Dict[str, Any]) -> None:
    truth_boundary = result.get("truth_boundary", {})

    if truth_boundary.get("production_proven") is True:
        raise RuntimeError(
            "CI BLOCK: production_proven=True is forbidden without field evidence."
        )

    if truth_boundary.get("live_pilot_authorized") is True:
        raise RuntimeError(
            "CI BLOCK: live_pilot_authorized=True is not allowed in CI."
        )

    forbidden = result.get("forbidden_claims", [])
    if not isinstance(forbidden, list):
        raise RuntimeError("CI BLOCK: forbidden_claims must be a list.")

    layers = result.get("layers", {})
    incomplete = [
        name for name, status in layers.items()
        if status != "COMPLETE"
    ]
    if incomplete:
        raise RuntimeError(
            f"CI BLOCK: incomplete classification layers: {', '.join(incomplete)}"
        )


def _print_summary(result: Dict[str, Any]) -> None:
    print("\nClassification Summary")
    print("-" * 40)
    print(f"Tier: {result['tier']}")
    print(f"State: {result['state']}")

    print("\nLayers:")
    for key, value in result["layers"].items():
        print(f"  - {key}: {value}")

    print("\nTruth Boundary:")
    for key, value in result["truth_boundary"].items():
        print(f"  - {key}: {value}")

    print("\nAllowed Claims:")
    for claim in result["allowed_claims"]:
        print(f"  - {claim}")

    print("\nForbidden Claims:")
    for claim in result["forbidden_claims"]:
        print(f"  - {claim}")

    print("\nMissing Evidence:")
    for evidence in result["missing_evidence"]:
        print(f"  - {evidence}")


def _exists(relative_path: str) -> bool:
    return (ROOT / relative_path).exists()


def _contains(relative_path: str, needle: str) -> bool:
    path = ROOT / relative_path
    if not path.exists():
        return False
    return needle in path.read_text(encoding="utf-8")


def main() -> int:
    try:
        run_classification_ci_validation()
        return 0
    except Exception as exc:
        print(f"Classification CI validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
