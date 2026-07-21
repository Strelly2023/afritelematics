from __future__ import annotations

import ast
from pathlib import Path


def _attribute_chain(node: ast.AST) -> list[str]:
    chain: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        chain.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        chain.append(current.id)
    return list(reversed(chain))


def test_novaid_application_layer_has_no_direct_sql_execution() -> None:
    banned: list[str] = []
    for source_path in sorted(Path("afritech/novaid/application").glob("*.py")):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"execute", "executemany"}:
                continue
            if _attribute_chain(node.func.value)[-2:] == ["uow", "connection"]:
                banned.append(f"{source_path}:{node.lineno}")
    assert banned == [], f"direct SQL execution remains in the NovaID application layer at {banned}"
