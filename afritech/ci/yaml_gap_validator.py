"""Validate missing YAML content gaps."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (
    ROOT / "afritech",
    ROOT / "ecosystems",
    ROOT / ".github",
)


class YamlGapValidationError(Exception):
    """Raised when YAML content gaps remain."""


def fail(message: str) -> None:
    raise YamlGapValidationError(message)


def yaml_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        files.extend(sorted(root.rglob("*.yaml")))
        files.extend(sorted(root.rglob("*.yml")))
    return files


def validate() -> None:
    empty: list[str] = []
    invalid: list[str] = []

    for path in yaml_files():
        relative = str(path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            empty.append(relative)
            continue
        try:
            payload = yaml.safe_load(text)
        except Exception as exc:
            invalid.append(f"{relative}: {exc}")
            continue
        if payload is None:
            empty.append(relative)

    if empty:
        fail(f"empty YAML files remain: {empty}")
    if invalid:
        fail(f"invalid YAML files: {invalid}")

    print("✅ YAML gap validation PASSED")
    print("✅ Empty YAML files: 0")
    print(f"✅ YAML files parsed: {len(yaml_files())}")


def main() -> int:
    try:
        validate()
        return 0
    except YamlGapValidationError as exc:
        print(f"❌ YAML gap validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
