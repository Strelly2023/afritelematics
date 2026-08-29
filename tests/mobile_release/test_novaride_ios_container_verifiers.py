from __future__ import annotations

import importlib.util
import json
import plistlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ios = load("novaride_ios_test", "scripts/novaride/verify_ios_signed_artifact.py")
container = load("novaride_container_test", "scripts/novaride/verify_container_release.py")
HEAD = "a" * 40


def fake_git(command, **kwargs):
    return subprocess.CompletedProcess(command, 0, HEAD + "\n", "")


def test_ipa_without_platform_tools_is_not_verified(tmp_path, monkeypatch):
    import zipfile
    app = tmp_path / "Payload" / "Rider.app"
    app.mkdir(parents=True)
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "com.test.rider"}))
    ipa = tmp_path / "rider.ipa"
    with zipfile.ZipFile(ipa, "w") as archive:
        archive.write(app / "Info.plist", "Payload/Rider.app/Info.plist")
    monkeypatch.setattr(ios.subprocess, "run", fake_git)
    monkeypatch.setattr(ios.shutil, "which", lambda _: None)
    result = ios.build_evidence(repo=tmp_path, artifact=ipa, application="rider",
                                release_channel="production", expected_commit=HEAD)
    assert result["verification"]["status"] == "NOT_VERIFIED"


def test_ios_bundle_identifier_mismatch_is_blocked(tmp_path, monkeypatch):
    app = tmp_path / "Rider.app"
    app.mkdir()
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "wrong.id"}))
    monkeypatch.setattr(ios.subprocess, "run", fake_git)
    monkeypatch.setattr(ios.shutil, "which", lambda _: None)
    result = ios.build_evidence(repo=tmp_path, artifact=app, application="rider",
                                release_channel="production", expected_bundle_id="expected.id",
                                expected_commit=HEAD)
    assert result["verification"]["status"] == "FAIL"



def test_container_platform_mismatch_is_blocked(
    tmp_path,
    monkeypatch,
):
    image = "registry/novaride@sha256:" + "b" * 64

    def fake_run(command, **kwargs):
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(
                command,
                0,
                HEAD + "\n",
                "",
            )

        if (
            len(command) >= 3
            and command[1:3] == ["image", "inspect"]
        ):
            payload = [{
                "Architecture": "arm64",
                "Os": "linux",
                "Config": {"Labels": {}},
            }]

            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(payload),
                "",
            )

        raise AssertionError(command)

    monkeypatch.setattr(
        container.subprocess,
        "run",
        fake_run,
    )
    monkeypatch.setattr(
        container.shutil,
        "which",
        lambda _: "/usr/bin/docker",
    )

    result = container.verify(
        repo=tmp_path,
        image=image,
        expected_commit=HEAD,
        expected_digest="sha256:" + "b" * 64,
        require_cosign=False,
        expected_platform="linux/amd64",
    )

    assert result["verification"]["status"] == "FAIL"
    assert any(
        "Container platform mismatch" in error
        for error in result["verification"]["errors"]
    )


def test_container_linux_amd64_platform_is_verified(
    tmp_path,
    monkeypatch,
):
    image = "registry/novaride@sha256:" + "b" * 64

    sbom = tmp_path / "sbom.json"
    provenance = tmp_path / "provenance.json"

    sbom.write_text(
        json.dumps({"bomFormat": "CycloneDX"}),
        encoding="utf-8",
    )

    provenance.write_text(
        json.dumps({"predicateType": "test"}),
        encoding="utf-8",
    )

    def fake_run(command, **kwargs):
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(
                command,
                0,
                HEAD + "\n",
                "",
            )

        if (
            len(command) >= 3
            and command[1:3] == ["image", "inspect"]
        ):
            payload = [{
                "Architecture": "amd64",
                "Os": "linux",
                "Config": {
                    "Labels": {
                        "org.opencontainers.image.revision": HEAD,
                    }
                },
            }]

            return subprocess.CompletedProcess(
                command,
                0,
                json.dumps(payload),
                "",
            )

        raise AssertionError(command)

    monkeypatch.setattr(
        container.subprocess,
        "run",
        fake_run,
    )
    monkeypatch.setattr(
        container.shutil,
        "which",
        lambda _: "/usr/bin/docker",
    )

    result = container.verify(
        repo=tmp_path,
        image=image,
        expected_commit=HEAD,
        expected_digest="sha256:" + "b" * 64,
        require_cosign=False,
        expected_platform="linux/amd64",
        sbom=sbom,
        provenance=provenance,
    )

    assert result["verification"]["status"] == "PASS"
    assert result["verification"]["errors"] == []


def test_container_arm64_production_admission_is_blocked(
    tmp_path,
    monkeypatch,
):
    image = "registry/novaride@sha256:" + "b" * 64

    monkeypatch.setattr(
        container.subprocess,
        "run",
        fake_git,
    )
    monkeypatch.setattr(
        container.shutil,
        "which",
        lambda _: None,
    )

    result = container.verify(
        repo=tmp_path,
        image=image,
        expected_commit=HEAD,
        expected_digest="sha256:" + "b" * 64,
        require_cosign=False,
        expected_platform="linux/arm64",
    )

    assert result["verification"]["status"] == "FAIL"
    assert any(
        "production platform is not authorized" in error
        for error in result["verification"]["errors"]
    )


def test_latest_container_is_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(container.subprocess, "run", fake_git)
    result = container.verify(repo=tmp_path, image="registry/novaride:latest",
                              expected_commit=HEAD, expected_digest=None, require_cosign=False)
    assert result["verification"]["status"] == "FAIL"


def test_container_digest_mismatch_is_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(container.subprocess, "run", fake_git)
    monkeypatch.setattr(container.shutil, "which", lambda _: None)
    image = "registry/novaride@sha256:" + "b" * 64
    result = container.verify(repo=tmp_path, image=image, expected_commit=HEAD,
                              expected_digest="sha256:" + "c" * 64, require_cosign=False)
    assert result["verification"]["status"] == "FAIL"


def test_required_cosign_unavailable_is_not_verified(tmp_path, monkeypatch):
    monkeypatch.setattr(container.subprocess, "run", fake_git)
    monkeypatch.setattr(container.shutil, "which", lambda _: None)
    image = "registry/novaride@sha256:" + "b" * 64
    result = container.verify(repo=tmp_path, image=image, expected_commit=HEAD,
                              expected_digest="sha256:" + "b" * 64, require_cosign=True)
    assert result["verification"]["status"] == "NOT_VERIFIED"


def test_sbom_checksum_mismatch_is_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(container.subprocess, "run", fake_git)
    monkeypatch.setattr(container.shutil, "which", lambda _: None)
    sbom = tmp_path / "sbom.cdx.json"
    sbom.write_text(json.dumps({"bomFormat": "CycloneDX"}))
    image = "registry/novaride@sha256:" + "b" * 64
    result = container.verify(repo=tmp_path, image=image, expected_commit=HEAD,
                              expected_digest="sha256:" + "b" * 64, require_cosign=False,
                              sbom=sbom, sbom_sha256="0" * 64)
    assert result["verification"]["status"] == "FAIL"
