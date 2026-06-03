"""
afritech.ci.distributed_scale_validator

CI validator for AfriTech distributed scale layer.

This validator enforces that distributed scale remains:
- operational
- non-sovereign
- deterministic
- replay-safe
- closed-world aligned
- infrastructure-independent
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import yaml


# ============================================================
# ERROR
# ============================================================

class DistributedScaleValidatorError(ValueError):
    pass


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class DistributedScaleValidationResult:
    passed: bool
    checked_contracts: int
    failures: tuple[str, ...]

    def report(self) -> str:
        if self.passed:
            return (
                "✅ Distributed scale validation PASSED\n"
                f"✅ Checked contracts: {self.checked_contracts}"
            )
        return (
            "❌ Distributed scale validation FAILED\n"
            f"❌ Checked contracts: {self.checked_contracts}\n"
            + "\n".join(self.failures)
        )


# ============================================================
# CONSTANTS
# ============================================================

REQUIRED_TOP_LEVEL = {
    "schema",
    "version",
    "metadata",
    "distributed_scale_contract",
    "partition_semantics",
    "worker_semantics",
    "coordinator_semantics",
    "distributed_replay",
    "recovery_semantics",
    "closed_world_alignment",
    "replay_alignment",
    "failure_modes",
    "ci_enforcement",
    "safety",
    "constitutional_assertion",
}

REQUIRED_CONTRACT_ROLE = {
    "partition_events",
    "route_to_workers",
    "preserve_order_per_partition",
    "record_worker_decisions",
    "support_deterministic_recovery",
    "preserve_replay_equivalence",
}

REQUIRED_CONTRACT_FORBIDDEN = {
    "define_execution_truth",
    "bypass_replay",
    "mutate_core_state_directly",
    "use_random_partitioning",
    "use_wall_clock_as_authority",
    "accept_unrecorded_worker_output",
    "permit_undeclared_worker_execution",
    "permit_hidden_retry_semantics",
    "allow_infrastructure_defined_legitimacy",
}

REQUIRED_CONTRACT_REQUIRED = {
    "canonical_partition_identity",
    "deterministic_routing",
    "replay_equivalent_worker_output",
    "append_only_execution_log",
    "fail_closed_on_divergence",
    "infrastructure_independent_replay",
    "explicit_worker_registration",
    "immutable_execution_transcripts",
}

REQUIRED_CI_VALIDATORS = {
    "distributed_scale_validator",
    "distributed_partition_validator",
    "distributed_worker_validator",
    "distributed_replay_validator",
    "distributed_recovery_validator",
    "distributed_transcript_validator",
}


# ============================================================
# CORE VALIDATION
# ============================================================

def validate_scale_contract_file(path: Path) -> None:

    if not path.exists():
        raise DistributedScaleValidatorError(f"missing scale contract: {path}")

    if path.suffix not in {".yaml", ".yml"}:
        raise DistributedScaleValidatorError(f"{path}: must be YAML")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DistributedScaleValidatorError(f"{path}: invalid YAML") from exc

    if not isinstance(data, dict):
        raise DistributedScaleValidatorError(f"{path}: root must be mapping")

    # strict non-empty contract
    if not data:
        raise DistributedScaleValidatorError(f"{path}: empty contract")

    _validate_top_level(data, path)
    _validate_metadata(data, path)
    _validate_scale_contract(data, path)
    _validate_partition_semantics(data, path)
    _validate_worker_semantics(data, path)
    _validate_coordinator_semantics(data, path)
    _validate_distributed_replay(data, path)
    _validate_recovery_semantics(data, path)
    _validate_closed_world_alignment(data, path)
    _validate_replay_alignment(data, path)
    _validate_ci_enforcement(data, path)
    _validate_safety(data, path)


# ============================================================
# SECTION VALIDATORS
# ============================================================

def _validate_top_level(data, path):
    missing = REQUIRED_TOP_LEVEL - set(data.keys())
    if missing:
        raise DistributedScaleValidatorError(
            f"{path}: missing keys: {', '.join(sorted(missing))}"
        )

    if data["schema"] != "afritech.distributed.scale_contract.v1":
        raise DistributedScaleValidatorError(f"{path}: invalid schema")

    if data["version"] != 1:
        raise DistributedScaleValidatorError(f"{path}: version must be 1")


def _validate_metadata(data, path):
    m = _mapping(data, "metadata", path)

    _require_equal(m, "authority", "OPERATIONAL", path)
    _require_equal(m, "status", "ACTIVE", path)
    _require_equal(m, "mutability", "CONTROLLED", path)
    _require_equal(
        m, "registry_class", "DISTRIBUTED_SCALE_CONTRACT", path
    )


def _validate_scale_contract(data, path):
    c = _mapping(data, "distributed_scale_contract", path)

    role = set(_list(c, "role", path))
    forbidden = set(_list(c, "forbidden", path))
    required = set(_list(c, "required", path))

    _require_subset(REQUIRED_CONTRACT_ROLE, role, path, "role")
    _require_subset(REQUIRED_CONTRACT_FORBIDDEN, forbidden, path, "forbidden")
    _require_subset(REQUIRED_CONTRACT_REQUIRED, required, path, "required")

    _forbid_overlap(role, forbidden, path, "role vs forbidden")
    _forbid_overlap(required, forbidden, path, "required vs forbidden")


def _validate_partition_semantics(data, path):
    p = _mapping(data, "partition_semantics", path)
    r = _mapping(p, "routing", path)
    o = _mapping(p, "ordering", path)

    for k in ("deterministic", "replay_safe", "infrastructure_independent"):
        _require_true(r, k, path)

    for k in (
        "preserve_fifo_per_partition",
        "canonical_sequence_required",
        "replay_equivalent_order_required",
    ):
        _require_true(o, k, path)


def _validate_worker_semantics(data, path):
    w = _mapping(data, "worker_semantics", path)
    identity = _mapping(w, "worker_identity", path)
    execution = _mapping(w, "execution", path)

    for k in (
        "explicit_registration_required",
        "replay_safe_identity",
        "deterministic_assignment",
    ):
        _require_true(identity, k, path)

    for k in (
        "deterministic_execution_required",
        "replay_equivalence_required",
        "append_only_execution_required",
        "provisional_until_replay_confirmation",
    ):
        _require_true(execution, k, path)


def _validate_coordinator_semantics(data, path):
    c = _mapping(data, "coordinator_semantics", path)
    auth = _mapping(c, "authority", path)

    if auth.get("truth_authority") is not False:
        raise DistributedScaleValidatorError(f"{path}: truth authority must be false")

    if auth.get("replay_authority") is not False:
        raise DistributedScaleValidatorError(f"{path}: replay authority must be false")


def _validate_distributed_replay(data, path):
    r = _mapping(data, "distributed_replay", path)
    required = _list(r, "replay_requirements", path)

    if len(required) == 0:
        raise DistributedScaleValidatorError(f"{path}: empty replay requirements")


def _validate_recovery_semantics(data, path):
    r = _mapping(data, "recovery_semantics", path)
    g = _list(r, "guarantees", path)

    if len(g) == 0:
        raise DistributedScaleValidatorError(f"{path}: empty recovery guarantees")


def _validate_closed_world_alignment(data, path):
    c = _mapping(data, "closed_world_alignment", path)
    _require_non_empty_list(c, "required", path)
    _require_non_empty_list(c, "forbidden", path)


def _validate_replay_alignment(data, path):
    r = _mapping(data, "replay_alignment", path)

    for k in (
        "replay_safe_required",
        "deterministic_execution_required",
        "witness_alignment_required",
        "invariant_preservation_required",
    ):
        _require_true(r, k, path)


def _validate_ci_enforcement(data, path):
    ci = _mapping(data, "ci_enforcement", path)
    vals = set(_list(ci, "validators", path))

    _require_subset(REQUIRED_CI_VALIDATORS, vals, path, "ci validators")

    if ci.get("failure_mode") != "CI_FAIL":
        raise DistributedScaleValidatorError(f"{path}: CI must fail on violation")


def _validate_safety(data, path):
    s = _mapping(data, "safety", path)

    _require_non_empty_list(s, "guarantees", path)
    _require_non_empty_list(s, "forbid", path)

    e = _mapping(s, "enforcement", path)

    if e.get("violation_action") != "FAIL_FAST":
        raise DistributedScaleValidatorError(f"{path}: must FAIL_FAST")


# ============================================================
# HELPERS
# ============================================================

def _mapping(d, key, path):
    v = d.get(key)
    if not isinstance(v, dict):
        raise DistributedScaleValidatorError(f"{path}: {key} must be mapping")
    return v


def _list(d, key, path):
    v = d.get(key)
    if not isinstance(v, list) or not all(isinstance(i, str) for i in v):
        raise DistributedScaleValidatorError(f"{path}: {key} must be list[str]")
    return v


def _require_true(d, key, path):
    if d.get(key) is not True:
        raise DistributedScaleValidatorError(f"{path}: {key} must be true")


def _require_equal(d, key, value, path):
    if d.get(key) != value:
        raise DistributedScaleValidatorError(f"{path}: {key} must be {value}")


def _require_subset(required, actual, path, field):
    missing = required - actual
    if missing:
        raise DistributedScaleValidatorError(
            f"{path}: {field} missing: {', '.join(sorted(missing))}"
        )


def _forbid_overlap(a, b, path, name):
    overlap = a & b
    if overlap:
        raise DistributedScaleValidatorError(
            f"{path}: {name} overlap: {', '.join(sorted(overlap))}"
        )


def _require_non_empty_list(d, key, path):
    v = d.get(key)
    if not isinstance(v, list) or not v:
        raise DistributedScaleValidatorError(
            f"{path}: {key} must be non-empty list"
        )


# ============================================================
# ENTRYPOINT
# ============================================================

def validate_distributed_scale() -> DistributedScaleValidationResult:

    path = Path("afritech/distributed/contracts/scale_contract.yaml")

    failures = []

    try:
        validate_scale_contract_file(path)
    except DistributedScaleValidatorError as exc:
        failures.append(str(exc))

    return DistributedScaleValidationResult(
        passed=not failures,
        checked_contracts=1,
        failures=tuple(failures),
    )


def main() -> int:
    result = validate_distributed_scale()
    print(result.report())
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())