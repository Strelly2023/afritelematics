"""Request logging middleware placeholder."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class RequestLoggingMiddleware:
    """Pass-through middleware for future request logging."""

    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        return self.get_response(request)
