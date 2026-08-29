#!/usr/bin/env python3
"""Read-only verification of an immutable NovaRide container reference."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

DIGEST_REFERENCE = re.compile(r"^.+@sha256:([0-9a-f]{64})$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def verify(*, repo: Path, image: str, expected_commit: str | None,
           expected_digest: str | None, require_cosign: bool,
           expected_platform: str = "linux/amd64",
           sbom: Path | None = None, sbom_sha256: str | None = None,
           provenance: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if expected_platform != "linux/amd64":
        errors.append(
            "Container production platform is not authorized: "
            f"{expected_platform}"
        )
    match = DIGEST_REFERENCE.match(image)
    digest = f"sha256:{match.group(1)}" if match else None
    if not match:
        errors.append("Container reference is not digest-pinned")
    if expected_digest and digest != expected_digest:
        errors.append("Container digest does not match manifest")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                          text=True, capture_output=True).stdout.strip()
    if expected_commit and expected_commit != head:
        errors.append("Container evidence commit does not match current HEAD")
    if sbom:
        if not sbom.is_file():
            errors.append("SBOM is missing")
        elif sbom_sha256 and sha256_file(sbom) != sbom_sha256:
            errors.append("SBOM checksum mismatch")
    else:
        warnings.append("SBOM was not supplied")
    if provenance is not None and not provenance.is_file():
        errors.append("Provenance is missing")
    docker = shutil.which("docker")
    labels: dict[str, str] = {}
    if docker and match:
        inspected = subprocess.run([docker, "image", "inspect", image], text=True, capture_output=True)
        if inspected.returncode:
            warnings.append("Image is unavailable for local inspection")
        else:
            data = json.loads(inspected.stdout)[0]
            expected_os, expected_arch = expected_platform.split("/", 1)
            actual_os = data.get("Os")
            actual_arch = data.get("Architecture")
            if (
                actual_os != expected_os
                or actual_arch != expected_arch
            ):
                errors.append(
                    "Container platform mismatch: "
                    f"expected {expected_platform}, got "
                    f"{actual_os}/{actual_arch}"
                )
            labels = data.get("Config", {}).get("Labels") or {}
            revision = labels.get("org.opencontainers.image.revision")
            if expected_commit and revision != expected_commit:
                errors.append("OCI source revision does not match release commit")
    else:
        warnings.append("docker is unavailable")
    cosign_verified = False
    if require_cosign:
        cosign = shutil.which("cosign")
        if not cosign:
            warnings.append("cosign is unavailable")
        elif match:
            result = subprocess.run([cosign, "verify", image], text=True, capture_output=True)
            if result.returncode:
                errors.append("cosign verification failed")
            else:
                cosign_verified = True
    status = "FAIL" if errors else ("NOT_VERIFIED" if warnings or (require_cosign and not cosign_verified) else "PASS")
    return {"artifact_type": "container_image", "artifact_path_or_reference": image,
            "artifact_sha256": digest, "git_commit": expected_commit,
            "signature": {"verification_tool": "cosign" if require_cosign else "digest",
                          "verified": cosign_verified if require_cosign else bool(match)},
            "oci_labels": labels, "sbom": {"present": bool(sbom and sbom.is_file())},
            "provenance": {"present": bool(provenance and provenance.is_file())},
            "verification": {"status": status, "errors": errors, "warnings": warnings}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--expected-commit")
    parser.add_argument("--expected-digest")
    parser.add_argument(
        "--expected-platform",
        default="linux/amd64",
        choices=("linux/amd64",),
    )
    parser.add_argument("--require-cosign", action="store_true")
    parser.add_argument("--sbom", type=Path)
    parser.add_argument("--sbom-sha256")
    parser.add_argument("--provenance", type=Path)
    args = parser.parse_args()
    result = verify(repo=args.repo.resolve(), image=args.image,
                    expected_commit=args.expected_commit,
                    expected_digest=args.expected_digest,
                    require_cosign=args.require_cosign,
                    expected_platform=args.expected_platform,
                    sbom=args.sbom,
                    sbom_sha256=args.sbom_sha256,
                    provenance=args.provenance)
    print(json.dumps(result, indent=2))
    return 0 if result["verification"]["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
