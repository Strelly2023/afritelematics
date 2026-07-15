"""Pagination primitives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageRequest:
    limit: int = 50
    cursor: str | None = None

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 500:
            raise ValueError("invalid_page_limit")
