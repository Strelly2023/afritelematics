"""Authentication middleware placeholder."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class AuthMiddleware:
    """Pass-through middleware for future product authentication."""

    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        return self.get_response(request)
