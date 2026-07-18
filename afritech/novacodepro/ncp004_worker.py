from __future__ import annotations

import argparse
import os
from pathlib import Path

from afritech.novacodepro import NovaCodeProRepository
from afritech.novacodepro.ncp004 import NCP004ExecutionContext, NovaCodeProNCP004Service


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NovaCodePro governed AI worker")
    parser.add_argument("--repository", default=os.environ.get("NOVACODEPRO_REPOSITORY_PATH", "var/novacodepro.sqlite3"))
    parser.add_argument("--run-once", action="store_true", help="Print the current governed AI execution summary and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository = NovaCodeProRepository(Path(args.repository))
    service = NovaCodeProNCP004Service(repository)
    workspace_id = os.environ.get("NOVACODEPRO_WORKSPACE_ID") or next((str(item.get("id")) for item in repository.list("workspace") if item.get("id")), "workspace-1")
    ctx = NCP004ExecutionContext(
        execution_id="ncp004-worker",
        actor_id=os.environ.get("NOVACODEPRO_WORKER_ACTOR_ID", "system.worker"),
        tenant_id=os.environ.get("NOVACODEPRO_TENANT_ID", "novatech"),
        organization_id=os.environ.get("NOVACODEPRO_ORGANIZATION_ID", "NovaTech"),
        workspace_id=workspace_id,
        project_id=None,
        request_id=None,
        role="ADMIN",
        permissions=("ai.read", "ai.execute", "ai.request", "ai.approve"),
        environment=os.environ.get("NOVACODEPRO_ENVIRONMENT", "development"),
        session_id=None,
        correlation_id="ncp004-worker",
    )
    executions = service.list_executions(ctx)
    if args.run_once:
        print(f"executions={len(executions)}")
        for item in executions[:10]:
            print(f"{item.get('id')} {item.get('status')} {item.get('request_type') or item.get('request_text') or ''}")
        return 0
    print("NovaCodePro NCP-004 worker is ready. Use --run-once to print a summary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
