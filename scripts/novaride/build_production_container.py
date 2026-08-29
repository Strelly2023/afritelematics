#!/usr/bin/env python3
"""Fail-closed NovaRide local production-container build authority.

Scope:
- validate exact authoritative build inputs,
- build the NovaRide production container for linux/amd64,
- inspect the resulting local image,
- verify OCI source revision and platform,
- execute in-image production validation,
- emit local build evidence.

Explicitly out of scope:
- registry authentication,
- image push/publication,
- cosign publication,
- Kubernetes mutation,
- Docker Compose deployment,
- database migrations,
- Terraform,
- AWS operations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

IMAGE = "novaride-api:2026.2"
PLATFORM = "linux/amd64"

DOCKERFILE = ROOT / "deploy/staging/Dockerfile.api"
LOCK = ROOT / "deploy/production/requirements-api.lock"
ENTRYPOINT = ROOT / "deploy/staging/api-entrypoint.sh"

EXPECTED_DOCKERFILE_SHA256 = (
    "b1abffd540f4bb519210ae1a3df2f164"
    "ab18f506847014f12eb0f5460baf5174"
)
EXPECTED_LOCK_SHA256 = (
    "16f64f83d5ea927b5ba14bda2aefe188"
    "89936b030c13fcd527e99966d82ee55f"
)
EXPECTED_ENTRYPOINT_SHA256 = (
    "a524d961d10c28cecd0672951cbe08a6"
    "d938a73c3164e15ac8852aa63f50717c"
)

PINNED_BASE_IMAGE = (
    "python:3.11.13-slim-bookworm@sha256:"
    "86adf8dbadc3d6e82ee5dd2c74bec2e1"
    "c2467cdad47886280501df722372d2e1"
)

EXECUTE_APPROVAL = (
    "NOVARIDE_PRODUCTION_IMAGE_BUILD_ALLOW_EXECUTE"
)
NETWORK_APPROVAL = (
    "NOVARIDE_PRODUCTION_IMAGE_BUILD_ALLOW_NETWORK"
)


class BuildAuthorityError(RuntimeError):
    """Fail-closed production container build authority error."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def require_exact_file(
    path: Path,
    expected_sha256: str,
    label: str,
) -> None:
    if not path.is_file():
        raise BuildAuthorityError(
            f"{label} is missing: {path}"
        )

    actual = sha256_file(path)

    if actual != expected_sha256:
        raise BuildAuthorityError(
            f"{label} authority drift: "
            f"expected {expected_sha256}, got {actual}"
        )


def require_authoritative_inputs() -> None:
    require_exact_file(
        DOCKERFILE,
        EXPECTED_DOCKERFILE_SHA256,
        "production Dockerfile",
    )
    require_exact_file(
        LOCK,
        EXPECTED_LOCK_SHA256,
        "production dependency lock",
    )
    require_exact_file(
        ENTRYPOINT,
        EXPECTED_ENTRYPOINT_SHA256,
        "production entrypoint",
    )

    dockerfile_text = DOCKERFILE.read_text(
        encoding="utf-8"
    )

    required_fragments = (
        PINNED_BASE_IMAGE,
        (
            "COPY deploy/production/requirements-api.lock "
            "/build/requirements-api.lock"
        ),
        "--constraint /build/requirements-api.lock",
        (
            "python -m "
            "afritech.tools.production_image_validation"
        ),
        (
            'ENTRYPOINT '
            '["afritech-api-entrypoint"]'
        ),
    )

    missing = [
        fragment
        for fragment in required_fragments
        if fragment not in dockerfile_text
    ]

    if missing:
        raise BuildAuthorityError(
            "production Dockerfile contract incomplete: "
            + repr(missing)
        )


def require_approval(name: str) -> None:
    if os.environ.get(name) != "YES":
        raise BuildAuthorityError(
            f"explicit approval required: {name}=YES"
        )


def require_docker() -> str:
    docker = shutil.which("docker")

    if not docker:
        raise BuildAuthorityError(
            "docker executable is unavailable"
        )

    return docker


def require_local_base_image(
    *,
    docker: str,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            docker,
            "image",
            "inspect",
            "--platform",
            PLATFORM,
            PINNED_BASE_IMAGE,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        raise BuildAuthorityError(
            "exact pinned linux/amd64 base image "
            "is not available locally"
        )

    payload = json.loads(completed.stdout)

    if not isinstance(payload, list) or len(payload) != 1:
        raise BuildAuthorityError(
            "unexpected base-image inspection payload"
        )

    image = payload[0]

    if (
        image.get("Os") != "linux"
        or image.get("Architecture") != "amd64"
    ):
        raise BuildAuthorityError(
            "local pinned base-image platform mismatch"
        )

    return {
        "id": image.get("Id"),
        "os": image.get("Os"),
        "architecture": image.get("Architecture"),
        "repo_digests": image.get("RepoDigests") or [],
    }


def build_command(
    *,
    docker: str,
    commit: str,
    branch: str,
    timestamp: str,
) -> list[str]:
    return [
        docker,
        "build",
        "--platform",
        PLATFORM,
        "--pull=false",
        "--no-cache",
        "--file",
        str(DOCKERFILE),
        "--tag",
        IMAGE,
        "--build-arg",
        f"BUILD_COMMIT={commit}",
        "--build-arg",
        f"BUILD_BRANCH={branch}",
        "--build-arg",
        f"BUILD_TIMESTAMP={timestamp}",
        str(ROOT),
    ]


def inspect_built_image(
    *,
    docker: str,
    expected_commit: str,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            docker,
            "image",
            "inspect",
            "--platform",
            PLATFORM,
            IMAGE,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        raise BuildAuthorityError(
            "built NovaRide image is unavailable "
            "for local inspection"
        )

    payload = json.loads(completed.stdout)

    if not isinstance(payload, list) or len(payload) != 1:
        raise BuildAuthorityError(
            "unexpected built-image inspection payload"
        )

    image = payload[0]

    actual_os = image.get("Os")
    actual_arch = image.get("Architecture")

    if actual_os != "linux" or actual_arch != "amd64":
        raise BuildAuthorityError(
            "built image platform mismatch: "
            f"{actual_os}/{actual_arch}"
        )

    labels = (
        image.get("Config", {}).get("Labels")
        or {}
    )

    revision = labels.get(
        "org.opencontainers.image.revision"
    )

    if revision != expected_commit:
        raise BuildAuthorityError(
            "built image OCI revision mismatch: "
            f"expected {expected_commit}, got {revision}"
        )

    image_id = image.get("Id")

    if (
        not isinstance(image_id, str)
        or not image_id.startswith("sha256:")
    ):
        raise BuildAuthorityError(
            "built image lacks local immutable image ID"
        )

    return {
        "id": image_id,
        "os": actual_os,
        "architecture": actual_arch,
        "labels": labels,
        "repo_digests": image.get("RepoDigests") or [],
    }


def runtime_validation_command(
    *,
    docker: str,
    output_dir: Path,
) -> list[str]:
    mount = (
        f"type=bind,src={output_dir.resolve()},"
        "dst=/evidence"
    )

    return [
        docker,
        "run",
        "--rm",
        "--network",
        "none",
        "--user",
        "0:0",
        "--mount",
        mount,
        "--entrypoint",
        "python",
        IMAGE,
        "-m",
        "afritech.tools.production_image_validation",
        "--output",
        "/evidence/runtime-validation.json",
        "--sbom",
        "/evidence/sbom.json",
    ]


def git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        raise BuildAuthorityError(
            "git authority query failed: "
            + " ".join(args)
        )

    return completed.stdout.strip()


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def execute(
    *,
    output_dir: Path,
    timestamp: str,
) -> dict[str, Any]:
    require_authoritative_inputs()
    require_approval(EXECUTE_APPROVAL)
    require_approval(NETWORK_APPROVAL)

    docker = require_docker()

    commit = git_value("rev-parse", "HEAD")
    branch = git_value(
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    )

    base = require_local_base_image(
        docker=docker,
    )

    command = build_command(
        docker=docker,
        commit=commit,
        branch=branch,
        timestamp=timestamp,
    )

    built = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        check=False,
    )

    if built.returncode != 0:
        raise BuildAuthorityError(
            "NovaRide linux/amd64 production "
            "container build failed"
        )

    image = inspect_built_image(
        docker=docker,
        expected_commit=commit,
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    validation = subprocess.run(
        runtime_validation_command(
            docker=docker,
            output_dir=output_dir,
        ),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    if validation.returncode != 0:
        raise BuildAuthorityError(
            "in-image production validation failed: "
            + validation.stderr.strip()
        )

    validation_path = (
        output_dir / "runtime-validation.json"
    )
    sbom_path = output_dir / "sbom.json"

    if not validation_path.is_file():
        raise BuildAuthorityError(
            "runtime validation evidence missing"
        )

    if not sbom_path.is_file():
        raise BuildAuthorityError(
            "SBOM evidence missing"
        )

    runtime_payload = json.loads(
        validation_path.read_text(
            encoding="utf-8"
        )
    )

    if runtime_payload.get("status") != "PASS":
        raise BuildAuthorityError(
            "runtime validation did not report PASS"
        )

    evidence = {
        "schema_version": 1,
        "authority": (
            "novaride_local_production_container_build"
        ),
        "platform": PLATFORM,
        "image_tag": IMAGE,
        "local_image_id": image["id"],
        "registry_digest": None,
        "registry_publication": False,
        "kubernetes_digest_binding": False,
        "repository": {
            "commit": commit,
            "branch": branch,
        },
        "inputs": {
            "dockerfile_sha256": sha256_file(
                DOCKERFILE
            ),
            "dependency_lock_sha256": sha256_file(
                LOCK
            ),
            "entrypoint_sha256": sha256_file(
                ENTRYPOINT
            ),
            "pinned_base_image": PINNED_BASE_IMAGE,
            "local_base_image": base,
        },
        "image": image,
        "runtime_validation": runtime_payload,
        "runtime_validation_sha256": sha256_file(
            validation_path
        ),
        "sbom_sha256": sha256_file(
            sbom_path
        ),
        "explicit_non_claims": {
            "registry_digest_proven": False,
            "registry_publication_proven": False,
            "cosign_proven": False,
            "provenance_proven": False,
            "kubernetes_digest_binding_proven": False,
        },
    }

    write_json(
        output_dir / "build-evidence.json",
        evidence,
    )

    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--execute",
        action="store_true",
    )
    parser.add_argument(
        "--print-pinned-base-image",
        action="store_true",
    )
    parser.add_argument(
        "--timestamp",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=(
            ROOT
            / "artifacts"
            / "novaride"
            / "container-build"
        ),
    )

    args = parser.parse_args()

    require_authoritative_inputs()

    if args.print_pinned_base_image:
        print(PINNED_BASE_IMAGE)
        return 0

    if not args.execute:
        print(
            json.dumps(
                {
                    "authority": (
                        "novaride_local_"
                        "production_container_build"
                    ),
                    "status": "VALIDATED_NOT_EXECUTED",
                    "platform": PLATFORM,
                    "image_tag": IMAGE,
                    "dockerfile_sha256": (
                        sha256_file(DOCKERFILE)
                    ),
                    "dependency_lock_sha256": (
                        sha256_file(LOCK)
                    ),
                    "entrypoint_sha256": (
                        sha256_file(ENTRYPOINT)
                    ),
                    "execute_approval": (
                        EXECUTE_APPROVAL
                    ),
                    "network_approval": (
                        NETWORK_APPROVAL
                    ),
                    "registry_publication": False,
                    "kubernetes_mutation": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    timestamp = args.timestamp

    if not timestamp:
        raise BuildAuthorityError(
            "--timestamp is required for execution"
        )

    evidence = execute(
        output_dir=args.output_dir,
        timestamp=timestamp,
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "local_image_id": (
                    evidence["local_image_id"]
                ),
                "registry_digest": None,
                "registry_publication": False,
                "kubernetes_digest_binding": False,
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
