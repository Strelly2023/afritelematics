#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 - <<'PY'
import subprocess
from pathlib import Path
from afritech.novacodepro import DevelopmentExecutionContext, NovaCodeProNCP007Service, NovaCodeProRepository

repo_root = Path("var/novacodepro-development-worker-repo").resolve()
repo_root.mkdir(parents=True, exist_ok=True)
if not (repo_root / ".git").exists():
    (repo_root / "README.md").write_text("# Development worker smoke\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "ncp007@example.com"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "NCP007"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
else:
    head = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=repo_root, capture_output=True, text=True)
    if head.returncode != 0:
        if not (repo_root / "README.md").exists():
            (repo_root / "README.md").write_text("# Development worker smoke\n", encoding="utf-8")
        subprocess.run(["git", "config", "user.email", "ncp007@example.com"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "NCP007"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)

repo = NovaCodeProRepository(Path("var/novacodepro-development-worker.sqlite3"))
service = NovaCodeProNCP007Service(repo, repo_root=repo_root)
ctx = DevelopmentExecutionContext(
    actor_id="worker",
    tenant_id="novatech",
    organization_id="novatech",
    workspace_id=None,
    project_id=None,
    role="SERVICE_ACCOUNT",
    permissions=("development.workspace.read", "development.workspace.configure", "repository.read", "code.generate", "build.execute", "test.execute"),
    session_id="worker-session",
    correlation_id="corr-worker",
)
workspace = service.create_workspace({"name": "Worker Workspace", "description": "Development worker smoke"}, ctx)
workspace_ctx = DevelopmentExecutionContext(
    actor_id="worker",
    tenant_id="novatech",
    organization_id="novatech",
    workspace_id=workspace["id"],
    project_id=None,
    role="SERVICE_ACCOUNT",
    permissions=("development.workspace.read", "development.workspace.configure", "repository.read", "code.generate", "build.execute", "test.execute"),
    session_id="worker-session",
    correlation_id="corr-worker",
)
session = service.create_session(workspace["id"], {"objective": "worker smoke test"}, workspace_ctx)
task = service.create_task(session["id"], {"title": "Worker task", "task_type": "TEST"}, workspace_ctx)
request = service.create_generation_request(task["id"], {"instruction": "Create a worker smoke artifact", "target_files": ["README.md"]}, workspace_ctx)
change_set = service.get_change_set(request["change_set"]["id"], workspace_ctx)
print({"workspace": workspace["id"], "session": session["id"], "task": task["id"], "change_set": change_set["id"]})
PY
