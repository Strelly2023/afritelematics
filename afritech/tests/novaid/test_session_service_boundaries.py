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


def test_session_service_has_no_direct_sql_execution() -> None:
    source = Path("afritech/novaid/application/sessions.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"execute", "executemany"}:
            continue
        if _attribute_chain(node.func.value)[-2:] == ["uow", "connection"]:
            banned.append(node.lineno)
    assert banned == [], f"direct SQL execution remains in sessions.py at lines {banned}"
