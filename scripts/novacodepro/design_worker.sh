#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 - <<'PY'
from pathlib import Path
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository
from afritech.novacodepro.ncp006b import DesignExecutionContext, NovaCodeProNCP006BService

repo = NovaCodeProRepository(Path("var/novacodepro-design-worker.sqlite3"))
service = NovaCodeProNCP006BService(repo)
ctx = DesignExecutionContext(
    actor_id="worker",
    tenant_id="novatech",
    organization_id="novatech",
    workspace_id="design-workspace-default",
    project_id="design-project-default",
    request_id="request-design-default",
    role="ADMIN",
    permissions=("design.read", "design.create", "design.update", "design.validate", "design.baseline"),
    session_id="worker-session",
    correlation_id="corr-worker",
    causation_id="corr-worker",
)
service.validate_artifact("design_token", service.create_resource("design_token", {"name": "token.worker", "path": "token.worker", "category": "COLOR", "level": "SEMANTIC", "value": "#111111"}, ctx)["id"], ctx)
print("design worker smoke test passed")
PY
