#!/usr/bin/env python3
"""Fail-closed validation of production deployment inputs."""

from __future__ import annotations

import argparse
import re
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COMPOSE = ROOT / "deploy/production/docker-compose.trust-node.yml"
DEFAULT_ENV = ROOT / "deploy/production/.env.production.trust-node"
SECRET_PATHS = (
    ROOT / "deploy/production/secrets/eth_private_key",
    ROOT / "deploy/production/secrets/afritech_private_key.pem",
    ROOT / "deploy/production/secrets/afritech_public_key.pem",
)
REQUIRED_ENV = (
    "AFRITECH_DOMAIN",
    "AFRITECH_TLS_EMAIL",
    "DATABASE_URL",
    "NOVATECH_CORE_DATABASE_URL",
    "AFRITECH_JWT_SECRET",
    "NOVATRUST_ED25519_PRIVATE_KEY_B64",
    "NOVAID_JWT_ISSUER",
    "NOVAID_JWT_AUDIENCE",
    "NOVAID_SIGNING_KEYS_JSON",
    "NOVAID_ACTIVE_SIGNING_KEY_ID",
    "NOVAID_TOKEN_PEPPER",
    "NOVAID_REDIS_URL",
)
REGION_ENV = (
    "AFRIRIDE_DEFAULT_REGION",
    "AFRIRIDE_REGION_CELL",
    "AFRIRIDE_DATA_RESIDENCY",
)
PLACEHOLDER = re.compile(
    r"replace-with|replace-me|your-domain\.example|trust\.afritech\.example|"
    r"YOUR_|example\.invalid",
    re.IGNORECASE,
)


class DeploymentConfigurationError(RuntimeError):
    """Raised when deployment inputs are unsafe or incomplete."""


def load_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise DeploymentConfigurationError(f"missing environment file: {path}")
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def validate_env(path: Path, *, regional: bool = False) -> dict[str, str]:
    values = load_env(path)
    required = (*REQUIRED_ENV, *(REGION_ENV if regional else ()))
    missing = [key for key in required if not values.get(key)]
    if missing:
        raise DeploymentConfigurationError(
            f"missing required environment values: {', '.join(missing)}"
        )
    placeholders = [key for key, value in values.items() if value and PLACEHOLDER.search(value)]
    if placeholders:
        raise DeploymentConfigurationError(
            f"placeholder environment values: {', '.join(sorted(placeholders))}"
        )
    return values


def validate_secret_files(paths: tuple[Path, ...] = SECRET_PATHS) -> None:
    failures: list[str] = []
    for path in paths:
        if not path.is_file():
            failures.append(f"{path}: missing regular file")
            continue
        if path.stat().st_size == 0:
            failures.append(f"{path}: empty")
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            failures.append(f"{path}: insecure mode {mode:04o}; require 0600 or stricter")
    if failures:
        raise DeploymentConfigurationError("; ".join(failures))


def validate_compose_files(paths: tuple[Path, ...]) -> None:
    failures = [str(path) for path in paths if not path.is_file()]
    if failures:
        raise DeploymentConfigurationError(
            f"missing Compose files: {', '.join(failures)}"
        )


def run_compose_validation(
    env_file: Path, compose_files: tuple[Path, ...], *, project_directory: Path
) -> None:
    command = [
        "docker",
        "compose",
        "--project-directory",
        str(project_directory),
        "--env-file",
        str(env_file),
    ]
    for path in compose_files:
        command.extend(("-f", str(path)))
    command.extend(("config", "--quiet"))
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except FileNotFoundError as exc:
        raise DeploymentConfigurationError("docker is not installed") from exc
    except subprocess.CalledProcessError as exc:
        raise DeploymentConfigurationError(
            f"Docker Compose validation failed with exit code {exc.returncode}"
        ) from exc


def validate(
    env_file: Path,
    compose_files: tuple[Path, ...],
    *,
    check_compose: bool,
) -> None:
    validate_compose_files(compose_files)
    regional = any(path.name == "docker-compose.region.yml" for path in compose_files)
    validate_env(env_file, regional=regional)
    validate_secret_files()
    if check_compose:
        run_compose_validation(
            env_file,
            compose_files,
            project_directory=DEFAULT_COMPOSE.parent,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument(
        "--compose-file",
        action="append",
        type=Path,
        dest="compose_files",
    )
    parser.add_argument("--check-compose", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compose_files = tuple(args.compose_files or (DEFAULT_COMPOSE,))
    try:
        validate(
            args.env_file.resolve(),
            tuple(path.resolve() for path in compose_files),
            check_compose=args.check_compose,
        )
    except DeploymentConfigurationError as exc:
        print(f"Production deployment preflight FAILED: {exc}", file=sys.stderr)
        return 1
    print("Production deployment preflight PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
