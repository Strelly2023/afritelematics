"""Outbox worker entrypoint.

The module is intentionally safe to import and dry-run locally. Production
deployments inject PostgreSQL/Kafka clients through the runtime container.
"""

from __future__ import annotations

from afritech.novaride_runtime.config import NovaRideRuntimeSettings


def main() -> int:
    settings = NovaRideRuntimeSettings.from_env()
    if settings.environment == "production":
        settings.validate()
    print("novaride_outbox_worker_configured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
