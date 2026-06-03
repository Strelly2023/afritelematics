"""Enforce AfriTech/AfriRide four-gate governance."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from afritech.ci import claim_discipline_validator
from afritech.ci import enforcement_integrity_validator
from afritech.ci import proof_surface_validator


ROOT = Path(__file__).resolve().parents[2]

ALLOWED_ACTIVE_ECOSYSTEMS = {"afriride", "afriprogramming"}

PROOF_EXPECTED = {
    "continuity": "pass",
    "replay": "pass",
    "identity": "stable",
    "conflicts": "deterministic",
    "claims_valid": True,
    "scope": "controlled_simulated_disruption",
    "global_deployment_readiness_claimed": False,
    "classification": "bounded deterministic continuity validation architecture",
}

API_FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.ci",
    "afritech.core.runtime",
    "afritech.demo.proof",
    "ecosystems.afriride.continuity",
    "ecosystems.afriride.runtime",
)

API_FORBIDDEN_NAMES = {
    "AssignDriver",
    "DeterministicExecutor",
    "canonical_hash",
    "execute",
    "execute_with_state",
    "initial_state",
}

MOBILE_FORBIDDEN_DELIVERY_TOKENS = (
    "new WebSocket(",
    "EventSource(",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def repo_path(path: Path) -> str:
    return str(path.relative_to(ROOT))


def validate_proof_meaning() -> None:
    proof_surface_validator.validate()

    result = subprocess.run(
        [sys.executable, "-m", "afritech.demo.proof", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        fail(result.stderr.strip() or "proof JSON output failed")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"proof JSON output is not valid JSON: {exc}")

    mismatches = {
        key: (payload.get(key), expected)
        for key, expected in PROOF_EXPECTED.items()
        if payload.get(key) != expected
    }
    if mismatches:
        fail(f"proof meaning changed: {mismatches}")

    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        fail("proof payload must include AfriRide scenarios")
    for scenario in scenarios:
        if not isinstance(scenario, str) or not scenario.startswith("AFRIRIDE-"):
            fail(f"non-AfriRide proof scenario detected: {scenario!r}")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


def referenced_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }


def validate_api_authority_boundary() -> None:
    api_root = ROOT / "afriride_system/api"
    for path in sorted(api_root.glob("*.py")):
        if path.name == "__init__.py":
            continue

        for module in imported_modules(path):
            if module.startswith(API_FORBIDDEN_IMPORT_PREFIXES):
                fail(
                    f"API authority boundary violation in {repo_path(path)}: "
                    f"imports {module}"
                )

        forbidden_names = referenced_names(path) & API_FORBIDDEN_NAMES
        if forbidden_names:
            fail(
                f"API authority boundary violation in {repo_path(path)}: "
                f"references core decision names {sorted(forbidden_names)}"
            )


def validate_delivery_boundary() -> None:
    mobile_root = ROOT / "afriride_system/mobile"
    if not mobile_root.exists():
        return

    for path in sorted(mobile_root.rglob("*.js")):
        text = path.read_text(encoding="utf-8")
        for token in MOBILE_FORBIDDEN_DELIVERY_TOKENS:
            if token in text:
                fail(
                    f"delivery boundary violation in {repo_path(path)}: "
                    "WebSocket delivery requires event -> poll -> confirmed state"
                )


def validate_afriride_scope() -> None:
    ecosystems_root = ROOT / "ecosystems"
    active = {
        path.name
        for path in ecosystems_root.iterdir()
        if path.is_dir() and not path.name.startswith("__")
    }
    invalid = active - ALLOWED_ACTIVE_ECOSYSTEMS
    if invalid:
        fail(f"active ecosystem scope expanded: {sorted(invalid)}")


def validate_claim_discipline() -> None:
    claim_discipline_validator.validate()


def validate_authority_boundaries() -> None:
    validate_api_authority_boundary()
    validate_delivery_boundary()


def validate() -> None:
    validate_proof_meaning()
    validate_authority_boundaries()
    validate_afriride_scope()
    validate_claim_discipline()
    enforcement_integrity_validator.validate()


def main() -> int:
    try:
        validate()
        print("✅ Four-gate enforcement PASSED")
        print("✅ Proof meaning preserved")
        print("✅ Authority boundaries preserved")
        print("✅ AfriRide scope preserved")
        print("✅ Claim discipline preserved")
        print("✅ Enforcement integrity preserved")
        return 0
    except Exception as exc:
        print(f"❌ Four-gate enforcement failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
