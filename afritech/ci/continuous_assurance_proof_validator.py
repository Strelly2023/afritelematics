"""Validate the continuous assurance proof artifact derived from the binding registry."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from afritech.compliance.assurance_binding_registry import (
    AssuranceBindingRegistryError,
    build_assurance_binding_registry,
    build_continuous_assurance_proof_artifact,
    export_continuous_assurance_proof_artifact,
    validate_assurance_binding_registry,
)


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports/continuous_assurance_proof_v1"
REPORT_FILE = REPORT_DIR / "continuous_assurance_proof.json"


class ContinuousAssuranceProofValidationError(RuntimeError):
    """Raised when the continuous assurance proof validation fails."""


@dataclass(frozen=True)
class ContinuousAssuranceProofReport:
    registry_hash: str
    proof_hash: str
    binding_count: int
    invariant_count: int
    guard_count: int
    verified: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.continuous_assurance_proof_validation_report.v1",
            "registry_hash": self.registry_hash,
            "proof_hash": self.proof_hash,
            "binding_count": self.binding_count,
            "invariant_count": self.invariant_count,
            "guard_count": self.guard_count,
            "verified": self.verified,
        }


def validate(*, write_artifacts: bool = False) -> ContinuousAssuranceProofReport:
    registry = build_assurance_binding_registry()
    try:
        validate_assurance_binding_registry(registry)
    except AssuranceBindingRegistryError as exc:
        raise ContinuousAssuranceProofValidationError(str(exc)) from exc

    proof = build_continuous_assurance_proof_artifact(registry)
    report = ContinuousAssuranceProofReport(
        registry_hash=str(registry["registry_hash"]),
        proof_hash=str(proof["proof_hash"]),
        binding_count=len(registry["bindings"]),
        invariant_count=len(proof["invariant_ids"]),
        guard_count=len(proof["guard_names"]),
        verified=(
            proof["verified"] is True
            and proof["registry_hash"] == registry["registry_hash"]
            and proof["binding_count"] == len(registry["bindings"])
        ),
    )
    if not report.verified:
        raise ContinuousAssuranceProofValidationError("continuous assurance proof validation failed")

    if write_artifacts:
        export_continuous_assurance_proof_artifact(proof, REPORT_DIR)

    if REPORT_FILE.exists():
        _validate_report_file(REPORT_FILE, report)

    return report


def _validate_report_file(path: Path, report: ContinuousAssuranceProofReport) -> None:
    payload = _load_json(path)
    if payload.get("proof_hash") != report.proof_hash:
        raise ContinuousAssuranceProofValidationError("continuous assurance proof hash mismatch")
    if payload.get("registry_hash") != report.registry_hash:
        raise ContinuousAssuranceProofValidationError("continuous assurance registry hash mismatch")
    if payload.get("verified") is not True:
        raise ContinuousAssuranceProofValidationError("continuous assurance proof artifact not verified")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContinuousAssuranceProofValidationError(f"proof artifact must be an object: {path}")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = validate(write_artifacts=args.write_artifacts)
    except ContinuousAssuranceProofValidationError as exc:
        print(f"CONTINUOUS_ASSURANCE_PROOF_VALIDATOR: FAIL ({exc})")
        return 1

    print(
        "CONTINUOUS_ASSURANCE_PROOF_VALIDATOR: PASS "
        f"(registry_hash={report.registry_hash}, proof_hash={report.proof_hash}, "
        f"bindings={report.binding_count}, invariants={report.invariant_count}, guards={report.guard_count})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
