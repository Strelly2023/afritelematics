"""Compatibility exports for the auth namespace."""

from __future__ import annotations

from .legacy_auth import require_api_key

__all__ = ["require_api_key"]