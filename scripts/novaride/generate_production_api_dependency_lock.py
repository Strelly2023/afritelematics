#!/usr/bin/env python3
"""Fail-closed production API dependency-lock generator.

This tool defines the governed resolution boundary for the production API
dependency lock. It intentionally requires:

* the repository-pinned Python image,
* an explicit Linux target platform,
* an available Docker daemon,
* explicit network-resolution authorization, and
* explicit replacement authorization before the authoritative lock changes.

The host Python environment is never dependency-resolution authority.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib


ROOT = Path(__file__).resolve().parents[2]

PYPROJECT = ROOT / "pyproject.toml"
REQUIREMENTS = ROOT / "requirements.txt"
DOCKERFILE = ROOT / "deploy/staging/Dockerfile.api"
LOCK = ROOT / "deploy/production/requirements-api.lock"

NETWORK_APPROVAL = "NOVARIDE_DEPENDENCY_LOCK_ALLOW_NETWORK"
REPLACE_APPROVAL = "NOVARIDE_DEPENDENCY_LOCK_ALLOW_REPLACE"

SUPPORTED_PLATFORMS = {
    "linux/amd64",
    "linux/arm64",
}

PIN_RE = re.compile(
    r"^[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_.,-]+\])?==[^\s;]+$"
)


class LockGenerationError(RuntimeError):
    """Fail-closed lock-generation error."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pinned_python_image() -> str:
    if not DOCKERFILE.is_file():
        raise LockGenerationError("production Dockerfile is missing")

    for line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("ARG PYTHON_IMAGE="):
            value = line.split("=", 1)[1].strip()
            if (
                not value
                or "@sha256:" not in value
                or value.endswith("@sha256:")
            ):
                raise LockGenerationError(
                    "production Python image is not digest pinned"
                )
            return value

    raise LockGenerationError(
        "production Dockerfile does not declare PYTHON_IMAGE"
    )


def validate_platform(platform: str) -> None:
    if platform not in SUPPORTED_PLATFORMS:
        allowed = ", ".join(sorted(SUPPORTED_PLATFORMS))
        raise LockGenerationError(
            f"unsupported production platform {platform!r}; "
            f"allowed: {allowed}"
        )


def require_source_contract() -> None:
    for path in (PYPROJECT, REQUIREMENTS, DOCKERFILE):
        if not path.is_file():
            raise LockGenerationError(
                f"required dependency authority missing: "
                f"{path.relative_to(ROOT)}"
            )

    pyproject = PYPROJECT.read_text(encoding="utf-8")
    requirements = REQUIREMENTS.read_text(encoding="utf-8")

    declaration = "confluent-kafka[oauthbearer-aws]==2.15.0"

    if declaration not in pyproject:
        raise LockGenerationError(
            "pyproject AWS MSK IAM dependency declaration missing"
        )

    if declaration not in requirements.splitlines():
        raise LockGenerationError(
            "requirements AWS MSK IAM dependency declaration missing"
        )


def require_docker() -> None:
    docker = shutil.which("docker")
    if docker is None:
        raise LockGenerationError("docker command is unavailable")

    probe = subprocess.run(
        [docker, "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode != 0:
        raise LockGenerationError("docker daemon is unavailable")


def require_pinned_image_local(
    *,
    image: str,
    platform: str,
) -> None:
    """Require the exact pinned image/platform to exist locally.

    This check is intentionally local-only. The generator must never
    allow ``docker run`` to become an implicit image-pull mechanism.
    """

    docker = shutil.which("docker")

    if docker is None:
        raise LockGenerationError(
            "docker command is unavailable"
        )

    probe = subprocess.run(
        [
            docker,
            "image",
            "inspect",
            "--platform",
            platform,
            image,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    if probe.returncode != 0:
        raise LockGenerationError(
            "pinned production image/platform is not local: "
            f"{platform} {image}"
        )


def require_network_approval() -> None:
    if os.environ.get(NETWORK_APPROVAL) != "YES":
        raise LockGenerationError(
            f"network dependency resolution requires "
            f"{NETWORK_APPROVAL}=YES"
        )


def normalize_package_name(name: str) -> str:
    return name.strip().lower().replace("_", "-").replace(".", "-")


def project_name() -> str:
    try:
        payload = tomllib.loads(
            PYPROJECT.read_text(encoding="utf-8")
        )
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise LockGenerationError(
            "production project metadata is unreadable"
        ) from exc

    project = payload.get("project")

    if not isinstance(project, dict):
        raise LockGenerationError(
            "production project metadata is missing [project]"
        )

    name = project.get("name")

    if not isinstance(name, str) or not name.strip():
        raise LockGenerationError(
            "production project name is missing"
        )

    return normalize_package_name(name)


def validate_lock(path: Path) -> list[str]:
    if not path.is_file():
        raise LockGenerationError("candidate lock was not generated")

    active: list[str] = []

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        if not PIN_RE.fullmatch(line):
            raise LockGenerationError(
                f"candidate contains non-exact dependency line: {line!r}"
            )

        active.append(line)

    if not active:
        raise LockGenerationError("candidate lock is empty")

    names = {
        line.split("==", 1)[0]
        .split("[", 1)[0]
        .lower()
        .replace("_", "-")
        for line in active
    }

    local_project = project_name()
    if local_project in names:
        raise LockGenerationError(
            "local project package is forbidden in production lock: "
            f"{local_project}"
        )

    required = {
        "confluent-kafka",
        "boto3",
        "botocore",
        "s3transfer",
        "jmespath",
        "uvicorn",
    }

    missing = sorted(required - names)

    if missing:
        raise LockGenerationError(
            "candidate lock missing AWS OAuth dependencies: "
            + ", ".join(missing)
        )

    return active


def docker_resolution_command(
    *,
    platform: str,
    image: str,
    output_dir: Path,
) -> list[str]:
    # Resolution occurs in the pinned Linux Python image. The repository is
    # mounted read-only; only /output is writable.
    resolver = r"""
set -eu

python - <<'PROJECT_REQUIREMENTS'
from pathlib import Path
import tomllib

payload = tomllib.loads(
    Path("/repo/pyproject.toml").read_text(encoding="utf-8")
)

project = payload.get("project")

if not isinstance(project, dict):
    raise SystemExit(
        "production project metadata is missing [project]"
    )

dependencies = project.get("dependencies")

if not isinstance(dependencies, list) or not dependencies:
    raise SystemExit(
        "production project dependencies are missing"
    )

Path("/tmp/project-requirements.txt").write_text(
    "\n".join(str(item) for item in dependencies) + "\n",
    encoding="utf-8",
)
PROJECT_REQUIREMENTS

python -m pip install \
  --disable-pip-version-check \
  --prefer-binary \
  --constraint /repo/deploy/production/requirements-api.lock \
  --target /tmp/resolved \
  --requirement /tmp/project-requirements.txt \
  uvicorn

python - <<'INNER'
from importlib import metadata
from pathlib import Path
import tomllib

out = Path("/output/requirements-api.lock")

project = tomllib.loads(
    Path("/repo/pyproject.toml").read_text(encoding="utf-8")
)
local_project = (
    project["project"]["name"]
    .strip()
    .lower()
    .replace("_", "-")
    .replace(".", "-")
)

pairs = set()

for dist in metadata.distributions(path=["/tmp/resolved"]):
    name = dist.metadata.get("Name")
    version = dist.version

    if name and version:
        normalized = name.replace("_", "-")
        canonical = normalized.lower().replace(".", "-")

        if canonical == local_project:
            continue

        pairs.add((canonical, normalized, version))

lines = [
    f"{display}=={version}"
    for _, display, version in sorted(pairs)
]

out.write_text(
    "# Generated by "
    "scripts/novaride/generate_production_api_dependency_lock.py\n"
    f"# Platform: {""" + repr(platform) + r"""}\n"
    + "\n".join(lines)
    + "\n",
    encoding="utf-8",
)
INNER
"""

    return [
        "docker",
        "run",
        "--rm",
        "--pull=never",
        "--platform",
        platform,
        "--network",
        "bridge",
        "--mount",
        f"type=bind,src={ROOT},dst=/repo,readonly",
        "--mount",
        f"type=bind,src={output_dir},dst=/output",
        "--workdir",
        "/repo",
        image,
        "/bin/sh",
        "-c",
        resolver,
    ]


def generate(platform: str) -> Path:
    validate_platform(platform)
    require_source_contract()

    image = pinned_python_image()

    require_docker()
    require_pinned_image_local(
        image=image,
        platform=platform,
    )
    require_network_approval()

    with tempfile.TemporaryDirectory(
        prefix="novaride-production-lock-"
    ) as temp:
        temp_path = Path(temp)

        command = docker_resolution_command(
            platform=platform,
            image=image,
            output_dir=temp_path,
        )

        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
        )

        if completed.returncode != 0:
            raise LockGenerationError(
                "target-container dependency resolution failed"
            )

        candidate = temp_path / "requirements-api.lock"
        validate_lock(candidate)

        durable_candidate = (
            ROOT
            / "deploy/production"
            / f"requirements-api.{platform.replace('/', '-')}.candidate.lock"
        )

        if durable_candidate.exists():
            raise LockGenerationError(
                "durable dependency candidate already exists: "
                f"{durable_candidate.relative_to(ROOT)}"
            )

        durable_candidate.write_bytes(candidate.read_bytes())

        return durable_candidate


def replace(candidate: Path) -> None:
    validate_lock(candidate)

    if os.environ.get(REPLACE_APPROVAL) != "YES":
        raise LockGenerationError(
            f"authoritative lock replacement requires "
            f"{REPLACE_APPROVAL}=YES"
        )

    target_dir = LOCK.parent

    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=target_dir,
        prefix=".requirements-api.lock.",
        delete=False,
    ) as handle:
        temp_target = Path(handle.name)
        handle.write(candidate.read_bytes())
        handle.flush()
        os.fsync(handle.fileno())

    try:
        validate_lock(temp_target)
        os.replace(temp_target, LOCK)
    finally:
        if temp_target.exists():
            temp_target.unlink()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument(
        "--platform",
        required=True,
        choices=sorted(SUPPORTED_PLATFORMS),
    )
    result.add_argument(
        "--replace",
        action="store_true",
        help="replace authoritative lock after successful generation",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)

    try:
        candidate = generate(args.platform)

        print(f"CANDIDATE={candidate.relative_to(ROOT)}")
        print(f"CANDIDATE_SHA256={sha256(candidate)}")
        print(f"PLATFORM={args.platform}")
        print(f"PYTHON_IMAGE={pinned_python_image()}")

        if args.replace:
            replace(candidate)
            print(f"AUTHORITATIVE_LOCK={LOCK.relative_to(ROOT)}")
            print(f"AUTHORITATIVE_SHA256={sha256(LOCK)}")
            print("LOCK_REPLACED=YES")
        else:
            print("LOCK_REPLACED=NO")

        return 0

    except LockGenerationError as exc:
        print(f"LOCK_GENERATION_DENIED={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
