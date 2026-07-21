#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "artifacts" / "ga-readiness" / "release" / "sbom"
DEFAULT_REPORT_JSON = DEFAULT_OUTPUT_DIR / "report.json"
DEFAULT_REPORT_MD = DEFAULT_OUTPUT_DIR / "report.md"


@dataclass(frozen=True)
class SbomTarget:
    component_id: str
    product: str
    source_path: Path
    kind: str
    manifest_path: Path | None = None
    lockfile_path: Path | None = None
    requirements_path: Path | None = None
    dev_requirements_path: Path | None = None


TARGETS: tuple[SbomTarget, ...] = (
    SbomTarget(
        component_id="novacodepro_portal",
        product="NovaCodePro",
        source_path=ROOT / "novacodepro_portal",
        kind="node",
        manifest_path=ROOT / "novacodepro_portal" / "package.json",
        lockfile_path=ROOT / "novacodepro_portal" / "package-lock.json",
    ),
    SbomTarget(
        component_id="novaid_backend",
        product="NovaID",
        source_path=ROOT / "afritech" / "novaid",
        kind="python",
        requirements_path=ROOT / "requirements.txt",
        dev_requirements_path=ROOT / "requirements-dev.txt",
    ),
    SbomTarget(
        component_id="novapay_backend",
        product="NovaPay",
        source_path=ROOT / "afritech" / "novapay",
        kind="python",
        requirements_path=ROOT / "requirements.txt",
        dev_requirements_path=ROOT / "requirements-dev.txt",
    ),
    SbomTarget(
        component_id="novaride_runtime",
        product="NovaRide",
        source_path=ROOT / "afritech" / "novaride_runtime",
        kind="python",
        requirements_path=ROOT / "requirements.txt",
        dev_requirements_path=ROOT / "requirements-dev.txt",
    ),
    SbomTarget(
        component_id="novacodepro_backend",
        product="NovaCodePro",
        source_path=ROOT / "afritech" / "api",
        kind="python",
        requirements_path=ROOT / "requirements.txt",
        dev_requirements_path=ROOT / "requirements-dev.txt",
    ),
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def commit_epoch() -> int:
    return int(git("show", "-s", "--format=%ct", "HEAD"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def component_ref(component_id: str, suffix: str = "root") -> str:
    return f"urn:novatech:sbom:{component_id}:{suffix}"


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_requirements(path: Path | None) -> list[dict[str, str]]:
    if not path or not path.exists():
        return []
    requirements: list[dict[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--requirement ")):
            continue
        marker_split = line.split(";", 1)
        requirement = marker_split[0].strip()
        if requirement.startswith(("-e ", "--editable ")):
            requirement = requirement.split(maxsplit=1)[1].strip()
        match = re.match(r"^([A-Za-z0-9_.-]+)(.*)$", requirement)
        if not match:
            continue
        name, spec = match.groups()
        requirements.append(
            {
                "name": name.lower().replace("_", "-"),
                "raw": requirement,
                "version_spec": spec.strip(),
            }
        )
    return sorted(requirements, key=lambda item: item["name"])


def build_node_sbom(target: SbomTarget) -> dict[str, Any]:
    if not target.manifest_path or not target.manifest_path.exists():
        raise FileNotFoundError(target.manifest_path or target.source_path)
    package = read_json(target.manifest_path)
    lockfile = read_json(target.lockfile_path) if target.lockfile_path and target.lockfile_path.exists() else {}
    lock_packages = lockfile.get("packages", {}) if isinstance(lockfile, dict) else {}
    direct_dependencies = {
        **(package.get("dependencies") or {}),
        **(package.get("devDependencies") or {}),
    }
    root_version = str(package.get("version", "0.0.0"))
    root_ref = component_ref(target.component_id)
    components: list[dict[str, Any]] = [
        {
            "bom-ref": root_ref,
            "type": "application",
            "name": str(package.get("name", target.component_id)),
            "version": root_version,
            "purl": f"pkg:npm/{package.get('name', target.component_id)}@{root_version}",
            "scope": "required",
        }
    ]
    dependencies: list[dict[str, Any]] = []
    root_dep_refs: list[str] = []
    for dep_name, dep_spec in sorted(direct_dependencies.items(), key=lambda item: item[0]):
        package_key = f"node_modules/{dep_name}"
        package_entry = lock_packages.get(package_key, {}) if isinstance(lock_packages, dict) else {}
        dep_version = str(package_entry.get("version") or dep_spec.get("version") or "unknown")
        dep_ref = component_ref(target.component_id, dep_name)
        root_dep_refs.append(dep_ref)
        components.append(
            {
                "bom-ref": dep_ref,
                "type": "library",
                "name": dep_name,
                "version": dep_version,
                "purl": f"pkg:npm/{dep_name}@{dep_version}",
                "scope": "required" if dep_name in (package.get("dependencies") or {}) else "optional",
            }
        )
        dependencies.append({"ref": dep_ref, "dependsOn": []})
    dependencies.insert(0, {"ref": root_ref, "dependsOn": root_dep_refs})
    serial_seed = canonical_json(
        {
            "component_id": target.component_id,
            "product": target.product,
            "source_path": target.source_path.as_posix(),
            "manifest": target.manifest_path.as_posix() if target.manifest_path else None,
            "kind": target.kind,
            "commit": git("rev-parse", "HEAD"),
        }
    )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, serial_seed)}",
        "metadata": {
            "timestamp": datetime.fromtimestamp(commit_epoch(), tz=timezone.utc).isoformat(timespec="milliseconds"),
            "component": {
                "bom-ref": root_ref,
                "type": "application",
                "name": str(package.get("name", target.component_id)),
                "version": root_version,
                "purl": f"pkg:npm/{package.get('name', target.component_id)}@{root_version}",
            },
            "tools": [
                {
                    "vendor": "AfriTech",
                    "name": "generate_sbom_bundle.py",
                    "version": "1",
                }
            ],
            "properties": [
                {"name": "afritech:product", "value": target.product},
                {"name": "afritech:source_path", "value": target.source_path.as_posix()},
                {"name": "afritech:component_id", "value": target.component_id},
                {"name": "afritech:build_commit", "value": git("rev-parse", "HEAD")},
                {"name": "afritech:source_mtime", "value": str(int(target.source_path.stat().st_mtime))},
            ],
        },
        "components": components,
        "dependencies": dependencies,
    }


def build_python_sbom(target: SbomTarget) -> dict[str, Any]:
    requirements = parse_requirements(target.requirements_path)
    dev_requirements = parse_requirements(target.dev_requirements_path)
    root_ref = component_ref(target.component_id)
    components = [
        {
            "bom-ref": root_ref,
            "type": "application",
            "name": target.component_id,
            "version": git("rev-parse", "HEAD")[:12],
            "purl": f"pkg:generic/{target.component_id}@{git('rev-parse', 'HEAD')[:12]}",
            "scope": "required",
        }
    ]
    dependencies: list[dict[str, Any]] = []
    root_dep_refs: list[str] = []
    for requirement in requirements + dev_requirements:
        dep_ref = component_ref(target.component_id, requirement["name"])
        root_dep_refs.append(dep_ref)
        components.append(
            {
                "bom-ref": dep_ref,
                "type": "library",
                "name": requirement["name"],
                "version": requirement["version_spec"] or "unspecified",
                "purl": f"pkg:pypi/{requirement['name']}",
                "scope": "required" if requirement in requirements else "optional",
                "properties": [{"name": "afritech:raw_requirement", "value": requirement["raw"]}],
            }
        )
        dependencies.append({"ref": dep_ref, "dependsOn": []})
    dependencies.insert(0, {"ref": root_ref, "dependsOn": root_dep_refs})
    serial_seed = canonical_json(
        {
            "component_id": target.component_id,
            "product": target.product,
            "source_path": target.source_path.as_posix(),
            "requirements": [item["raw"] for item in requirements],
            "dev_requirements": [item["raw"] for item in dev_requirements],
            "commit": git("rev-parse", "HEAD"),
        }
    )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, serial_seed)}",
        "metadata": {
            "timestamp": datetime.fromtimestamp(commit_epoch(), tz=timezone.utc).isoformat(timespec="milliseconds"),
            "component": {
                "bom-ref": root_ref,
                "type": "application",
                "name": target.component_id,
                "version": git("rev-parse", "HEAD")[:12],
                "purl": f"pkg:generic/{target.component_id}@{git('rev-parse', 'HEAD')[:12]}",
            },
            "tools": [
                {
                    "vendor": "AfriTech",
                    "name": "generate_sbom_bundle.py",
                    "version": "1",
                }
            ],
            "properties": [
                {"name": "afritech:product", "value": target.product},
                {"name": "afritech:source_path", "value": target.source_path.as_posix()},
                {"name": "afritech:component_id", "value": target.component_id},
                {"name": "afritech:build_commit", "value": git("rev-parse", "HEAD")},
                {
                    "name": "afritech:requirements_manifest",
                    "value": target.requirements_path.as_posix() if target.requirements_path else "",
                },
            ],
        },
        "components": components,
        "dependencies": dependencies,
    }


def build_target_sbom(target: SbomTarget) -> dict[str, Any]:
    if target.kind == "node":
        return build_node_sbom(target)
    if target.kind == "python":
        return build_python_sbom(target)
    raise ValueError(f"unsupported SBOM target kind: {target.kind}")


def build_aggregate_sbom(target_files: list[Path]) -> dict[str, Any]:
    root_ref = component_ref("release_bundle")
    components = []
    dependencies = []
    root_dep_refs: list[str] = []
    for path in target_files:
        sbom = read_json(path)
        component = sbom.get("metadata", {}).get("component", {})
        component_name = str(component.get("name") or path.stem)
        component_version = str(component.get("version") or "unknown")
        ref = f"urn:novatech:aggregate:{path.stem}"
        root_dep_refs.append(ref)
        components.append(
            {
                "bom-ref": ref,
                "type": "application",
                "name": component_name,
                "version": component_version,
                "purl": str(component.get("purl") or f"pkg:generic/{component_name}@{component_version}"),
                "properties": [
                    {"name": "afritech:sbom_path", "value": path.as_posix()},
                    {"name": "afritech:sbom_serial", "value": str(sbom.get("serialNumber", ""))},
                ],
            }
        )
        dependencies.append({"ref": ref, "dependsOn": []})
    dependencies.insert(0, {"ref": root_ref, "dependsOn": root_dep_refs})
    serial_seed = canonical_json({"aggregate": [path.as_posix() for path in target_files], "commit": git("rev-parse", "HEAD")})
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, serial_seed)}",
        "metadata": {
            "timestamp": datetime.fromtimestamp(commit_epoch(), tz=timezone.utc).isoformat(timespec="milliseconds"),
            "component": {
                "bom-ref": root_ref,
                "type": "application",
                "name": "novatech-release-bundle",
                "version": git("rev-parse", "HEAD")[:12],
                "purl": f"pkg:generic/novatech-release-bundle@{git('rev-parse', 'HEAD')[:12]}",
            },
            "tools": [
                {
                    "vendor": "AfriTech",
                    "name": "generate_sbom_bundle.py",
                    "version": "1",
                }
            ],
            "properties": [
                {"name": "afritech:bundle_commit", "value": git("rev-parse", "HEAD")},
            ],
        },
        "components": components,
        "dependencies": dependencies,
    }


def write_json(path: Path, payload: dict[str, Any]) -> str:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    sbom_files: list[Path] = []
    for target in TARGETS:
        try:
            sbom = build_target_sbom(target)
        except FileNotFoundError as exc:
            blocked.append(
                {
                    "component_id": target.component_id,
                    "product": target.product,
                    "reason": f"missing_source:{exc}",
                }
            )
            continue
        output_path = output_dir / f"{target.component_id}.cdx.json"
        digest = write_json(output_path, sbom)
        generated.append(
            {
                "component_id": target.component_id,
                "product": target.product,
                "path": display_path(output_path),
                "sha256": digest,
            }
        )
        sbom_files.append(output_path)
    aggregate_path = output_dir / "release-aggregate.cdx.json"
    aggregate_digest = write_json(aggregate_path, build_aggregate_sbom(sbom_files))
    generated.append(
        {
            "component_id": "release_aggregate",
            "product": "shared",
            "path": display_path(aggregate_path),
            "sha256": aggregate_digest,
        }
    )
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "branch": git("branch", "--show-current"),
        "commit": git("rev-parse", "HEAD"),
        "status": "PASS" if generated else "BLOCKED",
        "generated": generated,
        "blocked": blocked,
    }
    (output_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_lines = [
        "# Release SBOM Bundle",
        "",
        f"- branch: `{report['branch']}`",
        f"- commit: `{report['commit']}`",
        f"- status: `{report['status']}`",
        "",
        "## Generated",
    ]
    for item in generated:
        md_lines.append(f"- `{item['component_id']}` -> `{item['path']}`")
    md_lines.append("")
    md_lines.append("## Blocked")
    if blocked:
        for item in blocked:
            md_lines.append(f"- `{item['component_id']}`: `{item['reason']}`")
    else:
        md_lines.append("- none")
    (output_dir / "report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    report = generate(args.output_dir)
    print(json.dumps({"status": report["status"], "generated": len(report["generated"]), "blocked": len(report["blocked"])}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
