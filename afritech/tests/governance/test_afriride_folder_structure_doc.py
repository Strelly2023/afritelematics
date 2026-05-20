from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/implementation/AfriRide_GA_Elite_Folder_Structure.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: FOLDER STRUCTURE PLAN",
    "CLASSIFICATION: ISOLATED PRODUCT ARCHITECTURE SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

ROOT_DIRECTORIES = (
    "apps/",
    "core/",
    "api/",
    "interfaces/",
    "mobile/",
    "web/",
    "integrations/",
    "orchestration/",
    "simulation/",
    "tests/",
    "docs/",
    "config/",
    "docker/",
)

PRODUCT_APPS = (
    "ride_request/",
    "ride_matching/",
    "ride_lifecycle/",
    "pricing/",
    "driver/",
    "rider/",
    "trip_tracking/",
    "safety/",
    "payments/",
    "notifications/",
    "support/",
    "categories/",
)

ALLOWED_VALIDATION_BRIDGE_ACTIONS = (
    "calling validators",
    "reading proof outputs",
    "verifying replay traces",
)

FORBIDDEN_VALIDATION_BRIDGE_ACTIONS = (
    "modifying invariants",
    "bypassing enforcement",
    "redefining proof",
    "importing protected internal modules",
)

DRIFT_REJECTION_ITEMS = (
    "product importing AfriTech internal core",
    "orchestration redefining invariants",
    "pricing introducing randomness as authority",
    "simulation bypassing replay",
    "API overriding validator outputs",
    "feature flags disabling enforcement",
    "mobile state becoming truth authority",
)

FORBIDDEN_INFLATION = (
    "current repository exactly matches this folder structure",
    "global deployment readiness achieved",
    "validation bridge transfers authority",
    "product core is afritech core",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def test_folder_structure_has_isolated_architecture_status() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not define proof truth" in text
    assert "does not claim that every listed module is currently implemented" in text
    assert "Folder structure planning must preserve or isolate all claims." in text


def test_folder_structure_preserves_afritech_afriride_boundary() -> None:
    text = read_doc()

    assert "AfriTech (core truth) -> PRESERVE" in text
    assert "AfriRide (product system) -> ISOLATE" in text
    assert "may not redefine constitutional truth" in text
    assert "mutate invariants" in text
    assert "bypass enforcement" in text
    assert "claim authority over admissibility" in text


def test_root_structure_is_target_architecture_not_repo_state_claim() -> None:
    text = read_doc()
    root = section(text, "## Root Structure", "## Apps - Product Domain")

    for directory in ROOT_DIRECTORIES:
        assert directory in root

    assert "target architecture" in root
    assert "not a claim that the current repository has already been reshaped" in root


def test_product_apps_are_isolated_and_non_authoritative() -> None:
    text = read_doc()
    apps = section(text, "## Apps - Product Domain", "## Core Product Runtime - Not AfriTech Core")

    for app in PRODUCT_APPS:
        assert app in apps

    assert "isolated product domain" in apps
    assert "may not become sources of constitutional truth" in apps


def test_product_core_is_not_afritech_core() -> None:
    text = read_doc()
    core = section(text, "## Core Product Runtime - Not AfriTech Core", "## API Layer")

    assert "validation_bridge.py" in core
    assert "The AfriRide `core/` directory is a product-runtime configuration surface." in core
    assert "It is not the AfriTech constitutional core." in core
    assert "coordinates flows; no truth authority" in core


def test_orchestration_cannot_define_truth_or_admissibility() -> None:
    text = read_doc()
    orchestration = section(text, "## Orchestration Layer", "## Integrations")

    assert "This layer coordinates behavior," in orchestration
    assert "but cannot define truth or admissibility." in orchestration
    assert "may not redefine invariants" in orchestration
    assert "proof meaning" in orchestration
    assert "replay authority" in orchestration
    assert "enforcement integrity" in orchestration


def test_validation_bridge_is_verification_boundary_not_authority_transfer() -> None:
    text = read_doc()
    boundary = section(text, "## AfriTech Integration Boundary", "## Data Flow")

    assert "AfriRide connects to AfriTech only through:" in boundary
    assert "core/services/validation_bridge.py" in boundary
    for action in ALLOWED_VALIDATION_BRIDGE_ACTIONS:
        assert action in boundary
    for action in FORBIDDEN_VALIDATION_BRIDGE_ACTIONS:
        assert action in boundary
    assert "The validation bridge is a verification boundary." in boundary
    assert "It is not an authority transfer mechanism." in boundary


def test_folder_structure_rejects_boundary_drift_vectors() -> None:
    text = read_doc()
    drift = section(text, "## Drift Detection - Folder Level", "## Final Compression")

    for item in DRIFT_REJECTION_ITEMS:
        assert item in drift


def test_folder_structure_preserves_proof_boundary_and_avoids_inflation() -> None:
    text = read_doc()

    assert "does not modify `afritech.demo.proof`" in text
    assert "does not expand proof scope beyond the bounded AfriRide domain" in text
    assert "does not claim global deployment readiness" in text
    assert "does not claim global deployment readiness or assert that every listed folder currently exists" in text

    lowered = text.lower()
    for claim in FORBIDDEN_INFLATION:
        assert claim not in lowered
