"""Guard the runtime-boundary governance chain and generated artifacts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import yaml

from afritech.architecture.full_architecture_graph import generate_architecture_graph
from afritech.ci.runtime_boundary_validator import build_report, coerce_boundary_report


ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "afritech/governance/adr/ADR-0022-runtime-boundary-governance-activation.yaml"
RULE = ROOT / "afritech/governance/rules/RULE-042-runtime-boundary-governance.yaml"
BIND = ROOT / "afritech/governance/bindings/BIND-021-runtime-boundary-governance.yaml"
WORKFLOW = ROOT / ".github/workflows/architecture.yml"
PIPELINE = ROOT / "afritech/ci/constitutional_pipeline.py"
SCAN_REPORT = ROOT / "docs/reviews/AFRITECH_RUNTIME_BOUNDARY_SCAN.md"
GRAPH_REPORT = ROOT / "docs/architecture/AFRITECH_FULL_ARCHITECTURE_GRAPH.md"


class RuntimeBoundaryGovernanceGuardError(RuntimeError):
    """Raised when runtime-boundary governance drifts."""


@dataclass(frozen=True)
class RuntimeBoundaryGovernanceReport:
    adr_id: str
    rule_id: str
    bind_id: str
    validator_clean: bool
    scan_current: bool
    graph_current: bool
    workflow_enforced: bool
    optimization_active: bool

    @property
    def verified(self) -> bool:
        return (
            self.adr_id == "ADR-0022"
            and self.rule_id == "RULE-042"
            and self.bind_id == "BIND-021"
            and self.validator_clean is True
            and self.scan_current is True
            and self.graph_current is True
            and self.workflow_enforced is True
            and self.optimization_active is True
        )


def validate(*, write_artifacts: bool = False) -> RuntimeBoundaryGovernanceReport:
    adr = _load_yaml(ADR)
    rule = _load_yaml(RULE)
    bind = _load_yaml(BIND)

    if _yaml_id(adr, "adr") != "ADR-0022":
        raise RuntimeBoundaryGovernanceGuardError("ADR-0022 id mismatch")
    if rule.get("id") != "RULE-042":
        raise RuntimeBoundaryGovernanceGuardError("RULE-042 id mismatch")
    if bind.get("id") != "BIND-021":
        raise RuntimeBoundaryGovernanceGuardError("BIND-021 id mismatch")

    adr_text = ADR.read_text(encoding="utf-8")
    rule_text = RULE.read_text(encoding="utf-8")
    bind_text = BIND.read_text(encoding="utf-8")
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    pipeline_text = PIPELINE.read_text(encoding="utf-8")

    for required in (
        "runtime boundary validator",
        "full architecture graph",
        "CI must run the governance guard",
    ):
        if required not in adr_text:
            raise RuntimeBoundaryGovernanceGuardError(f"ADR-0022 incomplete: {required}")

    for required in (
        "docs/reviews/AFRITECH_RUNTIME_BOUNDARY_SCAN.md",
        "docs/architecture/AFRITECH_FULL_ARCHITECTURE_GRAPH.md",
        "upload-artifact",
    ):
        if required not in rule_text:
            raise RuntimeBoundaryGovernanceGuardError(f"RULE-042 incomplete: {required}")

    for required in (
        "afritech.ci.runtime_boundary_validator",
        "afritech.architecture.full_architecture_graph",
        "afritech.guards.guard_runtime_boundary_governance",
    ):
        if required not in bind_text:
            raise RuntimeBoundaryGovernanceGuardError(f"BIND-021 incomplete: {required}")

    report = coerce_boundary_report(build_report())
    if report.violations:
        raise RuntimeBoundaryGovernanceGuardError(
            f"runtime boundary violations detected: {len(report.violations)}"
        )
    expected_scan = report.to_markdown()
    expected_graph = generate_architecture_graph()

    if write_artifacts:
        SCAN_REPORT.write_text(expected_scan, encoding="utf-8")
        GRAPH_REPORT.write_text(expected_graph, encoding="utf-8")

    actual_scan = SCAN_REPORT.read_text(encoding="utf-8")
    actual_graph = GRAPH_REPORT.read_text(encoding="utf-8")

    scan_current = actual_scan == expected_scan
    graph_current = actual_graph == expected_graph
    if not scan_current:
        raise RuntimeBoundaryGovernanceGuardError("runtime boundary scan artifact drift detected")
    if not graph_current:
        raise RuntimeBoundaryGovernanceGuardError("full architecture graph drift detected")

    required_workflow_strings = (
        "python -m afritech.guards.guard_runtime_boundary_governance --fail-on-drift",
        "docs/reviews/AFRITECH_RUNTIME_BOUNDARY_SCAN.md",
        "docs/architecture/AFRITECH_FULL_ARCHITECTURE_GRAPH.md",
        "upload-artifact",
    )
    workflow_enforced = all(item in workflow_text for item in required_workflow_strings)
    if not workflow_enforced:
        raise RuntimeBoundaryGovernanceGuardError("architecture workflow missing governance activation")

    optimization_active = (
        "guard_runtime_boundary_governance" in pipeline_text
        and "AFRITECH_FULL_ARCHITECTURE_GRAPH" in workflow_text
        and "AFRITECH_RUNTIME_BOUNDARY_SCAN" in workflow_text
    )
    if not optimization_active:
        raise RuntimeBoundaryGovernanceGuardError("optimization layer not active")

    governance_report = RuntimeBoundaryGovernanceReport(
        adr_id="ADR-0022",
        rule_id="RULE-042",
        bind_id="BIND-021",
        validator_clean=True,
        scan_current=scan_current,
        graph_current=graph_current,
        workflow_enforced=workflow_enforced,
        optimization_active=optimization_active,
    )
    if not governance_report.verified:
        raise RuntimeBoundaryGovernanceGuardError("runtime boundary governance verification failed")
    return governance_report


def _load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeBoundaryGovernanceGuardError(f"{path} must contain a mapping")
    return payload


def _yaml_id(payload: dict, top_key: str) -> str | None:
    node = payload.get(top_key)
    if isinstance(node, dict):
        value = node.get("id")
        return str(value) if value is not None else None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifacts", action="store_true")
    parser.add_argument("--fail-on-drift", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = validate(write_artifacts=args.write_artifacts)
    except RuntimeBoundaryGovernanceGuardError:
        if args.fail_on_drift:
            raise
        raise

    print(
        "RUNTIME_BOUNDARY_GOVERNANCE_GUARD: PASS "
        f"(adr={report.adr_id}, rule={report.rule_id}, bind={report.bind_id}, "
        f"scan_current={report.scan_current}, graph_current={report.graph_current})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
