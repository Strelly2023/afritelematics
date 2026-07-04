"""Basic local documentation link checker."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "#", "/Users/", "/private/", "/tmp/", "/var/"))


def _resolve(path: Path, target: str) -> Path:
    fragment = target.split("#", 1)[0]
    if fragment.startswith("/"):
        return (ROOT / fragment.lstrip("/")).resolve()
    return (path.parent / fragment).resolve()


def validate() -> list[str]:
    broken: list[str] = []
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", "node_modules", "dist", "build", "venv", ".venv", "site-packages"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if _is_external(target):
                continue
            resolved = _resolve(path, target)
            if not resolved.exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    return broken


def main() -> int:
    broken = validate()
    if broken:
        print("Documentation link validation FAILED")
        for item in broken[:200]:
            print(f"- {item}")
        return 1
    print("Documentation link validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
