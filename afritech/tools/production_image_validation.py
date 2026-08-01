"""Fail-closed validation and SBOM generation for the production API image."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_IMPORTS = (
    "numpy",
    "scipy",
    "sklearn",
    "psycopg",
    "redis",
    "yaml",
    "fastapi",
    "uvicorn",
)
RESOURCE_PATTERNS = {
    "json_schemas": "afritech/**/*.schema.json",
    "yaml_resources": "afritech/**/*.yaml",
    "sql_migrations": "afritech/**/*.sql",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_runtime() -> dict[str, Any]:
    imports: dict[str, dict[str, str]] = {}
    for name in REQUIRED_IMPORTS:
        module = importlib.import_module(name)
        package_name = "PyYAML" if name == "yaml" else ("scikit-learn" if name == "sklearn" else name)
        imports[name] = {
            "status": "PASS",
            "version": importlib.metadata.version(package_name),
            "module": str(getattr(module, "__file__", "")),
        }

    afritech_root = Path(importlib.import_module("afritech").__file__).resolve().parent
    resources: dict[str, dict[str, Any]] = {}
    for key, pattern in RESOURCE_PATTERNS.items():
        relative_pattern = pattern.removeprefix("afritech/")
        matches = sorted(afritech_root.glob(relative_pattern))
        if not matches:
            raise RuntimeError(f"missing packaged resource class: {key}")
        resources[key] = {"status": "PASS", "count": len(matches)}

    from afritech.api.contracts.validator import EventContractValidator
    from afritech.platform_contracts.schema_registry import SchemaRegistry
    from services.administration.app_registry import build_app_registry_manifest

    EventContractValidator()
    schema_registry = SchemaRegistry()
    resources["event_registry"] = {
        "status": "PASS",
        "path": str(schema_registry.registry_path),
        "entries": len(schema_registry.event_types()),
    }
    manifest = build_app_registry_manifest()
    if not isinstance(manifest, dict):
        raise RuntimeError("administration app registry did not return an object")

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider

    provider = TracerProvider()
    provider.get_tracer("afritech.production-build").start_span("validation").end()
    if trace is None:
        raise RuntimeError("OpenTelemetry trace API unavailable")

    return {
        "status": "PASS",
        "validated_at": _utc_now(),
        "python": platform.python_version(),
        "imports": imports,
        "resources": resources,
        "event_contracts": "PASS",
        "administration_service": "PASS",
        "opentelemetry_initialization": "PASS",
    }


def build_sbom() -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    for distribution in sorted(importlib.metadata.distributions(), key=lambda item: item.metadata["Name"].lower()):
        name = distribution.metadata["Name"]
        files = list(distribution.files or ())
        hashes: list[dict[str, str]] = []
        for relative in files:
            path = Path(distribution.locate_file(relative))
            if path.is_file() and path.stat().st_size <= 10 * 1024 * 1024:
                hashes.append({"path": str(relative), "sha256": _sha256(path)})
        components.append(
            {
                "type": "library",
                "name": name,
                "version": distribution.version,
                "purl": f"pkg:pypi/{name}@{distribution.version}",
                "hashes": hashes,
            }
        )

    os_packages: list[dict[str, str]] = []
    result = subprocess.run(
        ["dpkg-query", "-W", "-f=${Package}\\t${Version}\\n"],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        name, version = line.split("\t", 1)
        os_packages.append({"name": name, "version": version, "purl": f"pkg:deb/debian/{name}@{version}"})

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": _utc_now(),
            "component": {"type": "application", "name": "afritech-api"},
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "components": components,
        "os_packages": os_packages,
    }


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--sbom", type=Path)
    args = parser.parse_args()
    validation = validate_runtime()
    if args.output:
        _write(args.output, validation)
    else:
        print(json.dumps(validation, sort_keys=True))
    if args.sbom:
        _write(args.sbom, build_sbom())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
