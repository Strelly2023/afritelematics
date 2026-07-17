#!/usr/bin/env python3
from __future__ import annotations

import json
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from release_lineage import current_android_fingerprint


ROOT = Path(__file__).resolve().parents[2]
VERSION = os.environ.get("NOVARIDE_RELEASE_VERSION", "2026.1.4")
RELEASE_DIR = ROOT / f"apk-public/novaride/releases/{VERSION}"
REPORT = RELEASE_DIR / "release-audit-report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def env_verified(name: str) -> bool:
    return os.environ.get(name) == "1"


def main() -> int:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = RELEASE_DIR / "release-manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"missing release manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = {}
    for app in ("rider", "driver"):
        apk = RELEASE_DIR / f"novaride-{app}-v{VERSION}-public-pilot.apk"
        expected = manifest.get("artifacts", {}).get(app, {})
        actual_hash = sha256(apk) if apk.exists() else ""
        actual_size = apk.stat().st_size if apk.exists() else 0
        manifest_match = (
            apk.exists()
            and actual_hash == expected.get("sha256")
            and actual_size == expected.get("byte_size")
        )
        artifacts[app] = {
            "apk": apk.name,
            "present": apk.exists(),
            "byte_size": actual_size,
            "sha256": actual_hash,
            "sha256_file_present": apk.with_suffix(apk.suffix + ".sha256").exists(),
            "manifest_match": manifest_match,
        }

    artifact_integrity_verified = all(entry["manifest_match"] for entry in artifacts.values())
    signing_verified = env_verified("NOVARIDE_SIGNING_VERIFIED")
    device_smoke_verified = env_verified("NOVARIDE_DEVICE_SMOKE_VERIFIED")
    publication_verified = env_verified("NOVARIDE_PUBLICATION_VERIFIED")
    verified = all(
        (artifact_integrity_verified, signing_verified, device_smoke_verified, publication_verified)
    )
    data = {
        "product": "NovaRide",
        "version": VERSION,
        "build_time": datetime.now(timezone.utc).isoformat(),
        "signed": signing_verified,
        "fingerprint": current_android_fingerprint(),
        "artifact_integrity_verified": artifact_integrity_verified,
        "device_smoke_verified": device_smoke_verified,
        "verified": verified,
        "published": publication_verified,
        "ga_allowed": False,
        "real_payments_enabled": False,
        "artifacts": artifacts,
    }
    REPORT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    if not artifact_integrity_verified:
        raise SystemExit("release audit failed: APK bytes do not match release manifest")
    print(f"release audit report written: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
