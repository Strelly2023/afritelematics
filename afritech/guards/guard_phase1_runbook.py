"""Guard the Phase 1 setup runbook against documentation drift."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
RULE = ROOT / "afritech/governance/rules/RULE-001-phase1-runbook.yaml"


class Phase1RunbookGuardError(RuntimeError):
    """Raised when the Phase 1 runbook governance contract is violated."""


@dataclass(frozen=True)
class Phase1RunbookGuardReport:
    rule_id: str
    runbook_doc: str
    runner_script: str
    sqlite_path: str
    endpoints: tuple[str, ...]
    phase2_spec_present: bool

    @property
    def verified(self) -> bool:
        return (
            self.rule_id == "RULE-001"
            and self.runbook_doc == "docs/pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md"
            and self.runner_script == "scripts/run_phase1_setup.sh"
            and self.sqlite_path == "afriride_system/pilot_state.sqlite3"
            and self.endpoints
            == ("/health", "/docs", "/auth/token", "/passenger/request-ride")
            and self.phase2_spec_present is True
        )


def validate() -> Phase1RunbookGuardReport:
    rule = _load_yaml(RULE)
    if rule.get("id") != "RULE-001":
        raise Phase1RunbookGuardError("RULE-001 id mismatch")

    linked = _require_mapping(rule, "linked_artifacts")
    contract = _require_mapping(rule, "contract")
    setup_contract = _require_mapping(contract, "setup_contract")
    code_alignment = _require_mapping(contract, "code_alignment")
    authority_boundary = _require_mapping(contract, "authority_boundary")
    phase2_gate = _require_mapping(contract, "phase2_gate")

    runbook_path = ROOT / str(linked["runbook_doc"])
    runner_path = ROOT / str(linked["runner"])
    phase2_path = ROOT / str(linked["phase2_spec"])

    for path in (
        runbook_path,
        runner_path,
        phase2_path,
        ROOT / "afritech/tests/governance/test_phase1_runbook_governance_chain.py",
        ROOT / "afritech/tests/governance/test_afriride_phase2_migration_governance_spec_doc.py",
    ):
        if not path.exists():
            raise Phase1RunbookGuardError(f"missing governed artifact: {path}")

    runbook_text = runbook_path.read_text(encoding="utf-8")
    runner_text = runner_path.read_text(encoding="utf-8")
    main_text = _read("afriride_system/api/main.py")
    auth_text = _read("afriride_system/api/auth.py")
    dispatcher_text = _read("afriride_system/api/dispatcher_adapter.py")
    storage_text = _read("afriride_system/backend/storage.py")
    schema_text = _read("scripts/sql/afriride_postgres_schema_v1.sql")
    phase2_text = phase2_path.read_text(encoding="utf-8")

    boundary_phrase = str(authority_boundary["required_phrase"])
    if boundary_phrase not in runbook_text:
        raise Phase1RunbookGuardError("runbook authority boundary mismatch")

    for forbidden in authority_boundary.get("forbidden_claims", ()):
        if str(forbidden) not in runbook_text.lower():
            raise Phase1RunbookGuardError(f"runbook missing non-claim boundary: {forbidden}")

    endpoints = tuple(str(item) for item in code_alignment.get("required_http_surfaces", ()))
    for endpoint in endpoints:
        if endpoint not in runbook_text:
            raise Phase1RunbookGuardError(f"runbook missing endpoint: {endpoint}")

    if "/health" not in main_text or "/docs" not in runbook_text:
        raise Phase1RunbookGuardError("health/docs surface mismatch")
    if 'prefix="/auth"' not in auth_text or '"/token"' not in auth_text:
        raise Phase1RunbookGuardError("auth route mismatch")
    if "/passenger/request-ride" not in runbook_text:
        raise Phase1RunbookGuardError("request ride route mismatch")

    sqlite_path = str(code_alignment["default_sqlite_path"])
    if sqlite_path not in runbook_text:
        raise Phase1RunbookGuardError("runbook sqlite path mismatch")
    if "pilot_state.sqlite3" not in storage_text:
        raise Phase1RunbookGuardError("storage default sqlite path missing")

    if "AFRIRIDE_DATABASE_URL" not in dispatcher_text or "AFRIRIDE_DB_PATH" not in dispatcher_text:
        raise Phase1RunbookGuardError("dispatcher adapter env contract mismatch")

    for table in (
        "trace_events",
        "idempotency_records",
        "replay_snapshots",
        "evidence_records",
        "receipt_records",
    ):
        if table not in runbook_text or table not in schema_text:
            raise Phase1RunbookGuardError(f"schema contract drifted for table: {table}")

    for command in setup_contract.get("required_commands", ()):
        command_text = str(command)
        if command_text not in runbook_text:
            raise Phase1RunbookGuardError(f"runbook missing command: {command_text}")
        if command_text.splitlines()[0].split()[0] not in runner_text:
            # Guard on the surface capability, not exact shell block duplication.
            raise Phase1RunbookGuardError(f"runner missing command surface for: {command_text}")

    for env_name in setup_contract.get("required_env_vars", ()):
        if str(env_name) not in runbook_text or str(env_name) not in runner_text:
            raise Phase1RunbookGuardError(f"env contract mismatch: {env_name}")

    for test_path in setup_contract.get("required_phase1_tests", ()):
        if str(test_path) not in runbook_text:
            raise Phase1RunbookGuardError(f"runbook missing test reference: {test_path}")

    for forward_link in phase2_gate.get("required_forward_links", ()):
        if str(forward_link) not in runbook_text:
            raise Phase1RunbookGuardError(f"runbook missing forward link: {forward_link}")

    for phrase in (
        "Status: PHASE 2 MIGRATION GOVERNANCE SPEC",
        "migration must preserve replay, evidence, and receipt equivalence",
        "replay diff must report",
        "This specification is not migration success evidence.",
    ):
        if phrase not in phase2_text:
            raise Phase1RunbookGuardError(f"phase2 governance spec incomplete: {phrase}")

    report = Phase1RunbookGuardReport(
        rule_id=str(rule["id"]),
        runbook_doc=str(linked["runbook_doc"]),
        runner_script=str(linked["runner"]),
        sqlite_path=sqlite_path,
        endpoints=endpoints,
        phase2_spec_present=True,
    )
    if not report.verified:
        raise Phase1RunbookGuardError("Phase 1 runbook guard report failed")
    return report


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Phase1RunbookGuardError(f"{path} must contain a mapping")
    return payload


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise Phase1RunbookGuardError(f"{key} must be a mapping")
    return value


def _read(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        raise Phase1RunbookGuardError(f"missing source file: {relative_path}")
    return path.read_text(encoding="utf-8")


def main() -> int:
    report = validate()
    print(
        "PHASE1_RUNBOOK_GUARD: PASS "
        f"(rule={report.rule_id}, runbook={report.runbook_doc}, phase2_spec={report.phase2_spec_present})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
