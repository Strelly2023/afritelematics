#!/usr/bin/env python3
"""Read-only, fail-closed verifier for NovaRide IPA and .app artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, text=True,
                          capture_output=True).stdout.strip()


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True)


def build_evidence(*, repo: Path, artifact: Path, application: str,
                   release_channel: str, expected_bundle_id: str | None = None,
                   expected_commit: str | None = None,
                   artifact_matches_manifest: bool = False,
                   immutable_reference: bool = False, **_: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    head = _git(repo, "rev-parse", "HEAD")
    commit = expected_commit or head
    digest = _sha256(artifact) if artifact.is_file() else None
    temporary: tempfile.TemporaryDirectory[str] | None = None
    app = artifact
    try:
        if artifact.suffix.lower() == ".ipa":
            temporary = tempfile.TemporaryDirectory(prefix="novaride-ios-verify-")
            with zipfile.ZipFile(artifact) as archive:
                unsafe = [n for n in archive.namelist() if Path(n).is_absolute() or ".." in Path(n).parts]
                if unsafe:
                    raise ValueError("IPA contains unsafe archive paths")
                archive.extractall(temporary.name)
            apps = list((Path(temporary.name) / "Payload").glob("*.app"))
            if len(apps) != 1:
                errors.append("IPA must contain exactly one Payload/*.app")
            else:
                app = apps[0]
        elif artifact.suffix.lower() != ".app" and not artifact.name.endswith(".app"):
            errors.append("iOS artifact must be an IPA or .app")

        info: dict[str, Any] = {}
        info_path = app / "Info.plist"
        if info_path.is_file():
            with info_path.open("rb") as stream:
                info = plistlib.load(stream)
        else:
            errors.append("Info.plist is missing")
        bundle_id = info.get("CFBundleIdentifier")
        if expected_bundle_id and bundle_id != expected_bundle_id:
            errors.append(f"Bundle identifier {bundle_id!r} does not match {expected_bundle_id!r}")

        codesign = shutil.which("codesign")
        security = shutil.which("security")
        verified = False
        authority = None
        profile_uuid = None
        profile_expiry = None
        if not codesign or not security:
            warnings.append("codesign/security verification tools are unavailable")
        elif not errors:
            check = _run([codesign, "--verify", "--deep", "--strict", "--verbose=4", str(app)])
            details = _run([codesign, "-dv", "--verbose=4", str(app)])
            if check.returncode:
                errors.append("codesign verification failed")
            else:
                verified = True
            detail_text = details.stdout + details.stderr
            for line in detail_text.splitlines():
                if line.startswith("Authority="):
                    authority = line.partition("=")[2].strip()
                    break
            provision = app / "embedded.mobileprovision"
            if not provision.is_file():
                errors.append("embedded provisioning profile is missing")
            else:
                decoded = _run([security, "cms", "-D", "-i", str(provision)])
                if decoded.returncode:
                    errors.append("provisioning profile could not be decoded")
                else:
                    profile = plistlib.loads(decoded.stdout.encode())
                    profile_uuid = profile.get("UUID")
                    expiry = profile.get("ExpirationDate")
                    if expiry:
                        profile_expiry = expiry.isoformat()
                        now = datetime.now(timezone.utc)
                        normalized = expiry.replace(tzinfo=timezone.utc) if expiry.tzinfo is None else expiry
                        if normalized <= now:
                            errors.append("provisioning profile is expired")
                    entitlements = profile.get("Entitlements", {})
                    app_identifier = entitlements.get("application-identifier", "")
                    if bundle_id and not app_identifier.endswith(f".{bundle_id}"):
                        errors.append("application identifier entitlement does not match bundle identifier")
            if release_channel in {"production", "ga"} and authority and (
                "development" in authority.lower() or "adhoc" in authority.lower()
            ):
                errors.append("development/ad-hoc signing is forbidden for production")

        if commit != head:
            errors.append(f"Artifact commit {commit} does not match current HEAD {head}")
        status = "FAIL" if errors else ("PASS" if verified else "NOT_VERIFIED")
        return {
            "schema_version": "1.0.0", "product": "NovaRide",
            "artifact_type": "ios_ipa" if artifact.suffix.lower() == ".ipa" else "ios_app",
            "application": application, "release_channel": release_channel,
            "git_commit": commit, "artifact_path_or_reference": str(artifact),
            "artifact_sha256": digest,
            "signature": {"verification_tool": "codesign/security" if codesign and security else None,
                          "verified": verified, "verified_at_utc": datetime.now(timezone.utc).isoformat(),
                          "certificate_subject": authority, "provisioning_profile_uuid": profile_uuid,
                          "provisioning_profile_expiry": profile_expiry},
            "release_candidate": {"commit_matches_current_head": commit == head,
                                  "artifact_matches_manifest": artifact_matches_manifest,
                                  "immutable_reference": immutable_reference},
            "verification": {"status": status, "errors": errors, "warnings": warnings},
        }
    finally:
        if temporary:
            temporary.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--application", required=True, choices=("rider", "driver"))
    parser.add_argument("--release-channel", default="production")
    parser.add_argument("--expected-bundle-id")
    args = parser.parse_args()
    evidence = build_evidence(repo=args.repo.resolve(), artifact=args.artifact.resolve(),
                              application=args.application, release_channel=args.release_channel,
                              expected_bundle_id=args.expected_bundle_id)
    print(json.dumps(evidence, indent=2, default=str))
    return 0 if evidence["verification"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
