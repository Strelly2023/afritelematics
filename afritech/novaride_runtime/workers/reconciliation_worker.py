from __future__ import annotations

from afritech.novaride_runtime.config import NovaRideRuntimeSettings


def main() -> int:
    NovaRideRuntimeSettings.from_env().validate()
    print("novaride_reconciliation_worker_configured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
