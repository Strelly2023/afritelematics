"""Canonical binding registry for continuous assurance traceability."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "afritech.assurance_binding_registry.v1"
AUTHORITY_BOUNDARY = "binding_registry_read_only"
ADR_ID = "ADR-0022"
INVARIANT_IDS = tuple(f"IA-{index:03d}" for index in range(1, 12))
GUARD_NAMES = ("guard_runtime_boundary_governance", "guard_test_contract_enforcement")


class AssuranceBindingRegistryError(RuntimeError):
    """Raised when the assurance binding registry is invalid."""


def build_assurance_binding_registry() -> dict[str, Any]:
    bindings = [
        {
            "binding_id": "continuous_assurance_contract",
            "adr": ADR_ID,
            "invariants": list(INVARIANT_IDS),
            "tests": [
                "test_invariants_accept_replay_safe_package",
                "test_same_evidence_set_produces_same_package_hash",
                "test_evidence_order_cannot_change_truth",
                "test_evidence_mutation_changes_hash",
                "test_dashboard_cannot_mutate_evidence",
                "test_package_is_evidence_only_and_has_authority_boundary",
                "test_external_evidence_is_never_automatically_trusted",
                "test_missing_evidence_fails_visibly",
                "test_package_schema_is_stable_and_replay_is_deterministic",
            ],
            "guards": list(GUARD_NAMES),
            "proof_artifacts": [
                "continuous_assurance_proof.json",
                "docs/reviews/AFRITECH_RUNTIME_BOUNDARY_SCAN.md",
                "docs/operations/AFRIPAY_CONTINUOUS_ASSURANCE_DASHBOARD.md",
            ],
        },
        {
            "binding_id": "continuous_assurance_threats",
            "adr": ADR_ID,
            "invariants": ["IA-001", "IA-004", "IA-006", "IA-007", "IA-008", "IA-010", "IA-011"],
            "tests": [
                "test_threat_simulation_detects_all_scenarios_and_live_ai_alerts",
                "test_threat_simulation_is_deterministic",
                "test_threat_simulation_serialization_roundtrip",
                "test_threat_simulation_rejects_invalid_baseline",
            ],
            "guards": list(GUARD_NAMES),
            "proof_artifacts": [
                "continuous_assurance_threats.json",
                "continuous_assurance_proof.json",
            ],
        },
        {
            "binding_id": "continuous_assurance_proof_artifact",
            "adr": ADR_ID,
            "invariants": ["IA-001", "IA-002", "IA-003", "IA-008", "IA-009", "IA-010", "IA-011"],
            "tests": [
                "test_recursive_proof_generates_auditable_artifact",
                "test_recursive_proof_is_deterministic",
                "test_real_groth16_proof_execution_evidence_if_configured",
                "test_proof_hash_matches_exported_artifact",
                "test_third_party_verifier_accepts_valid_evidence",
            ],
            "guards": list(GUARD_NAMES),
            "proof_artifacts": [
                "recursive_proof_bundle.json",
                "recursive_proof_bundle.pdf",
                "continuous_assurance_proof.json",
            ],
        },
    ]
    registry = {
        "schema": SCHEMA,
        "title": "AfriPay Assurance Binding Registry",
        "authority_boundary": AUTHORITY_BOUNDARY,
        "adr": ADR_ID,
        "bindings": bindings,
    }
    registry["registry_hash"] = _canonical_hash(registry)
    return registry


def validate_assurance_binding_registry(registry: Mapping[str, Any] | dict[str, Any] | None) -> bool:
    if registry is None:
        raise AssuranceBindingRegistryError("registry must not be None")
    payload = _coerce_mapping(registry)

    if payload.get("schema") != SCHEMA:
        raise AssuranceBindingRegistryError("registry schema mismatch")
    if payload.get("authority_boundary") != AUTHORITY_BOUNDARY:
        raise AssuranceBindingRegistryError("registry authority boundary mismatch")
    if payload.get("adr") != ADR_ID:
        raise AssuranceBindingRegistryError("registry adr mismatch")

    bindings = payload.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise AssuranceBindingRegistryError("registry must define bindings")

    canonical_bindings: list[str] = []
    seen_binding_ids: set[str] = set()
    covered_invariants: set[str] = set()
    covered_guards: set[str] = set()
    covered_tests: set[str] = set()

    for index, binding in enumerate(bindings, start=1):
        if not isinstance(binding, dict):
            raise AssuranceBindingRegistryError(f"binding {index} must be a mapping")
        binding_id = binding.get("binding_id")
        adr = binding.get("adr")
        invariants = binding.get("invariants")
        tests = binding.get("tests")
        guards = binding.get("guards")
        proof_artifacts = binding.get("proof_artifacts")

        if not isinstance(binding_id, str) or not binding_id.strip():
            raise AssuranceBindingRegistryError(f"binding {index} missing binding_id")
        if binding_id in seen_binding_ids:
            raise AssuranceBindingRegistryError(f"duplicate binding_id: {binding_id}")
        seen_binding_ids.add(binding_id)

        if not isinstance(adr, str) or not adr.startswith("ADR-"):
            raise AssuranceBindingRegistryError(f"invalid adr for binding {binding_id}")
        if adr != ADR_ID:
            raise AssuranceBindingRegistryError(f"unexpected adr for binding {binding_id}")

        if not isinstance(invariants, list) or not invariants:
            raise AssuranceBindingRegistryError(f"binding {binding_id} must define invariants")
        if not isinstance(tests, list) or not tests:
            raise AssuranceBindingRegistryError(f"binding {binding_id} must define tests")
        if not isinstance(guards, list) or not guards:
            raise AssuranceBindingRegistryError(f"binding {binding_id} must define guards")
        if not isinstance(proof_artifacts, list) or not proof_artifacts:
            raise AssuranceBindingRegistryError(f"binding {binding_id} must define proof_artifacts")

        if len(set(invariants)) != len(invariants):
            raise AssuranceBindingRegistryError(f"duplicate invariants in binding {binding_id}")
        if len(set(tests)) != len(tests):
            raise AssuranceBindingRegistryError(f"duplicate tests in binding {binding_id}")
        if len(set(guards)) != len(guards):
            raise AssuranceBindingRegistryError(f"duplicate guards in binding {binding_id}")
        if len(set(proof_artifacts)) != len(proof_artifacts):
            raise AssuranceBindingRegistryError(f"duplicate proof artifacts in binding {binding_id}")

        for invariant in invariants:
            if not isinstance(invariant, str) or not invariant.startswith("IA-"):
                raise AssuranceBindingRegistryError(f"invalid invariant identifier in {binding_id}: {invariant}")
            covered_invariants.add(invariant)
        for test_name in tests:
            if not isinstance(test_name, str) or not test_name.startswith("test_"):
                raise AssuranceBindingRegistryError(f"invalid test identifier in {binding_id}: {test_name}")
            covered_tests.add(test_name)
        for guard_name in guards:
            if not isinstance(guard_name, str) or "guard_" not in guard_name:
                raise AssuranceBindingRegistryError(f"invalid guard identifier in {binding_id}: {guard_name}")
            covered_guards.add(guard_name)
        for artifact in proof_artifacts:
            if not isinstance(artifact, str) or not artifact.strip():
                raise AssuranceBindingRegistryError(f"invalid proof artifact in {binding_id}: {artifact}")

        canonical_bindings.append(_canonical_hash(binding))

    missing_invariants = tuple(invariant for invariant in INVARIANT_IDS if invariant not in covered_invariants)
    if missing_invariants:
        raise AssuranceBindingRegistryError(
            "registry missing invariant coverage: " + ", ".join(missing_invariants)
        )
    missing_guards = tuple(guard for guard in GUARD_NAMES if guard not in covered_guards)
    if missing_guards:
        raise AssuranceBindingRegistryError(
            "registry missing guard coverage: " + ", ".join(missing_guards)
        )

    if not any(test_name.startswith("test_same_evidence_set") for test_name in covered_tests):
        raise AssuranceBindingRegistryError("registry missing evidence contract tests")
    if not any(test_name.startswith("test_threat_simulation") for test_name in covered_tests):
        raise AssuranceBindingRegistryError("registry missing threat simulation tests")
    if not any(test_name.startswith("test_recursive_proof") or test_name.startswith("test_proof_hash") for test_name in covered_tests):
        raise AssuranceBindingRegistryError("registry missing proof artifact tests")

    expected_hash = _canonical_hash({k: v for k, v in payload.items() if k != "registry_hash"})
    if payload.get("registry_hash") != expected_hash:
        raise AssuranceBindingRegistryError("registry hash mismatch")

    if len(canonical_bindings) != len(set(canonical_bindings)):
        raise AssuranceBindingRegistryError("duplicate binding entries detected")

    return True


def build_continuous_assurance_proof_artifact(
    registry: Mapping[str, Any] | dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = build_assurance_binding_registry() if registry is None else _coerce_mapping(registry)
    validate_assurance_binding_registry(payload)
    binding_hashes = [_canonical_hash(binding) for binding in payload["bindings"]]
    proof = {
        "schema": "afritech.continuous_assurance_proof.v1",
        "authority_boundary": "continuous_assurance_proof_read_only",
        "registry_hash": payload["registry_hash"],
        "registry_schema": payload["schema"],
        "binding_count": len(payload["bindings"]),
        "binding_hashes": binding_hashes,
        "invariant_ids": list(INVARIANT_IDS),
        "guard_names": list(GUARD_NAMES),
        "verified": True,
    }
    proof["proof_hash"] = _canonical_hash(proof)
    return proof


def export_continuous_assurance_proof_artifact(
    proof: Mapping[str, Any] | dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Path]:
    payload = _coerce_mapping(proof)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "continuous_assurance_proof.json"
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    return {"json": json_path}


def _coerce_mapping(value: Mapping[str, Any] | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return dict(value)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


__all__ = [
    "ADR_ID",
    "AUTHORITY_BOUNDARY",
    "INVARIANT_IDS",
    "SCHEMA",
    "AssuranceBindingRegistryError",
    "build_assurance_binding_registry",
    "validate_assurance_binding_registry",
    "build_continuous_assurance_proof_artifact",
    "export_continuous_assurance_proof_artifact",
]
