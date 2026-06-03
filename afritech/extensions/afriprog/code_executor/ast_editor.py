from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any


class ASTEditorError(Exception):
    """Raised when AST inspection or transformation fails."""


@dataclass(frozen=True)
class ASTSummary:
    functions: tuple[str, ...]
    classes: tuple[str, ...]
    imports: tuple[str, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "functions": list(self.functions),
            "classes": list(self.classes),
            "imports": list(self.imports),
            "function_count": len(self.functions),
            "class_count": len(self.classes),
            "import_count": len(self.imports),
        }


class ASTEditor:
    """
    Safe code inspection and text proposal engine.

    Phase 4 behavior:
    - AST inspection allowed
    - text proposal allowed
    - no file writes
    - no in-place mutation
    """

    def inspect_python(self, content: str) -> ASTSummary:
        if not isinstance(content, str):
            raise ASTEditorError("content must be a string")

        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            raise ASTEditorError(f"invalid Python syntax: {exc}") from exc

        functions: list[str] = []
        classes: list[str] = []
        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)

            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)

            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append(module)

        return ASTSummary(
            functions=tuple(sorted(functions)),
            classes=tuple(sorted(classes)),
            imports=tuple(sorted(imports)),
        )

    def insert_text(
        self,
        content: str,
        insertion: str,
    ) -> str:
        if not isinstance(content, str):
            raise ASTEditorError("content must be a string")

        if not isinstance(insertion, str):
            raise ASTEditorError("insertion must be a string")

        normalized_insertion = insertion.strip()

        if not normalized_insertion:
            raise ASTEditorError("insertion must not be empty")

        if normalized_insertion in content:
            return content

        return content.rstrip() + "\n\n" + normalized_insertion + "\n"

    def canonical_dict_for_content(
        self,
        content: str,
    ) -> dict[str, Any]:
        return self.inspect_python(content).canonical_dict()