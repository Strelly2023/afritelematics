"""Editor helpers for Codex-style AfriPro workspace panes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EditorDocument:
    path: str
    language: str
    content: str
    editor_engine: str = "Monaco-compatible"
    read_only: bool = False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "language": self.language,
            "content": self.content,
            "editor_engine": self.editor_engine,
            "read_only": self.read_only,
        }


def build_editor_document(path: str, language: str, content: str) -> EditorDocument:
    return EditorDocument(path=path, language=language, content=content)


__all__ = ["EditorDocument", "build_editor_document"]
