from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def validate() -> bool:
    required_files = (
        ROOT / "afritech/afripower/predictive_orchestration.py",
        ROOT / "afritech/federation/protocol.py",
        ROOT / "afritech/tests/afripower/test_predictive_orchestration.py",
        ROOT / "afritech/tests/federation/test_protocol.py",
    )
    for path in required_files:
        if not path.exists():
            raise SystemExit(f"missing predictive/federation file: {path}")

    predictive_source = (ROOT / "afritech/afripower/predictive_orchestration.py").read_text(
        encoding="utf-8"
    )
    federation_source = (ROOT / "afritech/federation/protocol.py").read_text(encoding="utf-8")
    for forbidden in ("execute_orchestration(", "execute_domain_operation(", "process_command("):
        if forbidden in predictive_source:
            raise SystemExit(f"AfriPower predictive layer must not execute: {forbidden}")
    for required in (
        "assert_read_only_contract",
        "advisory_only",
        "execution_authority: bool = False",
        "explain_suggestion",
        "learn_patterns",
        "score_risk",
    ):
        if required not in predictive_source:
            raise SystemExit(f"missing AfriPower predictive guard: {required}")
    for required in (
        "FederationMessage",
        "verify_federation_message",
        "independently_verified",
        "remote event must be independently replay-verified",
        "federated_state_agreement",
        "apply_federated_policy",
    ):
        if required not in federation_source:
            raise SystemExit(f"missing federation verification guard: {required}")
    return True


def main() -> int:
    validate()
    print("PREDICTIVE_FEDERATION_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
