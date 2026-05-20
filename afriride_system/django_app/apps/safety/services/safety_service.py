"""Deterministic safety skeleton."""

from __future__ import annotations


class SafetyService:
    """Provide deterministic placeholders for baseline trust flows."""

    @staticmethod
    def generate_pin() -> str:
        return "1234"
