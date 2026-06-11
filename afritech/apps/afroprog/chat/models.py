"""Chat session contracts for AfriPro."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    mode: str

    def canonical_dict(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
            "mode": self.mode,
        }


@dataclass(frozen=True)
class ChatSession:
    session_id: str
    project_id: str
    open_file: str
    messages: tuple[ChatMessage, ...] = field(default_factory=tuple)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "open_file": self.open_file,
            "messages": [message.canonical_dict() for message in self.messages],
        }


__all__ = ["ChatMessage", "ChatSession"]
