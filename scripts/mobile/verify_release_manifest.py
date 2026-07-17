#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from release_lineage import android_package_ids, current_android_fingerprint


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VERSION = os.environ.get("NOVARIDE_RELEASE_VERSION", "2026.1.3")
PLACEHOLDERS = {"pending", "pending-release-build", "pending-apksigner", "unknown"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_android_tool(name: str) -> str | None:
    direct = shutil.which(name)
    if direct:
        return direct
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk:
        return None
    candidates = sorted((Path(sdk) / "build-tools").glob(f"*/{name}"), reverse=True)
    return str(candidates[0]) if candidates else None


def apk_badging(apk: Path, *, required: bool) -> dict[str, str]:
    aapt = find_android_tool("aapt") or find_android_tool("aapt2")
    if not aapt:
        if required:
            raise SystemExit("aapt/aapt2 is required for strict APK metadata validation")
        return {}
    output = subprocess.run(
        [aapt, "dump", "badging", str(apk)], check=True, text=True, capture_output=True
    ).stdout
    match = re.search(
        r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", output
    )
    if not match:
        raise SystemExit(f"could not parse APK package metadata: {apk}")
    sdk_match = re.search(r"sdkVersion:'([^']+)'", output)
    target_match = re.search(r"targetSdkVersion:'([^']+)'", output)
    return {
        "package_id": match.group(1),
        "version_code": match.group(2),
        "version_name": match.group(3),
        "minimum_sdk": sdk_match.group(1) if sdk_match else "",
        "target_sdk": target_match.group(1) if target_match else "",
    }


def signing_fingerprint(apk: Path, *, required: bool) -> str:
    apksigner = find_android_tool("apksigner")
    if not apksigner:
        if required:
            raise SystemExit("apksigner is required for strict signing validation")
        return ""
    output = subprocess.run(
        [apksigner, "verify", "--verbose", "--print-certs", str(apk)],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    match = re.search(r"certificate SHA-256 digest:\s*([0-9a-fA-F: ]+)", output)
    if not match:
        raise SystemExit(f"could not read APK signing certificate: {apk}")
    return re.sub(r"[^0-9a-fA-F]", "", match.group(1)).lower()


def reject_placeholder(value: object, label: str) -> None:
    if not value or str(value).strip().lower() in PLACEHOLDERS:
        raise SystemExit(f"release metadata contains placeholder: {label}")


def verify(version: str, release_dir: Path, require_apk_tools: bool) -> None:
    manifest_path = release_dir / "release-manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"missing release manifest: {manifest_path}")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("release") != version:
        raise SystemExit(f"release manifest version mismatch: {data.get('release')}")
    if data.get("ga_allowed") is not False or data.get("real_payments_enabled") is not False:
        raise SystemExit("release must keep ga_allowed=false and real_payments_enabled=false")

    packages = android_package_ids()
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict):
        raise SystemExit("release manifest missing artifacts")
    for app in ("rider", "driver"):
        entry = artifacts.get(app)
        if not isinstance(entry, dict):
            raise SystemExit(f"release manifest missing artifact: {app}")
        for key in ("file", "sha256", "byte_size", "package_id", "version_name", "version_code"):
            reject_placeholder(entry.get(key), f"{app}.{key}")
        apk = release_dir / str(entry["file"])
        if not apk.is_file():
            raise SystemExit(f"release artifact is missing: {apk}")
        actual_size = apk.stat().st_size
        actual_hash = sha256(apk)
        if actual_size != int(entry["byte_size"]):
            raise SystemExit(f"{app} byte-size mismatch: {actual_size} != {entry['byte_size']}")
        if actual_hash != str(entry["sha256"]).lower():
            raise SystemExit(f"{app} SHA-256 mismatch: {actual_hash} != {entry['sha256']}")
        if entry["package_id"] != packages[app]:
            raise SystemExit(f"{app} package ID is not the registered NovaRide package")

        badging = apk_badging(apk, required=require_apk_tools)
        if badging:
            expected = {
                "package_id": str(entry["package_id"]),
                "version_name": str(entry["version_name"]),
                "version_code": str(entry["version_code"]),
            }
            for key, value in expected.items():
                if badging[key] != value:
                    raise SystemExit(f"{app} APK {key} mismatch: {badging[key]} != {value}")

        fingerprint = signing_fingerprint(apk, required=require_apk_tools)
        if fingerprint and fingerprint != current_android_fingerprint():
            raise SystemExit(f"{app} signing certificate does not match active release lineage")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--release-dir", type=Path)
    parser.add_argument("--require-apk-tools", action="store_true")
    args = parser.parse_args()
    release_dir = args.release_dir or ROOT / f"apk-public/novaride/releases/{args.version}"
    verify(args.version, release_dir.resolve(), args.require_apk_tools)
    print("release manifest and APK artifacts verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
