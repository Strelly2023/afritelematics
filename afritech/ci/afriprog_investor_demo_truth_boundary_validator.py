from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEMO_ROOT = ROOT / "afriprogramming_demo"
PACKAGE_ROOT = ROOT / "AfriProgramming_Investor_Package"

REQUIRED_FILES = (
    DEMO_ROOT / "index.html",
    DEMO_ROOT / "src/app.js",
    DEMO_ROOT / "src/demoData.js",
    DEMO_ROOT / "src/styles.css",
    PACKAGE_ROOT / "README.md",
    PACKAGE_ROOT / "03_Technical/Whitepaper.md",
    PACKAGE_ROOT / "04_Business/One_Pager.md",
    PACKAGE_ROOT / "05_Outreach/Investor_Email.txt",
)

REQUIRED_BOUNDARY_PHRASES = (
    "controlled-pilot-ready",
    "not production-scale validated",
)

FORBIDDEN_CLAIMS = (
    "production-proven",
    "fully autonomous",
    "self-fixing",
    "guaranteed real-world reliability",
    "globally deployed",
)


def validate() -> None:
    missing = tuple(str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists())
    if missing:
        raise RuntimeError(f"investor package missing files: {missing}")

    material = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in REQUIRED_FILES
    ).lower()
    for phrase in REQUIRED_BOUNDARY_PHRASES:
        if phrase not in material:
            raise RuntimeError(f"missing truth boundary phrase: {phrase}")
    for claim in FORBIDDEN_CLAIMS:
        if claim in material and f"not {claim}" not in material:
            raise RuntimeError(f"forbidden unbounded claim found: {claim}")

    app = (DEMO_ROOT / "src/app.js").read_text(encoding="utf-8", errors="replace")
    for required in (
        "Non-authoritative",
        "Activation remains blocked",
        "Runtime mutation is allowed only through this gate",
    ):
        if required not in app:
            raise RuntimeError(f"demo missing authority boundary copy: {required}")


def main() -> int:
    try:
        validate()
        print("Afriprog investor demo truth-boundary validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog investor demo truth-boundary validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
