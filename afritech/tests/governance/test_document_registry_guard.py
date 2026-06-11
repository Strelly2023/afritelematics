from __future__ import annotations

from pathlib import Path

import yaml

from afritech.guards.document_registry_guard import validate


ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "afritech/governance/document_registry.yaml"
SWEEP = ROOT / "docs/reviews/AFRITECH_CANONICAL_CONFLICT_SWEEP.md"

EXPECTED_REGISTERED_DOCS = (
    "docs/README.md",
    "afritech/constitution/AFRITECH_CONSTITUTION_V1.md",
    "docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md",
    "docs/pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md",
    "docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md",
    "docs/pilot/AFRIRIDE_PHASE3_LIVE_OPERATIONS_MONITORING_GOVERNANCE_SPEC.md",
    "docs/mobile/AFRIRIDE_MOBILE_PLATFORM_READINESS.md",
    "docs/business/AFRITECH_FIRST_REVENUE_CONVERSION_PLAN.md",
    "docs/reviews/AFRITECH_DOCUMENTATION_AUTHORITY_AUDIT.md",
    "docs/reviews/AFRITECH_CANONICAL_CONFLICT_SWEEP.md",
)

EXPECTED_HISTORICAL_CONFLICTS = (
    "docs/AfriTech_Final_Canonical.md",
    "docs/Afritech_Canonical_Specification_final.md",
    "docs/afritech_canonical_specification.md",
    "docs/AfriTech_Terminal_Canonical_Closure.md",
    "docs/AfriTech_Final_Irreducible_Admissibility_Algebra.md",
    "docs/AfriTech_Irreducible_Admissibility_Algebra.md",
)


def load_registry() -> dict:
    payload = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_document_registry_declares_active_authority_surfaces() -> None:
    registry = load_registry()

    assert registry["schema"] == "afritech.governance.document_registry.v1"
    assert registry["version"] == "1.0.0"
    assert registry["status"] == "ACTIVE"
    assert registry["classification"] == "DOCUMENT_AUTHORITY_REGISTRY"

    documents = registry["documents"]
    assert tuple(entry["path"] for entry in documents) == EXPECTED_REGISTERED_DOCS

    authorities = {entry["authority"] for entry in documents}
    assert "ROOT_NAVIGATION" in authorities
    assert "CONSTITUTIONAL_ROOT" in authorities
    assert "ARCHITECTURE_ROOT" in authorities
    assert "BOUNDED_OPERATIONAL_GATE" in authorities
    architecture_doc = next(entry for entry in documents if entry["id"] == "DOC-ARCH-001")
    assert architecture_doc["binds"]["code_surfaces"] == [
        "afriride_system/backend/trace_enforcement.py",
        "afriride_system/backend/replay_engine.py",
        "afriride_system/backend/evidence_engine.py",
        "afriride_system/backend/receipt_engine.py",
    ]
    assert "I6_REPLAY_AUTHORITY" in architecture_doc["binds"]["invariants"]


def test_document_registry_tracks_historical_conflicts_explicitly() -> None:
    registry = load_registry()

    conflicts = registry["historical_conflicts"]
    assert tuple(entry["path"] for entry in conflicts) == EXPECTED_HISTORICAL_CONFLICTS
    assert {
        entry["disposition"] for entry in conflicts
    } == {"HISTORICAL_NARRATIVE_NOT_ACTIVE_AUTHORITY"}


def test_document_registry_guard_validates_clean_authority_order() -> None:
    report = validate()

    assert report.clean is True
    assert report.registry_path == "afritech/governance/document_registry.yaml"
    assert report.registry_version == "1.0.0"
    assert report.registered_document_count == len(EXPECTED_REGISTERED_DOCS)
    assert report.historical_conflict_count == len(EXPECTED_HISTORICAL_CONFLICTS)
    assert report.root_navigation_doc == "docs/README.md"
    assert report.constitutional_root_doc == "afritech/constitution/AFRITECH_CONSTITUTION_V1.md"
    assert report.architecture_root_doc == "docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md"
    assert report.invariant_binding_count >= 10
    assert report.code_surface_binding_count == 4
    assert report.unregistered_authority_claims == ()
    assert report.unbound_registered_docs == ()
    assert report.invalid_invariant_bindings == ()
    assert report.invalid_code_surface_bindings == ()
    assert report.module_metadata_mismatches == ()
    assert report.module_version_mismatches == ()


def test_canonical_conflict_sweep_binds_historical_files_to_non_authority() -> None:
    text = SWEEP.read_text(encoding="utf-8")

    for item in (
        "CANONICAL CONFLICT SWEEP",
        "HISTORICAL_AUTHORITY_CONFLICT_REVIEW",
        "document_registry.yaml",
        "not active authority",
        "re-ratified",
        "registered order wins",
        *EXPECTED_HISTORICAL_CONFLICTS,
    ):
        assert item in text
