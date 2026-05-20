"""Uniform API response envelopes."""

from __future__ import annotations

from typing import Any


def success(data: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "data": data,
        "error": None,
    }


def error(code: str, message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }
