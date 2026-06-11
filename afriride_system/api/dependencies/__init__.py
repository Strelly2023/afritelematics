"""Dependency exports for FastAPI route and middleware wiring."""

from afriride_system.api.dependencies.runtime import (
    get_gateway,
    get_trace_log,
    reset_gateway,
    reset_trace_log,
)

__all__ = ["get_gateway", "get_trace_log", "reset_gateway", "reset_trace_log"]
