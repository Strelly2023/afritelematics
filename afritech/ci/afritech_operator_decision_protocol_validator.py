"""Validate the operator decision protocol for ADR-0044."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
ADR_0044 = ROOT / "afritech/governance/adr/ADR-0044-operator-decision-protocol.yaml"
RULE_064 = ROOT / "afritech/governance/rules/RULE-064-operator-decision-protocol.yaml"
BIND_042 = ROOT / "afritech/governance/bindings/BIND-042-operator-decision-protocol.yaml"
ARCH_DOC = ROOT / "docs/architecture/AFRIOPERATOR_DECISION_PROTOCOL.md"
RUNBOOK = ROOT / "docs/operations/AFRITECH_OPERATOR_DECISION_PROTOCOL.md"
TLS_CUTOVER_DOC = ROOT / "docs/operations/AFRITECH_DOMAIN_TLS_CUTOVER.md"
ZERO_DOWNTIME_SCRIPT = ROOT / "scripts/deploy_production_zero_downtime.sh"
CADDY_TLS = ROOT / "deploy/production/Caddyfile.tls"
COMPOSE_TLS = ROOT / "deploy/production/docker-compose.production.tls.yml"

REQUIRED_TEXT = {
    ADR_0044: (
        "Operator Decision Protocol",
        "decision_surface",
        "zero-downtime deployment",
        "domain-based TLS cutover",
        "afritech.ci.afritech_operator_decision_protocol_validator",
    ),
    RULE_064: (
        "Operator Decision Protocol Governance",
        "Domain TLS cutover must use a domain-only Caddy configuration and not an IP-bound edge.",
        "afritech/tests/ci/test_afritech_operator_decision_protocol_validator.py",
    ),
    BIND_042: (
        "zero_downtime_deploy_script",
        "domain_tls_cutover_bundle",
        "scripts/deploy_production_zero_downtime.sh",
    ),
    ARCH_DOC: (
        "Operator Decision Protocol",
        "go",
        "rollback",
        "The TLS cutover uses a domain-only Caddy configuration",
    ),
    RUNBOOK: (
        "Decision Modes",
        "rollback",
        "Write the decision record into the operator log and preserve it as pilot evidence.",
    ),
    TLS_CUTOVER_DOC: (
        "Domain TLS Cutover",
        "Caddyfile.tls",
        "do not bind the edge to an IP address",
    ),
}


class AfriTechOperatorDecisionProtocolError(RuntimeError):
    """Raised when ADR-0044 operator decision protocol validation fails."""


@dataclass(frozen=True)
class AfriTechOperatorDecisionProtocolReport:
    adr_id: str
    rule_id: str
    binding_id: str
    zero_downtime_script: str
    tls_caddyfile: str
    tls_compose_file: str
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "adr_id": self.adr_id,
            "binding_id": self.binding_id,
            "rule_id": self.rule_id,
            "schema": "afritech.operator_decision_protocol_report.v1",
            "tls_caddyfile": self.tls_caddyfile,
            "tls_compose_file": self.tls_compose_file,
            "verified": self.verified,
            "zero_downtime_script": self.zero_downtime_script,
        }


def validate() -> AfriTechOperatorDecisionProtocolReport:
    adr = _load_yaml(ADR_0044)
    rule = _load_yaml(RULE_064)
    binding = _load_yaml(BIND_042)

    _validate_doc_texts()
    _validate_script()
    _validate_edge_bundle()

    report = AfriTechOperatorDecisionProtocolReport(
        adr_id=str(adr.get("id", "")),
        rule_id=str(rule.get("id", "")),
        binding_id=str(binding.get("id", "")),
        zero_downtime_script=str(ZERO_DOWNTIME_SCRIPT.relative_to(ROOT)),
        tls_caddyfile=str(CADDY_TLS.relative_to(ROOT)),
        tls_compose_file=str(COMPOSE_TLS.relative_to(ROOT)),
        verified=_is_verified(adr, rule, binding),
    )
    if not report.verified:
        raise AfriTechOperatorDecisionProtocolError("operator decision protocol report failed")
    return report


def _load_yaml(path: Path) -> dict[str, object]:
    if not path.exists():
        raise AfriTechOperatorDecisionProtocolError(f"missing required file: {path.relative_to(ROOT)}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AfriTechOperatorDecisionProtocolError(f"YAML root must be a mapping: {path.relative_to(ROOT)}")
    return payload


def _validate_doc_texts() -> None:
    for path, required_text in REQUIRED_TEXT.items():
        if not path.exists():
            raise AfriTechOperatorDecisionProtocolError(
                f"missing required artifact: {path.relative_to(ROOT)}"
            )
        text = path.read_text(encoding="utf-8")
        for needle in required_text:
            if needle not in text:
                raise AfriTechOperatorDecisionProtocolError(
                    f"{path.relative_to(ROOT)} missing required text: {needle}"
                )


def _validate_script() -> None:
    if not ZERO_DOWNTIME_SCRIPT.exists():
        raise AfriTechOperatorDecisionProtocolError("missing zero-downtime deploy script")
    text = ZERO_DOWNTIME_SCRIPT.read_text(encoding="utf-8")
    for needle in (
        "--compose-file",
        "--env-file",
        "caddy validate",
        "caddy reload",
        "Zero-downtime production deployment completed.",
    ):
        if needle not in text:
            raise AfriTechOperatorDecisionProtocolError(
                f"zero-downtime script missing required text: {needle}"
            )


def _validate_edge_bundle() -> None:
    if not CADDY_TLS.exists():
        raise AfriTechOperatorDecisionProtocolError("missing TLS Caddyfile")
    if not COMPOSE_TLS.exists():
        raise AfriTechOperatorDecisionProtocolError("missing TLS compose bundle")


def _is_verified(adr: dict[str, object], rule: dict[str, object], binding: dict[str, object]) -> bool:
    if adr.get("id") != "ADR-0044":
        return False
    if adr.get("status") != "ACCEPTED":
        return False
    if rule.get("id") != "RULE-064":
        return False
    if binding.get("id") != "BIND-042":
        return False
    authority_model = adr.get("authority_model")
    if not isinstance(authority_model, dict):
        return False
    if tuple(authority_model.get("chain", ())) != ("Constitution", "Deterministic Truth", "Replay", "Proof"):
        return False
    protocol = adr.get("operator_decision_protocol")
    if not isinstance(protocol, dict):
        return False
    if protocol.get("authoritative") is not False:
        return False
    if protocol.get("role") != "decision_surface":
        return False
    if set(protocol.get("decision_modes", ())) != {
        "go",
        "continue",
        "refine",
        "stop",
        "rollback",
        "escalate",
    }:
        return False
    if set(protocol.get("forbidden", ())) != {
        "operator_decision_as_truth_authority",
        "operator_decision_overrides_replay",
        "operator_decision_overrides_proof",
        "operator_decision_overrides_reconciliation",
        "operator_decision_overrides_dispatch",
        "operator_decision_overrides_settlement",
    }:
        return False
    return True


def format_summary(report: AfriTechOperatorDecisionProtocolReport) -> str:
    return "\n".join(
        (
            "AfriTech operator decision protocol validation PASSED",
            f"adr={report.adr_id} rule={report.rule_id} binding={report.binding_id}",
            f"script={report.zero_downtime_script}",
            f"tls_caddyfile={report.tls_caddyfile}",
            f"tls_compose_file={report.tls_compose_file}",
        )
    )


def main() -> int:
    try:
        report = validate()
    except AfriTechOperatorDecisionProtocolError as exc:
        print(f"AfriTech operator decision protocol validation FAILED: {exc}")
        return 1

    print(format_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
