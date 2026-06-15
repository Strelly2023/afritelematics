"""CI validator for the governed evidence operating protocol."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/protocol/AFRITECH_GOVERNED_EVIDENCE_PROTOCOL.md"
ADR = ROOT / "afritech/governance/adr/ADR-0047-governed-evidence-operating-protocol.yaml"
RULE = ROOT / "afritech/governance/rules/RULE-067-governed-evidence-operating-protocol.yaml"
BIND = ROOT / "afritech/governance/bindings/BIND-045-governed-evidence-operating-protocol.yaml"
INDEXER = ROOT / "afritech/architecture/anchor_indexer.py"
API = ROOT / "afritech/api/architecture_proof_api.py"
EXPLORER_APP = ROOT / "anchor_explorer/src/App.jsx"

VALIDATOR_NAME = "afritech.ci.afritech_governed_evidence_protocol_validator"


@dataclass(frozen=True)
class GovernedEvidenceProtocolValidatorReport:
    docs_present: bool
    adr_present: bool
    rule_present: bool
    binding_present: bool
    protocol_builder_present: bool
    api_surface_present: bool
    explorer_present: bool
    governance_hashes_present: bool
    validator_chain_present: bool
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "adr_present": self.adr_present,
            "api_surface_present": self.api_surface_present,
            "binding_present": self.binding_present,
            "docs_present": self.docs_present,
            "explorer_present": self.explorer_present,
            "governance_hashes_present": self.governance_hashes_present,
            "protocol_builder_present": self.protocol_builder_present,
            "rule_present": self.rule_present,
            "schema": "afritech.governed_evidence_protocol_validator_report.v1",
            "validator_chain_present": self.validator_chain_present,
            "verified": self.verified,
        }


def validate() -> GovernedEvidenceProtocolValidatorReport:
    doc_text = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    adr_text = ADR.read_text(encoding="utf-8") if ADR.exists() else ""
    rule_text = RULE.read_text(encoding="utf-8") if RULE.exists() else ""
    bind_text = BIND.read_text(encoding="utf-8") if BIND.exists() else ""
    indexer_text = INDEXER.read_text(encoding="utf-8")
    api_text = API.read_text(encoding="utf-8")
    explorer_text = EXPLORER_APP.read_text(encoding="utf-8") if EXPLORER_APP.exists() else ""

    docs = DOC.exists() and "GOVERNED_EVIDENCE_OPERATING_PROTOCOL" in doc_text
    adr = ADR.exists() and "Governed Evidence Operating Protocol" in adr_text
    rule = RULE.exists() and "Governed Evidence Operating Protocol Governance" in rule_text
    binding = BIND.exists() and "BIND-045" in bind_text and "RULE-067" in bind_text
    protocol_builder = all(
        marker in indexer_text
        for marker in (
            "GOVERNED_EVIDENCE_PROTOCOL_VERSION",
            "GOVERNED_EVIDENCE_GOVERNANCE_ARTIFACTS",
            "build_governed_evidence_protocol",
            "GOVERNED_EVIDENCE_OPERATING_PROTOCOL",
            "protocol_hash",
            "semantics_hash",
            "policy_hash",
        )
    )
    api_surface = all(
        marker in api_text
        for marker in (
            "build_governed_evidence_protocol",
            "/public/architecture/evidence/protocol",
            "governed_protocol",
        )
    )
    explorer = all(
        marker in explorer_text
        for marker in (
            "governedProtocol",
            "/public/architecture/evidence/protocol",
            "Evidence protocol",
            "protocol_hash",
        )
    )
    governance_hashes = all(
        marker in indexer_text
        for marker in (
            "ADR-0047",
            "RULE-067",
            "BIND-045",
            "_file_sha256",
            "governance_artifacts",
        )
    )
    validator_chain = all(
        marker in indexer_text
        for marker in (
            "afritech.ci.afritech_blockchain_anchor_validator",
            "afritech.ci.afritech_blockchain_anchor_realtime_validator",
            "afritech.ci.afritech_governed_evidence_protocol_validator",
        )
    )
    verified = all(
        (
            docs,
            adr,
            rule,
            binding,
            protocol_builder,
            api_surface,
            explorer,
            governance_hashes,
            validator_chain,
        )
    )
    return GovernedEvidenceProtocolValidatorReport(
        docs_present=docs,
        adr_present=adr,
        rule_present=rule,
        binding_present=binding,
        protocol_builder_present=protocol_builder,
        api_surface_present=api_surface,
        explorer_present=explorer,
        governance_hashes_present=governance_hashes,
        validator_chain_present=validator_chain,
        verified=verified,
    )


def format_summary(report: GovernedEvidenceProtocolValidatorReport) -> str:
    status = "PASSED" if report.verified else "FAILED"
    return (
        f"{VALIDATOR_NAME} {status} | "
        f"adr={report.adr_present} rule={report.rule_present} binding={report.binding_present} "
        f"docs={report.docs_present} builder={report.protocol_builder_present} "
        f"api={report.api_surface_present} explorer={report.explorer_present} "
        f"governance_hashes={report.governance_hashes_present} "
        f"validators={report.validator_chain_present}"
    )


def main() -> int:
    report = validate()
    print(format_summary(report))
    return 0 if report.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
