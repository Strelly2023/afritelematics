from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.release]

ROOT = Path(__file__).resolve().parents[2]
CLASSIFICATION = ROOT / "docs/release/RELEASE_ARTIFACT_CLASSIFICATION.md"
INVENTORY = ROOT / "docs/release/release-artifact-inventory.json"
SCOPE = ROOT / "docs/release/release-scope.yaml"


def test_release_artifact_classification_documents_safe_cleanup_policy() -> None:
    text = CLASSIFICATION.read_text(encoding="utf-8")
    assert "TEMPORARY_RUNTIME_OUTPUT" in text
    assert "var/` is treated as temporary runtime output" in text
    assert "csv.py" in text
    assert "operator review" in text.lower()


def test_release_artifact_inventory_includes_current_untracked_classes() -> None:
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert payload["branch"] == "feature/product-factory-enterprise-sdlc"
    assert payload["commit"] == "d99e60b72f14a32dc6675ccecc4ef9ffe11eb6d4"
    paths = {item["relative_path"] for item in payload["items"]}
    assert "csv.py" in paths
    assert "artifacts/novaid/final" in paths or any(path.startswith("artifacts/novaid/final/") for path in paths)
    assert any(path.startswith("var/") for path in paths)


def test_release_scope_references_current_baseline_commit() -> None:
    text = SCOPE.read_text(encoding="utf-8")
    assert "feature/product-factory-enterprise-sdlc" in text
    assert "d99e60b72f14a32dc6675ccecc4ef9ffe11eb6d4" in text
    assert "novacodepro_portal" in text
    assert "VERIFIED" in text
