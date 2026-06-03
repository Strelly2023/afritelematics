from __future__ import annotations

from pathlib import Path

import yaml

from afritech.architecture.registry_loader import load_implementation_registry
from afritech.ci.claim_discipline_validator import validate


ROOT = Path(__file__).resolve().parents[3]
CLAIM_BINDINGS = ROOT / "afritech/constitution/CLAIM_EVIDENCE_BINDINGS.yaml"
IMPLEMENTATION_REGISTRY = ROOT / "afritech/architecture/implementation_registry.yaml"

EXPECTED_BINDING_CLAIMS = (
    "continuity_under_simulated_disruption",
    "deterministic_replay",
    "identity_and_coordination_continuity",
    "enforcement_integrity",
)


def test_claim_discipline_policy_validates() -> None:
    validate()


def test_claim_evidence_bindings_are_validated_by_claim_gate() -> None:
    payload = yaml.safe_load(CLAIM_BINDINGS.read_text(encoding="utf-8"))

    assert payload["schema"] == "afritech.constitution.claim_evidence_bindings.v1"
    assert payload["binding_rule"] == "No IMPLEMENTED claim is admissible without executable evidence and validator binding."
    assert tuple(claim["id"] for claim in payload["claims"]) == EXPECTED_BINDING_CLAIMS

    for claim in payload["claims"]:
        assert claim["status"] == "IMPLEMENTED"
        assert claim["evidence"]
        assert claim["implementation_refs"]
        assert claim["validators"]
        assert claim["non_claims"]


def test_claim_evidence_bindings_reference_implemented_registry_surfaces() -> None:
    bindings = yaml.safe_load(CLAIM_BINDINGS.read_text(encoding="utf-8"))
    registry = load_implementation_registry()
    implementations = registry["implementations"]

    for claim in bindings["claims"]:
        for implementation_ref in claim["implementation_refs"]:
            implementation = implementations[implementation_ref]
            assert implementation["implementation_state"] == "IMPLEMENTED"
            assert implementation["semantic_properties"]["replay_admissible"] is True
            assert implementation["semantic_properties"]["proof_admissible"] is True
            assert implementation["semantic_properties"]["deterministic_execution"] is True
