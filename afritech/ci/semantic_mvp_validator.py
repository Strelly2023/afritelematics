from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from afritech.core.runtime.system_enforcement.execution_guard import admit_contract


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    ROOT / "afritech/core/runtime/system_enforcement/execution_pipeline.yaml",
    ROOT / "afritech/core/runtime/contracts/normalization_contract.yaml",
    ROOT / "afritech/semantic_engine/hash/hash_policy.yaml",
    ROOT / "afritech/governance/anti_entropy.yaml",
]

REQUIRED_CHECKS = {
    "no_undeclared_semantics",
    "semantic_reference_required",
    "dependency_acyclic",
    "kernel_size_constraint",
}

CANONICAL_ORDER = [
    "compile",
    "normalize",
    "hash",
    "evaluate",
    "proof",
    "admission_gate",
]

ALLOWED_OPERATORS = {
    "AND",
    "EQUIVALENT",
    "REQUIRES",
    "FORALL",
}

CONTRACT_ROOT = ROOT / "afritech/semantic_engine/contracts"

ADVERSARIAL_CONTRACTS = {
    "adversarial_undeclared_symbol.yaml": "undeclared_symbol:driver_available",
    "adversarial_unsupported_operator.yaml": "unsupported_operator:OR",
}

DENIAL_CONTRACTS = {
    "adversarial_rejected_admission.yaml": "execution_not_admissible",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing file: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{path} must be a YAML mapping")
    return payload


def validate_required_files() -> None:
    for path in REQUIRED_FILES:
        load_yaml(path)


def validate_pipeline_contract() -> None:
    payload = load_yaml(REQUIRED_FILES[0])
    pipeline = payload.get("execution_pipeline")
    if not isinstance(pipeline, dict):
        fail("execution_pipeline.yaml missing execution_pipeline")

    if pipeline.get("non_bypassable_order") != CANONICAL_ORDER:
        fail("execution pipeline order is not canonical")

    stages = pipeline.get("stages")
    if not isinstance(stages, list):
        fail("execution pipeline stages must be a list")

    evaluate_stage = next(
        (stage for stage in stages if isinstance(stage, dict) and stage.get("name") == "evaluate"),
        None,
    )
    if not evaluate_stage:
        fail("execution pipeline missing evaluate stage")

    operators = set(evaluate_stage.get("allowed_operators", []))
    if operators != ALLOWED_OPERATORS:
        fail(f"allowed operators must be exactly {sorted(ALLOWED_OPERATORS)}")


def validate_normalization_contract() -> None:
    payload = load_yaml(REQUIRED_FILES[1])
    contract = payload.get("normalization_contract")
    if not isinstance(contract, dict):
        fail("normalization_contract.yaml missing normalization_contract")

    invariant = contract.get("invariant")
    if not isinstance(invariant, dict):
        fail("normalization contract missing invariant")
    if invariant.get("evaluation_requires_normalized_ir") is not True:
        fail("normalization contract must require normalized IR before evaluation")
    if invariant.get("raw_expression_evaluation_allowed") is not False:
        fail("normalization contract must forbid raw expression evaluation")


def validate_hash_policy() -> None:
    payload = load_yaml(REQUIRED_FILES[2])
    policy = payload.get("hash_policy")
    if not isinstance(policy, dict):
        fail("hash_policy.yaml missing hash_policy")
    if policy.get("authority") != "normalized_s_ir":
        fail("hash authority must be normalized_s_ir")
    identity = policy.get("identity_rule")
    if not isinstance(identity, dict) or identity.get("semantic_identity_is_hash_of_normalized_s_ir") is not True:
        fail("hash policy must bind semantic identity to normalized S-IR")


def validate_anti_entropy() -> None:
    payload = load_yaml(REQUIRED_FILES[3])
    policy = payload.get("anti_entropy")
    if not isinstance(policy, dict):
        fail("anti_entropy.yaml missing anti_entropy")

    boundary = policy.get("executable_boundary")
    if not isinstance(boundary, dict):
        fail("anti-entropy policy missing executable boundary")

    forbidden = set(boundary.get("runtime_code_must_not", []))
    required_forbidden = {
        "define_semantics",
        "bypass_normalization",
        "evaluate_raw_expressions",
    }
    if not required_forbidden.issubset(forbidden):
        fail("anti-entropy policy does not forbid semantic leakage")


def validate_ci_manifest() -> None:
    payload = load_yaml(ROOT / "afritech/ci/semantic_integrity_checks.yaml")
    checks = payload.get("checks")
    if not isinstance(checks, list):
        fail("semantic_integrity_checks.yaml must define checks")

    names = {
        check.get("name")
        for check in checks
        if isinstance(check, dict)
    }
    missing = REQUIRED_CHECKS - names
    if missing:
        fail(f"semantic integrity manifest missing checks: {sorted(missing)}")


def validate_contract_fixtures() -> None:
    admitted = admit_contract(CONTRACT_ROOT / "minimal_admit.yaml")
    if admitted["status"] != "ADMIT":
        fail("minimal semantic contract must admit")

    stages = [entry["stage"] for entry in admitted.get("trace", [])]
    if stages != CANONICAL_ORDER:
        fail("minimal semantic contract trace does not follow canonical order")

    proof = admitted.get("proof", {})
    if not proof.get("normalized_expression_hash") or not proof.get("proof_hash"):
        fail("minimal semantic contract must emit proof hashes")

    for contract_name, expected_reason in ADVERSARIAL_CONTRACTS.items():
        rejected = admit_contract(CONTRACT_ROOT / contract_name)
        if rejected["status"] != "SYSTEM_INVALID":
            fail(f"{contract_name} must fail closed")
        if rejected.get("reason") != expected_reason:
            fail(
                f"{contract_name} failed for {rejected.get('reason')}, "
                f"expected {expected_reason}"
            )

    for contract_name, expected_reason in DENIAL_CONTRACTS.items():
        denied = admit_contract(CONTRACT_ROOT / contract_name)
        if denied["status"] != "DENY":
            fail(f"{contract_name} must produce DENY")
        if denied.get("reason") != expected_reason:
            fail(
                f"{contract_name} denied for {denied.get('reason')}, "
                f"expected {expected_reason}"
            )

        stages = [entry["stage"] for entry in denied.get("trace", [])]
        if stages != CANONICAL_ORDER:
            fail(f"{contract_name} denial trace does not follow canonical order")

        proof = denied.get("proof", {})
        if proof.get("evaluated") is not False:
            fail(f"{contract_name} must emit proof of false evaluation")
        if not proof.get("normalized_expression_hash") or not proof.get("proof_hash"):
            fail(f"{contract_name} must emit denial proof hashes")


def run() -> None:
    validate_required_files()
    validate_pipeline_contract()
    validate_normalization_contract()
    validate_hash_policy()
    validate_anti_entropy()
    validate_ci_manifest()
    validate_contract_fixtures()
    print("Semantic MVP validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Semantic MVP validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
