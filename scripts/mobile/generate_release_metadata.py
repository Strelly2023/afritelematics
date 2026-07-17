#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from release_lineage import android_package_ids, current_android_fingerprint


ROOT = Path(__file__).resolve().parents[2]
VERSIONS = {"rider": 6, "driver": 6}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_value(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, text=True, capture_output=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=os.environ.get("NOVARIDE_RELEASE_VERSION", "2026.1.3"))
    parser.add_argument("--release-dir", type=Path)
    parser.add_argument("--publication-base", default="https://download.afritechnology.com/novaride/releases")
    args = parser.parse_args()
    release_dir = (args.release_dir or ROOT / f"apk-public/novaride/releases/{args.version}").resolve()
    release_dir.mkdir(parents=True, exist_ok=True)
    packages = android_package_ids()
    commit = os.environ.get("GITHUB_SHA") or git_value("rev-parse", "HEAD")
    branch = os.environ.get("GITHUB_REF_NAME") or git_value("branch", "--show-current")
    workflow_run = os.environ.get("GITHUB_RUN_ID") or "local"
    timestamp = datetime.now(timezone.utc).isoformat()
    builder = os.environ.get("GITHUB_ACTOR") or os.environ.get("USER") or "local-builder"

    artifacts: dict[str, dict[str, object]] = {}
    provenance_apps: dict[str, dict[str, object]] = {}
    for app in ("rider", "driver"):
        name = f"novaride-{app}-v{args.version}-public-pilot.apk"
        apk = release_dir / name
        if not apk.is_file():
            raise SystemExit(f"missing release artifact: {apk}")
        digest = sha256(apk)
        checksum = apk.with_suffix(apk.suffix + ".sha256")
        checksum.write_text(f"{digest}  {name}\n", encoding="utf-8")
        url = f"{args.publication_base.rstrip('/')}/{args.version}/{name}"
        artifacts[app] = {
            "file": name,
            "sha256": digest,
            "byte_size": apk.stat().st_size,
            "package_id": packages[app],
            "version_name": args.version,
            "version_code": VERSIONS[app],
            "signing_certificate_sha256": current_android_fingerprint(),
            "source_commit": commit,
            "publication_url": url,
            "ipa_status": "not_built_in_this_release_run",
        }
        provenance_apps[app] = {
            "version": args.version,
            "versionCode": VERSIONS[app],
            "packageId": packages[app],
            "apiHost": "https://api.afritechnology.com",
            "apkSha256": digest,
            "apkByteSize": apk.stat().st_size,
            "signingCertificateSha256": current_android_fingerprint(),
            "signingVerificationStatus": "required_before_publication",
            "publicationUrl": url,
        }

    manifest = {
        "release": args.version,
        "channel": "PUBLIC_PILOT",
        "environment": "PUBLIC_PILOT",
        "approval_status": "blocked_pending_publication_and_device_verification",
        "ga_allowed": False,
        "real_payments_enabled": False,
        "artifacts": artifacts,
    }
    (release_dir / "release-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    provenance = {
        "release": args.version,
        "generated_at": timestamp,
        "builder": builder,
        "branch": branch,
        "commit": commit,
        "workflow_run": workflow_run,
        "environment": "PUBLIC_PILOT",
        "publicationUrl": f"{args.publication_base.rstrip('/')}/{args.version}/",
        "publicationVerified": False,
        **provenance_apps,
    }
    provenance_path = ROOT / f"reports/mobile/releases/{args.version}/novaride-release-provenance.json"
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"release metadata generated for {args.version} at {commit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
