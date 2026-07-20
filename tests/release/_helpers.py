from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable, TypeVar

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config/release.json"
DOC_PATH = ROOT / "docs/release/ENTERPRISE_RELEASE_FRAMEWORK_2026.md"
MOBILE_STATE_PATH = ROOT / "docs/mobile/release/novatech_release_state.json"
PRR_PATH = ROOT / "docs/prr/PRR-001-production-readiness-review.yaml"
ADR_PATH = ROOT / "adr/ADR-0024-release-governance.yaml"
INVARIANT_PATH = ROOT / "afritech/constitution/INVARIANT-016-release-stage.yaml"
RULE_PATH = ROOT / "afritech/governance/rules/RULE-073-release-transition.yaml"
BINDING_PATH = ROOT / "afritech/governance/bindings/BIND-051-release-domains.yaml"
RELEASE_STAGE_SOURCE = ROOT / "packages/novatech-platform-sdk/src/release/releaseStage.ts"
ACTIVATION_SOURCE = ROOT / "packages/novatech-platform-sdk/src/activation/activationGate.ts"
READINESS_SOURCE = ROOT / "packages/novatech-platform-sdk/src/readiness/readinessDomains.ts"
PRR_VALIDATOR_SOURCE = ROOT / "packages/novatech-platform-sdk/src/prr/prrValidator.ts"
GA_GUARD_SOURCE = ROOT / "afritech/guards/guard_ga_enablement.py"

T = TypeVar("T")


def read_json(path: Path | str):
    return json.loads((ROOT / path if isinstance(path, str) else path).read_text(encoding="utf-8"))


def read_text(path: Path | str) -> str:
    return (ROOT / path if isinstance(path, str) else path).read_text(encoding="utf-8")


def run_in_detached_worktree(callback: Callable[[Path], T]) -> T:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    worktree_dir = Path(tempfile.mkdtemp(prefix="release-tests-", dir="/private/tmp"))
    try:
        subprocess.run(["git", "worktree", "add", "--detach", str(worktree_dir), commit], cwd=ROOT, check=True, capture_output=True, text=True)
        return callback(worktree_dir)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree_dir)], cwd=ROOT, check=False, capture_output=True, text=True)
        shutil.rmtree(worktree_dir, ignore_errors=True)
