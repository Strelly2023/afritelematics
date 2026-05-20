from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[3]
CI_AUTHORITY = ROOT / "afritech/ci/CI_AUTHORITY.yaml"
CLAIM_BINDINGS = ROOT / "afritech/constitution/CLAIM_EVIDENCE_BINDINGS.yaml"
IMPLEMENTATION_REGISTRY = ROOT / "afritech/architecture/implementation_registry.yaml"
AFRIRIDE_SPEC = ROOT / "docs/requirements/AfriRide_Rider_Features_and_Experience.md"

CANONICAL_COMMANDS = (
    "python3 -m afritech.ci.constitutional_pipeline",
    "python -m afritech.ci.constitutional_pipeline",
)

EXPECTED_WORKFLOWS = (
    ".github/workflows/architecture.yml",
    ".github/workflows/constitutional_ci.yml",
    ".github/workflows/constitutional_enforcement.yml",
    ".github/workflows/ga_plus_plus_plus.yml",
)

EXPECTED_IMPLEMENTED_CLAIMS = (
    "continuity_under_simulated_disruption",
    "deterministic_replay",
    "identity_and_coordination_continuity",
    "enforcement_integrity",
)

FORBIDDEN_CLAIM_STATEMENT_TERMS = (
    "global deployment readiness",
    "mass market operational",
    "production business platform",
)


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_ci_authority_declares_single_canonical_gate() -> None:
    payload = load_yaml(CI_AUTHORITY)

    assert payload["schema"] == "afritech.ci.authority.v1"
    assert payload["status"] == "PROVEN_GOVERNANCE"
    assert payload["classification"] == "AUTHORITY_COMPRESSION"
    assert payload["canonical_gate"]["id"] == "canonical_constitutional_pipeline"
    assert payload["canonical_gate"]["command"] == "python3 -m afritech.ci.constitutional_pipeline"
    assert payload["canonical_gate"]["authority"] == "CI_ADMISSIBILITY_GATE"
    assert "Only the canonical constitutional pipeline defines CI admissibility." in payload["canonical_gate"]["rule"]


def test_all_workflows_are_registered_and_invoke_canonical_pipeline() -> None:
    payload = load_yaml(CI_AUTHORITY)
    workflow_roles = payload["workflow_roles"]

    assert tuple(workflow_roles) == EXPECTED_WORKFLOWS
    for workflow in EXPECTED_WORKFLOWS:
        role = workflow_roles[workflow]
        assert role["must_invoke_canonical_gate"] is True
        assert role["role"].startswith("supporting_")

        text = (ROOT / workflow).read_text(encoding="utf-8")
        assert any(command in text for command in CANONICAL_COMMANDS), workflow


def test_ci_authority_rules_prevent_workflow_authority_fragmentation() -> None:
    payload = load_yaml(CI_AUTHORITY)
    statements = {rule["statement"] for rule in payload["rules"]}

    assert "Only canonical_pipeline defines CI admissibility; workflows are adapters or supporting gates." in statements
    assert "Workflows may invoke validators but may not redefine proof truth, invariants, or admissibility." in statements
    assert "Supporting workflows must invoke the canonical constitutional pipeline before making completion claims." in statements


def test_claim_evidence_bindings_define_implemented_claims_with_evidence() -> None:
    payload = load_yaml(CLAIM_BINDINGS)

    assert payload["schema"] == "afritech.constitution.claim_evidence_bindings.v1"
    assert payload["status"] == "PROVEN_GOVERNANCE"
    assert payload["authority"] == "afritech.demo.proof"
    assert payload["binding_rule"] == "No IMPLEMENTED claim is admissible without executable evidence and validator binding."

    claims = payload["claims"]
    assert tuple(claim["id"] for claim in claims) == EXPECTED_IMPLEMENTED_CLAIMS
    for claim in claims:
        assert claim["status"] == "IMPLEMENTED"
        assert claim["scope"]
        assert isinstance(claim["evidence"], list) and claim["evidence"]
        assert isinstance(claim["validators"], list) and claim["validators"]
        assert isinstance(claim["non_claims"], list) and claim["non_claims"]


def test_claim_evidence_bindings_do_not_inflate_readiness() -> None:
    payload = load_yaml(CLAIM_BINDINGS)

    for claim in payload["claims"]:
        statement = claim["statement"].lower()
        for term in FORBIDDEN_CLAIM_STATEMENT_TERMS:
            assert term not in statement

    non_claims = {
        non_claim
        for claim in payload["claims"]
        for non_claim in claim["non_claims"]
    }
    assert "global_deployment_readiness" in non_claims
    assert "production_business_platform_readiness" in non_claims


def test_canonical_implementation_registry_and_afriride_spec_exist() -> None:
    assert IMPLEMENTATION_REGISTRY.exists()
    registry = load_yaml(IMPLEMENTATION_REGISTRY)
    assert registry["schema"].startswith("afritech.")

    assert AFRIRIDE_SPEC.exists()
    spec_text = AFRIRIDE_SPEC.read_text(encoding="utf-8")
    assert "STATUS: OPERATIONAL REQUIREMENTS" in spec_text
    assert "CLASSIFICATION: ISOLATED OPERATIONAL REQUIREMENTS SURFACE" in spec_text
    assert "GOVERNANCE MODE: PRESERVE OR ISOLATE" in spec_text
