from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from architecture_validator.scanners.files import iter_text_files


class ForbiddenCallVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path, forbidden_call_names: set[str]) -> None:
        self.file_path = file_path
        self.forbidden_call_names = forbidden_call_names
        self.issues: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        call_name = _call_name(node.func)
        if call_name in self.forbidden_call_names:
            self.issues.append(
                f"{self.file_path}:{node.lineno}: Forbidden authority call detected: {call_name}"
            )
        self.generic_visit(node)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def scan_python_ast(
    roots: Iterable[str | Path],
    forbidden_call_names: Iterable[str],
) -> list[str]:
    issues: list[str] = []
    forbidden = {str(name) for name in forbidden_call_names if str(name)}
    if not forbidden:
        return issues

    for path in iter_text_files(roots):
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            issues.append(f"{path}:{exc.lineno or 1}: Python AST parse failed: {exc.msg}")
            continue
        visitor = ForbiddenCallVisitor(path, forbidden)
        visitor.visit(tree)
        issues.extend(visitor.issues)

    return issues
