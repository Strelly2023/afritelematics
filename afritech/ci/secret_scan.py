"""Lightweight repository secret scanner."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)aws(.{0,20})?(secret|access).{0,20}=[\"']?[A-Za-z0-9/+=]{20,}"),
    re.compile(r"(?i)gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
)


def scan() -> list[str]:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "node_modules", "dist", "build", "__pycache__", "venv", ".venv", "site-packages"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".md", ".json", ".yml", ".yaml", ".js", ".ts", ".tsx", ".toml", ".txt", ".env"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(ROOT)))
                break
    return findings


def main() -> int:
    findings = scan()
    if findings:
        print("Secret scan FAILED")
        for item in findings[:200]:
            print(f"- {item}")
        return 1
    print("Secret scan PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
