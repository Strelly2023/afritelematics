from __future__ import annotations

from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

FORBIDDEN_IMPORT_PATTERNS = (
    "from governance.",
    "import governance.",
)

ALLOWED_EXCEPTIONS = (
    # Explicit overrides if ever needed (keep empty for now)
)


# ============================================================
# CORE TEST
# ============================================================

def test_governance_imports_use_afritech_root():
    """
    Ensure all governance imports use canonical module-path identity.

    Forbidden:
        from governance.*
        import governance.*

    Required:
        from afritech.governance.*
    """

    root = Path("afritech/governance")

    violations: list[str] = []

    for path in root.rglob("*.py"):
        # Skip cache and hidden dirs
        if "__pycache__" in path.parts:
            continue

        text = path.read_text(encoding="utf-8")

        for pattern in FORBIDDEN_IMPORT_PATTERNS:
            if pattern in text:
                if any(exc in text for exc in ALLOWED_EXCEPTIONS):
                    continue

                violations.append(f"{path}: contains '{pattern}'")

    assert not violations, "\n".join(violations)


# ============================================================
# STRICT MODE (OPTIONAL HARDENING)
# ============================================================

def test_no_relative_imports_in_governance():
    """
    Prevent relative imports inside governance layer.

    This enforces:
    - full canonical module identity
    - no ambiguous resolution
    """

    root = Path("afritech/governance")

    violations: list[str] = []

    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        text = path.read_text(encoding="utf-8")

        if "from ." in text or "import ." in text:
            violations.append(f"{path}: contains relative import")

    assert not violations, "\n".join(violations)


# ============================================================
# CANONICAL PREFIX ENFORCEMENT
# ============================================================

def test_governance_imports_resolve_to_afritech_prefix():
    """
    Ensure governance imports explicitly reference afritech namespace.

    Example:
        ✅ from afritech.governance.policy...
        ❌ from governance.policy...
    """

    root = Path("afritech/governance")

    violations: list[str] = []

    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        text = path.read_text(encoding="utf-8")

        lines = text.splitlines()

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()

            if stripped.startswith("from ") or stripped.startswith("import "):
                # Skip stdlib / third-party safely
                if stripped.startswith(
                    ("from afritech.", "import afritech.", "import ", "from fastapi", "from typing", "from pathlib", "import json")
                ):
                    continue

                # Catch forbidden governance import
                if "governance." in stripped and not stripped.startswith("from afritech."):
                    violations.append(f"{path}:{i} → {stripped}")

    assert not violations, "\n".join(violations)