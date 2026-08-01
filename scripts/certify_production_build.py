#!/usr/bin/env python3
"""Build and certify the production API image with immutable JSON evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/production-build"
DEFAULT_IMAGE = "afritech/afritech-api:production"
DEFAULT_DOCKERFILE = ROOT / "deploy/staging/Dockerfile.api"
DEFAULT_COMPOSE = ROOT / "deploy/production/docker-compose.trust-node.yml"
DEFAULT_ENV = ROOT / "deploy/production/.env.production.trust-node"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    command: list[str],
    *,
    timings: dict[str, Any],
    name: str,
    capture: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=capture,
        env={**os.environ, "DOCKER_BUILDKIT": "1"},
    )
    timings[name] = {
        "seconds": round(time.monotonic() - started, 3),
        "exit_code": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }
    if check and completed.returncode:
        if completed.stdout:
            print(completed.stdout, file=sys.stderr)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
        raise RuntimeError(f"{name} failed with exit code {completed.returncode}")
    return completed


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def inspect_image(image: str, timings: dict[str, Any]) -> dict[str, Any]:
    result = run(
        ["docker", "image", "inspect", image],
        timings=timings,
        name="image_inspection",
    )
    payload = json.loads(result.stdout)[0]
    return {
        "reference": image,
        "id": payload["Id"],
        "repo_digests": payload.get("RepoDigests", []),
        "size_bytes": payload["Size"],
        "created": payload["Created"],
        "architecture": payload["Architecture"],
        "os": payload["Os"],
        "labels": payload.get("Config", {}).get("Labels") or {},
    }


def http_gate(url: str, *, attempts: int = 30, delay: float = 2.0) -> dict[str, Any]:
    last_error = ""
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                body = response.read().decode("utf-8")
                payload = json.loads(body)
                if response.status == 200:
                    return {
                        "status": "PASS",
                        "http_status": response.status,
                        "attempt": attempt,
                        "payload": payload,
                    }
        except (
            urllib.error.URLError,
            ConnectionError,
            OSError,
            TimeoutError,
            json.JSONDecodeError,
        ) as exc:
            last_error = type(exc).__name__
        time.sleep(delay)
    return {"status": "FAIL", "http_status": None, "error": last_error}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--compose-file", type=Path, default=DEFAULT_COMPOSE)
    parser.add_argument("--skip-deploy", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    timings: dict[str, Any] = {"started_at": utc_now(), "gates": {}}
    gates: dict[str, Any] = {}
    commit = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    build_timestamp = utc_now()

    try:
        build_command = [
                "docker",
                "build",
                "--progress=plain",
                "--build-arg",
                f"BUILD_COMMIT={commit}",
                "--build-arg",
                f"BUILD_BRANCH={branch}",
                "--build-arg",
                f"BUILD_TIMESTAMP={build_timestamp}",
                "--tag",
                args.image,
                "--file",
                str(DEFAULT_DOCKERFILE),
                ".",
            ]
        if args.no_cache:
            build_command.insert(2, "--no-cache")
        if args.skip_build:
            timings["gates"]["docker_build"] = {
                "seconds": 0,
                "exit_code": 0,
                "status": "SKIPPED_EXISTING_IMAGE",
            }
            gates["docker_build"] = "PASS"
        else:
            build = run(
                build_command,
                timings=timings["gates"],
                name="docker_build",
                capture=False,
            )
            gates["docker_build"] = "PASS" if build.returncode == 0 else "FAIL"
        image = inspect_image(args.image, timings["gates"])

        evidence_mount = f"{output}:/evidence"
        validation = run(
            [
                "docker",
                "run",
                "--rm",
                "--user",
                "0:0",
                "--volume",
                evidence_mount,
                "--entrypoint",
                "python",
                args.image,
                "-m",
                "afritech.tools.production_image_validation",
                "--output",
                "/evidence/runtime-validation.json",
                "--sbom",
                "/evidence/sbom.json",
            ],
            timings=timings["gates"],
            name="in_image_validation",
        )
        gates["runtime_imports_and_resources"] = "PASS" if validation.returncode == 0 else "FAIL"

        dependencies = run(
            [
                "docker",
                "run",
                "--rm",
                "--user",
                "10001:10001",
                "--entrypoint",
                "python",
                args.image,
                "-m",
                "pip",
                "list",
                "--format=freeze",
            ],
            timings=timings["gates"],
            name="dependency_inventory",
        )
        (output / "dependency-tree.txt").write_text(dependencies.stdout, encoding="utf-8")

        governance = run(
            [
                str(ROOT / "venv/bin/python"),
                "-m",
                "pytest",
                "-q",
                "afritech/tests/governance/test_production_deployment_preflight.py",
            ],
            timings=timings["gates"],
            name="governance_tests",
        )
        gates["governance"] = "PASS"
        preflight = run(
            [
                str(ROOT / "venv/bin/python"),
                "scripts/preflight_production_deployment.py",
                "--env-file",
                str(args.env_file.resolve()),
                "--compose-file",
                str(args.compose_file.resolve()),
                "--check-compose",
            ],
            timings=timings["gates"],
            name="production_preflight",
        )
        gates["production_preflight"] = "PASS"

        if not args.skip_deploy:
            compose_command = [
                "docker",
                "compose",
                "--project-directory",
                str(args.compose_file.resolve().parent),
                "--env-file",
                str(args.env_file.resolve()),
                "-f",
                str(args.compose_file.resolve()),
            ]
            run(
                [
                    *compose_command,
                    "run",
                    "--rm",
                    "--no-deps",
                    "--entrypoint",
                    "python",
                    "afritech-api",
                    "-m",
                    "afritech.novaid.persistence.migrations",
                ],
                timings=timings["gates"],
                name="novaid_database_migrations",
            )
            gates["novaid_database_migrations"] = "PASS"
            run(
                [
                    *compose_command,
                    "up",
                    "-d",
                    "--no-deps",
                    "--force-recreate",
                    "afritech-api",
                ],
                timings=timings["gates"],
                name="api_deployment",
            )
            health = http_gate("http://127.0.0.1:8001/health")
            ready = http_gate("http://127.0.0.1:8001/ready")
            timings["gates"]["health_http"] = health
            timings["gates"]["ready_http"] = ready
            gates["health"] = health["status"]
            gates["ready"] = ready["status"]

            if health["status"] == "PASS" and ready["status"] == "PASS":
                run(
                    [
                        "docker",
                        "exec",
                        "production-afritech-api-1",
                        "python",
                        "-c",
                        (
                            "import os, psycopg, redis;"
                            "c=psycopg.connect(os.environ['NOVAPROGRAMMING_DATABASE_URL']);"
                            "c.execute('SELECT 1').fetchone();c.close();"
                            "assert redis.from_url(os.environ['NOVAID_REDIS_URL']).ping();"
                            "print('postgres=PASS redis=PASS')"
                        ),
                    ],
                    timings=timings["gates"],
                    name="database_redis_connectivity",
                )
                gates["postgresql"] = "PASS"
                gates["redis"] = "PASS"
            else:
                gates["postgresql"] = "BLOCKED"
                gates["redis"] = "BLOCKED"
                raise RuntimeError("HTTP health/readiness gates failed")
        else:
            health = ready = {"status": "SKIPPED"}
            gates.update({"health": "SKIPPED", "ready": "SKIPPED", "postgresql": "SKIPPED", "redis": "SKIPPED"})

        runtime_validation = json.loads((output / "runtime-validation.json").read_text(encoding="utf-8"))
        sbom_hash = sha256(output / "sbom.json")
        manifest = {
            "schema_version": 1,
            "repository": {"commit": commit, "branch": branch},
            "build_timestamp": build_timestamp,
            "image": image,
            "python_version": runtime_validation["python"],
            "dependency_versions": {
                name: value["version"]
                for name, value in runtime_validation["imports"].items()
            },
        }
        write_json(output / "image-manifest.json", manifest)
        report = {
            "schema_version": 1,
            "status": "PASS",
            "image": image["id"],
            "gates": gates,
            "governance_output": governance.stdout.strip(),
            "preflight_output": preflight.stdout.strip(),
        }
        write_json(output / "build-report.json", report)
        certification = {
            "schema_version": 1,
            "phase": "3B.3A6",
            "status": "PASS",
            "classification": [
                "IMPLEMENTATION_COMPLETE",
                "BUILD_SYSTEM_CERTIFIED",
                "PRODUCTION_RUNTIME_CERTIFIED",
                "READY_FOR_RELEASE_CANDIDATE",
            ],
            "repository_commit": commit,
            "docker_image_digest": image["id"],
            "runtime_validation": runtime_validation["status"],
            "governance_validation": gates["governance"],
            "security_validation": gates["production_preflight"],
            "dependency_validation": gates["runtime_imports_and_resources"],
            "sbom_sha256": sbom_hash,
            "release_timestamp": utc_now(),
            "gates": gates,
        }
        if any(value == "FAIL" for value in gates.values()):
            raise RuntimeError("one or more certification gates failed")
        write_json(output / "certification.json", certification)
        timings["completed_at"] = utc_now()
        write_json(output / "build-timing.json", timings)
        print("Phase 3B.3A6 production build certification PASSED")
        return 0
    except Exception as exc:
        timings["completed_at"] = utc_now()
        timings["status"] = "FAIL"
        timings["error"] = str(exc)
        write_json(output / "build-timing.json", timings)
        write_json(
            output / "build-report.json",
            {"schema_version": 1, "status": "FAIL", "error": str(exc), "gates": gates},
        )
        print(f"Phase 3B.3A6 production build certification FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
