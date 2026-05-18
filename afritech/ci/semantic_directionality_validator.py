from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / "afritech/constitution"

FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.runtime",
    "afritech.execution",
    "afritech.worker",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def module_name(path: Path) -> str:
    relative = path.relative_to(ROOT).with_suffix("")
    return ".".join(relative.parts)


def validate_python_directionality() -> None:
    for path in sorted(CONSTITUTION.rglob("*.py")):
        module = module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                        fail(f"{module} imports downward runtime module {alias.name}")

            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    fail(f"{module} imports downward runtime module {node.module}")


def run() -> None:
    validate_python_directionality()
    print("✅ Semantic directionality validation PASSED")
    print("✅ Constitution has no runtime/execution imports")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Semantic directionality validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
