from __future__ import annotations

from pathlib import Path

from scripts.release.generate_checksum_manifest import sha256 as checksum_sha256
from scripts.release.verify_checksum_manifest import verify


def test_checksum_manifest_verifier_accepts_matching_files(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("release evidence", encoding="utf-8")
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{checksum_sha256(artifact)}  artifact.txt\n", encoding="utf-8")

    report = verify(manifest, base_dir=tmp_path)

    assert report["status"] == "PASS"
    assert report["missing"] == []
    assert report["mismatched"] == []
    assert report["file_count"] == 1


def test_checksum_manifest_verifier_rejects_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("release evidence", encoding="utf-8")
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text(f"{'0' * 64}  artifact.txt\n", encoding="utf-8")

    report = verify(manifest, base_dir=tmp_path)

    assert report["status"] == "FAIL"
    assert report["mismatched"]
