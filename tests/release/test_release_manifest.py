from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = [pytest.mark.release]

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "artifacts/ga-readiness/release/manifests/release-manifest.json"


def test_release_manifest_records_unsigned_baseline_state() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    head = __import__("subprocess").run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()

    assert manifest["schema_version"] == 1
    assert manifest["release_candidate"] == "novatech-2026.1.0-rc.1"
    assert manifest["status"] == "BASELINE_IN_PROGRESS"
    assert manifest["approval_status"] == "UNSIGNED"
    assert manifest["signature_status"] == "EXTERNALLY_BLOCKED"
    assert manifest["commit_sha"] == head
    assert manifest["remote_commit_sha"] == head
    assert manifest["checksum_manifest"] == "artifacts/ga-readiness/release/checksums/SHA256SUMS"
    assert manifest["reproducibility_report"] == "artifacts/ga-readiness/release/reproducibility/report.json"
    assert manifest["products"] == ["NovaID", "NovaPay", "NovaRide", "NovaCodePro"]
    assert "production signing material unavailable" in manifest["known_blockers"]
