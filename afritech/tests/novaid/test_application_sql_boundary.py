from __future__ import annotations

import ast
from pathlib import Path


APP_DIR = Path("afritech/novaid/application")


def _attribute_chain(node: ast.AST) -> list[str]:
    chain: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        chain.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        chain.append(current.id)
    return list(reversed(chain))


def _find_banned_calls(source: str) -> list[int]:
    tree = ast.parse(source)
    banned: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"execute", "executemany"}:
            continue
        if _attribute_chain(node.func.value)[-2:] == ["uow", "connection"]:
            banned.append(node.lineno)
        if _attribute_chain(node.func.value)[-1:] == ["connection"]:
            banned.append(node.lineno)
    return banned


def test_novaid_application_layer_has_no_direct_sql_execution() -> None:
    banned: dict[str, list[int]] = {}
    for path in sorted(APP_DIR.rglob("*.py")):
        banned_lines = _find_banned_calls(path.read_text(encoding="utf-8"))
        if banned_lines:
            banned[str(path)] = banned_lines
    assert banned == {}, f"direct SQL execution remains in NovaID application layer: {banned}"
