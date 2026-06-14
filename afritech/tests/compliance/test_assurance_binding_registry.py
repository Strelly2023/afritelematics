from __future__ import annotations

import json
from copy import deepcopy

import pytest

from afritech.compliance.assurance_binding_registry import (
    AssuranceBindingRegistryError,
    build_assurance_binding_registry,
    build_continuous_assurance_proof_artifact,
    validate_assurance_binding_registry,
)


def test_happy_path():
    registry = build_assurance_binding_registry()

    assert registry is not None
    assert "bindings" in registry
    assert isinstance(registry["bindings"], list)
    assert registry["bindings"]


def test_invalid_input_structure():
    with pytest.raises(AssuranceBindingRegistryError):
        validate_assurance_binding_registry(None)  # type: ignore[arg-type]


def test_determinism():
    a = build_assurance_binding_registry()
    b = build_assurance_binding_registry()

    assert a == b


def test_replay_stability():
    r1 = build_assurance_binding_registry()
    r2 = build_assurance_binding_registry()

    assert r1 == r2


def test_tampering_detection():
    registry = build_assurance_binding_registry()

    tampered = deepcopy(registry)
    tampered["bindings"][0]["adr"] = "ADR-FAKE"

    assert tampered != registry


def test_serialization_roundtrip():
    registry = build_assurance_binding_registry()

    encoded = json.dumps(registry, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded == registry


def test_schema_integrity():
    registry = build_assurance_binding_registry()

    assert registry["schema"] == "afritech.assurance_binding_registry.v1"


def test_authority_boundary():
    registry = build_assurance_binding_registry()

    assert registry["authority_boundary"] == "binding_registry_read_only"


def test_governance_constraints():
    registry = build_assurance_binding_registry()

    for binding in registry["bindings"]:
        assert "adr" in binding
        assert "invariants" in binding
        assert "tests" in binding
        assert "guards" in binding
        assert "proof_artifacts" in binding


def test_backward_compatibility():
    registry = build_assurance_binding_registry()

    modified = deepcopy(registry)
    modified.pop("authority_boundary", None)

    assert "bindings" in modified


def test_detects_drift():
    registry = build_assurance_binding_registry()

    tampered = deepcopy(registry)
    tampered["bindings"][0]["invariants"].append("IA-999")

    assert tampered != registry


def test_reproducibility_under_load():
    registries = [build_assurance_binding_registry() for _ in range(5)]

    assert len(set(json.dumps(r, sort_keys=True) for r in registries)) == 1


def test_binding_completeness():
    registry = build_assurance_binding_registry()

    for binding in registry["bindings"]:
        assert binding["adr"].startswith("ADR-")
        assert all(inv.startswith("IA-") for inv in binding["invariants"])
        assert all(test_name.startswith("test_") for test_name in binding["tests"])
        assert all("guard_" in guard for guard in binding["guards"])


def test_missing_chain_component_fails():
    registry = build_assurance_binding_registry()

    broken = deepcopy(registry)
    broken["bindings"][0].pop("guards")

    with pytest.raises(AssuranceBindingRegistryError):
        validate_assurance_binding_registry(broken)


def test_duplicate_bindings_detected():
    registry = build_assurance_binding_registry()

    duplicated = deepcopy(registry)
    duplicated["bindings"].append(deepcopy(duplicated["bindings"][0]))

    assert len(duplicated["bindings"]) != len(set(json.dumps(b, sort_keys=True) for b in duplicated["bindings"]))


def test_invalid_binding_identifiers():
    registry = build_assurance_binding_registry()

    tampered = deepcopy(registry)
    tampered["bindings"][0]["adr"] = "INVALID"

    with pytest.raises(AssuranceBindingRegistryError):
        validate_assurance_binding_registry(tampered)


def test_proof_artifact_structure():
    registry = build_assurance_binding_registry()
    proof = build_continuous_assurance_proof_artifact(registry)

    assert proof["schema"] == "afritech.continuous_assurance_proof.v1"
    assert proof["authority_boundary"] == "continuous_assurance_proof_read_only"
    assert proof["verified"] is True
    assert len(proof["proof_hash"]) == 64
    assert len(proof["registry_hash"]) == 64
    assert proof["binding_count"] == len(registry["bindings"])


def test_validate_registry_passes():
    registry = build_assurance_binding_registry()

    result = validate_assurance_binding_registry(registry)

    assert result is True

