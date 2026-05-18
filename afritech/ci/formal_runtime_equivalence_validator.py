"""Validate that formal Level 2 obligations are wired to runtime CI."""

from __future__ import annotations

import sys

from afritech.ci.completion_utils import ROOT, fail, load_yaml, main_result


LEVEL2_MODEL = ROOT / "afritech/constitution/level2_formal_model.yaml"


def validate() -> None:
    from afritech.ci.constitutional_validation import SUBSYSTEMS
    from afritech.ci.constitutional_pipeline import PIPELINE

    model = load_yaml(LEVEL2_MODEL)
    verifiers = {
        theorem.get("verifier")
        for theorem in model.get("theorems", [])
        if isinstance(theorem, dict)
    }

    subsystem_modules = {subsystem.module for subsystem in SUBSYSTEMS}
    pipeline_modules = {
        step.command[-1]
        for step in PIPELINE
        if len(step.command) >= 3 and step.command[-2] == "-m"
    }

    wired = subsystem_modules | pipeline_modules
    missing = sorted(
        verifier for verifier in verifiers
        if isinstance(verifier, str) and verifier not in wired
    )

    allowed_documented = {
        "afritech.ci.receipt_validator",
        "afritech.ci.identity_validator",
        "afritech.ci.semantic_kernel_validator",
        "afritech.ci.trace_reconstruction_validator",
        "afritech.verify.verify_execution_lineage",
        "afritech.verify.verify_multi_epoch_replay",
        "afritech.ci.constitutional_validation",
    }
    unresolved = sorted(set(missing) - allowed_documented)
    if unresolved:
        fail(f"Level 2 verifiers are not runtime/CI wired: {unresolved}")

    print(f"✅ Level 2 verifier bindings checked: {len(verifiers)}")


def main() -> int:
    return main_result("Formal runtime equivalence validation", validate)


if __name__ == "__main__":
    sys.exit(main())
