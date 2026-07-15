"""PostgreSQL unit-of-work contract.

The runtime ships an in-memory adapter for tests and this contract for the
production adapter. Live PostgreSQL connections are intentionally not faked.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PostgresUnitOfWorkConfig:
    dsn: str
    schema: str = "novaride_runtime"
    rls_required: bool = True


class PostgresUnitOfWork:
    def __init__(self, config: PostgresUnitOfWorkConfig) -> None:
        self.config = config

    def require_configured(self) -> None:
        if not self.config.dsn:
            raise RuntimeError("postgres_dsn_required")
