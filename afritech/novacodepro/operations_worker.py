from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from afritech.novacodepro import NCP008ExecutionContext, NCP008OperationsService, NovaCodeProPlatform, NovaCodeProRepository


def _repository() -> NovaCodeProRepository:
    db_path = Path(os.environ.get("NOVACODEPRO_OPERATIONS_DB_PATH") or "/var/lib/novacodepro/operations.sqlite3")
    return NovaCodeProRepository(db_path)


def _context() -> NCP008ExecutionContext:
    tenant = os.environ.get("NOVACODEPRO_TENANT_ID") or "novatech"
    organization = os.environ.get("NOVACODEPRO_ORGANIZATION_ID") or tenant
    return NCP008ExecutionContext(
        actor_id=os.environ.get("NOVACODEPRO_WORKER_ACTOR_ID") or "operations-worker",
        tenant_id=tenant,
        organization_id=organization,
        workspace_id=os.environ.get("NOVACODEPRO_WORKER_WORKSPACE_ID") or None,
        project_id=os.environ.get("NOVACODEPRO_WORKER_PROJECT_ID") or None,
        request_id=os.environ.get("NOVACODEPRO_WORKER_REQUEST_ID") or None,
        environment=os.environ.get("NOVACODEPRO_ENVIRONMENT") or "development",
        region=os.environ.get("NOVACODEPRO_REGION") or "Australia",
        role="SYSTEM_ADMIN",
        permissions=("operations.read", "operations.action.execute", "operations.action.verify", "operations.action.approve"),
        correlation_id=os.environ.get("NOVACODEPRO_WORKER_CORRELATION_ID") or "operations-worker",
        causation_id=os.environ.get("NOVACODEPRO_WORKER_CAUSATION_ID") or "operations-worker",
    )


def process_once(service: NCP008OperationsService, ctx: NCP008ExecutionContext) -> list[dict[str, Any]]:
    pending = [action for action in service.list_actions(ctx) if str(action.get("status") or "").lower() in {"approved"}]
    processed: list[dict[str, Any]] = []
    for action in pending:
        execution = service.execute_action(action["id"], ctx)
        verification = service.verify_action(action["id"], ctx)
        processed.append({"action_id": action["id"], "execution": execution, "verification": verification})
    return processed


def main(argv: list[str] | None = None) -> int:
    _ = argv or sys.argv[1:]
    repository = _repository()
    service = NCP008OperationsService(repository)
    ctx = _context()
    dry_run = os.environ.get("NCP008_WORKER_EXECUTE_APPROVED_ACTIONS", "false").lower() not in {"1", "true", "yes"}
    pending = [action for action in service.list_actions(ctx) if str(action.get("status") or "").lower() in {"approved"}]
    print(f"NCP008 worker ready: pending_approved_actions={len(pending)} dry_run={dry_run}")
    if dry_run:
        return 0
    processed = process_once(service, ctx)
    print(f"NCP008 worker processed={len(processed)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

