"""Guard the AfriPro codex-style workspace governance chain."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "afritech/governance/adr/ADR-0021-afroprog-codex-workspace.yaml"
RULE = ROOT / "afritech/governance/rules/RULE-041-afroprog-workspace-boundary.yaml"
WORKSPACE = ROOT / "afritech/apps/afroprog/dashboard/workspace.py"
AI_SERVICE = ROOT / "afritech/apps/afroprog/chat/ai_service.py"
EXECUTION_ENGINE = ROOT / "afritech/apps/afroprog/editor/execution_engine.py"
API = ROOT / "afritech/api/afroprog_workspace_api.py"
UI = ROOT / "dashboard/src/App.jsx"


class AfroProgWorkspaceGuardError(RuntimeError):
    """Raised when the AfriPro workspace governance chain drifts."""


@dataclass(frozen=True)
class AfroProgWorkspaceGuardReport:
    adr_id: str
    rule_id: str
    workspace_mode: str
    proposal_only: bool
    governance_linked: bool

    @property
    def verified(self) -> bool:
        return (
            self.adr_id == "ADR-0021"
            and self.rule_id == "RULE-041"
            and self.workspace_mode == "codex_style"
            and self.proposal_only is True
            and self.governance_linked is True
        )


def validate() -> AfroProgWorkspaceGuardReport:
    adr_text = ADR.read_text(encoding="utf-8")
    rule_text = RULE.read_text(encoding="utf-8")
    workspace_text = WORKSPACE.read_text(encoding="utf-8")
    ai_service_text = AI_SERVICE.read_text(encoding="utf-8")
    execution_engine_text = EXECUTION_ENGINE.read_text(encoding="utf-8")
    api_text = API.read_text(encoding="utf-8")
    ui_text = UI.read_text(encoding="utf-8")

    if "id: ADR-0021" not in adr_text:
        raise AfroProgWorkspaceGuardError("ADR-0021 id mismatch")
    if "id: RULE-041" not in rule_text:
        raise AfroProgWorkspaceGuardError("RULE-041 id mismatch")

    for required in (
        "proposal-only developer workspace",
        "Django backend templates",
        "AfriProg to AfriProgramming governed handoff",
    ):
        if required not in adr_text:
            raise AfroProgWorkspaceGuardError(f"ADR-0021 decision missing: {required}")

    for required in (
        "AfriPro Dashboard",
        '"workspace_mode": "codex_style"',
        '"proposal_only": True',
        '"governance_linked": True',
    ):
        if required not in workspace_text:
            raise AfroProgWorkspaceGuardError(f"workspace drifted: {required}")

    for required in (
        "class PoultryHouse(models.Model)",
        "class Flock(models.Model)",
        "build_afriprog_to_afriprogramming_view",
        "generate_context_aware_proposal",
    ):
        if required not in ai_service_text:
            raise AfroProgWorkspaceGuardError(f"AI service drifted: {required}")

    for required in (
        '"mutation_allowed": False',
        '"next_step": "send_to_governance"',
    ):
        if required not in execution_engine_text:
            raise AfroProgWorkspaceGuardError(f"Execution preview drifted: {required}")

    for required in (
        "/v1/afroprog/dashboard",
        "/v1/afroprog/chat/prompts",
        "/v1/afroprog/projects",
        "/v1/afroprog/workspace",
    ):
        if required not in api_text:
            raise AfroProgWorkspaceGuardError(f"API surface drifted: {required}")

    for required in (
        "Project Explorer",
        "Chat / AI Assistant Panel",
        "Code Editor (Live Editing + Execution)",
        "Django Backend for AfriPro Chat + Dashboard",
    ):
        if required not in ui_text:
            raise AfroProgWorkspaceGuardError(f"UI surface drifted: {required}")

    report = AfroProgWorkspaceGuardReport(
        adr_id="ADR-0021",
        rule_id="RULE-041",
        workspace_mode="codex_style",
        proposal_only=True,
        governance_linked=True,
    )
    if not report.verified:
        raise AfroProgWorkspaceGuardError("AfriPro workspace governance verification failed")
    return report


def main() -> int:
    report = validate()
    print(
        "AFROPROG_WORKSPACE_GUARD: PASS "
        f"(adr={report.adr_id}, rule={report.rule_id}, mode={report.workspace_mode})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
