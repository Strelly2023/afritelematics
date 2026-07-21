from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.release.generate_sbom_bundle import generate
from scripts.release.verify_sbom_bundle import verify_bundle


pytestmark = [pytest.mark.release]


def test_generate_sbom_bundle_and_verify(tmp_path: Path) -> None:
    output_dir = tmp_path / "sbom"
    report = generate(output_dir)

    assert report["status"] == "PASS"
    assert any(item["component_id"] == "novacodepro_portal" for item in report["generated"])
    assert (output_dir / "novacodepro_portal.cdx.json").exists()
    assert (output_dir / "release-aggregate.cdx.json").exists()

    verified = verify_bundle(output_dir)
    assert verified["status"] == "PASS"
    assert verified["files"]


def test_verify_sbom_bundle_reports_missing_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "sbom"
    output_dir.mkdir()
    (output_dir / "broken.cdx.json").write_text(json.dumps({"bomFormat": "CycloneDX"}), encoding="utf-8")

    verified = verify_bundle(output_dir)

    assert verified["status"] == "FAIL"
    assert any(issue.startswith("metadata_missing:") for issue in verified["issues"])
