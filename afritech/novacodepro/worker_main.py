from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from afritech.novacodepro.distributed.workers import AgentExecutionWorker, OutboxWorker
from afritech.novacodepro.platform import NovaCodeProPlatform, get_novacodepro_platform


def _platform(service_name: str, db_env_var: str, database_url_env_var: str | None = None) -> tuple[Path, NovaCodeProPlatform]:
    db_path = Path(os.environ.get(db_env_var, f"var/novacodepro/{service_name}.sqlite3"))
    database_url = None
    for env_var in (
        database_url_env_var,
        "NOVACODEPRO_DATABASE_URL",
        f"NOVACODEPRO_{service_name.upper().replace('-', '_')}_DATABASE_URL",
    ):
        if env_var and os.environ.get(env_var):
            database_url = os.environ.get(env_var)
            break
    return db_path, get_novacodepro_platform(db_path, database_url=database_url)


def run_worker(*, service_name: str, db_env_var: str, kind: str, interval: float = 1.0, database_url_env_var: str | None = None) -> None:
    _, platform = _platform(service_name, db_env_var, database_url_env_var=database_url_env_var)
    if kind == "agents":
        worker = AgentExecutionWorker(platform=platform)
    else:
        worker = OutboxWorker(platform=platform)
    while True:
        worker.run_once()
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="NovaCodePro worker runner")
    parser.add_argument("service_name")
    parser.add_argument("kind", choices=["agents", "outbox"])
    parser.add_argument("--db-env-var", default="NOVACODEPRO_DB_PATH")
    parser.add_argument("--database-url-env-var")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    run_worker(
        service_name=args.service_name,
        db_env_var=args.db_env_var,
        kind=args.kind,
        database_url_env_var=args.database_url_env_var,
        interval=args.interval,
    )


if __name__ == "__main__":  # pragma: no cover - process entrypoint
    main()
