"""Validate explicit PARTIAL/PLANNED occurrence audit."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "afritech/ci/partial_planned_audit.yaml"
SCAN_ROOTS = (
    ROOT / "afritech",
    ROOT / "ecosystems",
    ROOT / ".github",
)
PATTERN = re.compile(r"\b(PARTIAL|PLANNED)\b")


class PartialPlannedAuditError(Exception):
    """Raised when unresolved PARTIAL/PLANNED references are unaudited."""


def fail(message: str) -> None:
    raise PartialPlannedAuditError(message)


def load_audit() -> dict:
    payload = yaml.safe_load(AUDIT.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail("partial_planned_audit.yaml must be a mapping")
    return payload


def scanned_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".py", ".yaml", ".yml", ".md", ".lean"}:
                continue
            files.append(path)
    return sorted(files)


def validate() -> None:
    audit = load_audit()
    allowed_entries = audit.get("allowed_occurrences")
    if not isinstance(allowed_entries, list) or not allowed_entries:
        fail("audit must declare allowed_occurrences")

    allowed = {
        entry.get("path")
        for entry in allowed_entries
        if isinstance(entry, dict)
    }
    invalid_entries = [
        entry for entry in allowed_entries
        if not isinstance(entry, dict)
        or not entry.get("path")
        or not entry.get("class")
        or not entry.get("reason")
    ]
    if invalid_entries:
        fail(f"invalid audit entries: {invalid_entries}")

    discovered: set[str] = set()
    for path in scanned_files():
        relative = str(path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PATTERN.search(text):
            discovered.add(relative)

    unaudited = sorted(discovered - allowed - {str(AUDIT.relative_to(ROOT))})
    stale = sorted(allowed - discovered)

    if unaudited:
        fail(f"unaudited PARTIAL/PLANNED references: {unaudited}")
    if stale:
        fail(f"stale PARTIAL/PLANNED audit entries: {stale}")

    print("✅ PARTIAL/PLANNED audit validation PASSED")
    print(f"✅ Audited files: {len(allowed)}")


def main() -> int:
    try:
        validate()
        return 0
    except PartialPlannedAuditError as exc:
        print(f"❌ PARTIAL/PLANNED audit validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
