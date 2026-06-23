#!/usr/bin/env python3
"""Apply NovaTech core platform SQL migrations."""

from __future__ import annotations

import os

from afritech.core_platform.migration_system import apply_migrations, build_migration_plan


def main() -> None:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is required")
    print(build_migration_plan())
    print(apply_migrations(dsn))


if __name__ == "__main__":
    main()
