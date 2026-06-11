"""Backward-compatible gateway dependency exports.

The API storage selector remains governed by the Phase 1 setup contract:
`AFRIRIDE_DATABASE_URL` takes precedence, with `AFRIRIDE_DB_PATH` as the
SQLite fallback override. The implementation lives in
`afriride_system.api.dependencies.runtime`.
"""

from afriride_system.api.dependencies.runtime import get_gateway, reset_gateway

__all__ = ["get_gateway", "reset_gateway"]
