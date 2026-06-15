"""CI validator for the AfriTech blockchain architecture anchor system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/architecture/AFRITECH_BLOCKCHAIN_ARCHITECTURE_MAP.md"
ADR = ROOT / "afritech/governance/adr/ADR-0045-blockchain-architecture-anchor-system.yaml"
RULE = ROOT / "afritech/governance/rules/RULE-065-blockchain-architecture-anchor-system.yaml"
BIND = ROOT / "afritech/governance/bindings/BIND-043-blockchain-architecture-anchor-system.yaml"
API = ROOT / "afritech/api/architecture_proof_api.py"
INDEXER = ROOT / "afritech/architecture/anchor_indexer.py"
CHAIN = ROOT / "afritech/architecture/blockchain_anchor.py"
DEPLOYMENT = ROOT / "afritech/chain/contracts/deployment_config.py"

VALIDATOR_NAME = "afritech.ci.afritech_blockchain_anchor_validator"


@dataclass(frozen=True)
class BlockchainAnchorValidatorReport:
    docs_present: bool
    adr_present: bool
    rule_present: bool
    binding_present: bool
    api_surface_present: bool
    indexer_persistence_present: bool
    event_subscription_present: bool
    reconciliation_engine_present: bool
    evidence_policy_present: bool
    operational_semantics_present: bool
    mainnet_gate_present: bool
    multi_network_present: bool
    etherscan_packet_present: bool
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "adr_present": self.adr_present,
            "api_surface_present": self.api_surface_present,
            "binding_present": self.binding_present,
            "docs_present": self.docs_present,
            "event_subscription_present": self.event_subscription_present,
            "etherscan_packet_present": self.etherscan_packet_present,
            "evidence_policy_present": self.evidence_policy_present,
            "indexer_persistence_present": self.indexer_persistence_present,
            "mainnet_gate_present": self.mainnet_gate_present,
            "multi_network_present": self.multi_network_present,
            "operational_semantics_present": self.operational_semantics_present,
            "reconciliation_engine_present": self.reconciliation_engine_present,
            "rule_present": self.rule_present,
            "schema": "afritech.blockchain_anchor_validator_report.v1",
            "verified": self.verified,
        }


def validate() -> BlockchainAnchorValidatorReport:
    docs = DOC.exists()
    adr = ADR.exists() and "Blockchain Architecture Anchor System" in ADR.read_text(encoding="utf-8")
    rule = RULE.exists() and "Blockchain Architecture Anchor System Governance" in RULE.read_text(encoding="utf-8")
    binding = BIND.exists() and "blockchain anchor API" in BIND.read_text(encoding="utf-8")
    api_text = API.read_text(encoding="utf-8")
    indexer_text = INDEXER.read_text(encoding="utf-8")
    chain_text = CHAIN.read_text(encoding="utf-8")
    deployment_text = DEPLOYMENT.read_text(encoding="utf-8")
    api_surface = all(
        marker in api_text
        for marker in (
            "/public/architecture/anchors",
            "/public/architecture/anchors/status",
            "/public/architecture/anchors/dashboard",
            "/public/architecture/anchors/verification",
            "/public/architecture/anchors/stream/status",
        )
    )
    indexer_persistence = all(
        marker in indexer_text
        for marker in (
            "JsonFileAnchorIndexBackend",
            "RedisAnchorIndexBackend",
            "PostgresAnchorIndexBackend",
            "AnchorIndexStore",
        )
    )
    event_subscription = all(
        marker in indexer_text
        for marker in (
            "AnchorChainEventSubscriber",
            "poll_once",
            "poll_all",
            "build_anchor_stream_replay",
        )
    )
    reconciliation_engine = all(
        marker in indexer_text
        for marker in (
            "_entry_key_from_parts",
            "EVIDENCE_CONSISTENCY_INVARIANTS",
            "CONFLICT_RESOLUTION_STRATEGIES",
            "observed_networks",
            "missing_networks",
            "reconciliation_status",
            "conflicts",
            "resolution_strategy",
        )
    )
    evidence_policy = (
        "build_evidence_consistency_policy" in indexer_text
        and "build_evidence_consistency_policy" in api_text
        and "BLOCKCHAIN_EVIDENCE_CONSISTENCY_POLICY" in indexer_text
    )
    operational_semantics = (
        "build_evidence_operational_semantics" in indexer_text
        and "build_evidence_operational_semantics" in api_text
        and "BLOCKCHAIN_EVIDENCE_OPERATIONAL_SEMANTICS" in indexer_text
        and "EVIDENCE_OPERATIONAL_TRANSITIONS" in indexer_text
        and "/public/architecture/evidence/semantics" in api_text
    )
    mainnet_gate = (
        "build_mainnet_promotion_gate" in indexer_text
        and "build_mainnet_promotion_gate" in api_text
        and "BLOCKCHAIN_MAINNET_PROMOTION_GATE" in indexer_text
    )
    multi_network = all(
        marker in chain_text and marker in deployment_text
        for marker in (
            "base-sepolia",
            "sepolia",
            "mainnet",
        )
    )
    etherscan_packet = all(
        marker in api_text
        for marker in (
            "/public/architecture/anchors/verification/abi",
            "/public/architecture/anchors/verification/source",
            "build_etherscan_contract_verification_report",
        )
    )
    verified = all(
        (
            docs,
            adr,
            rule,
            binding,
            api_surface,
            indexer_persistence,
            event_subscription,
            reconciliation_engine,
            evidence_policy,
            operational_semantics,
            mainnet_gate,
            multi_network,
            etherscan_packet,
        )
    )
    return BlockchainAnchorValidatorReport(
        docs_present=docs,
        adr_present=adr,
        rule_present=rule,
        binding_present=binding,
        api_surface_present=api_surface,
        indexer_persistence_present=indexer_persistence,
        event_subscription_present=event_subscription,
        reconciliation_engine_present=reconciliation_engine,
        evidence_policy_present=evidence_policy,
        operational_semantics_present=operational_semantics,
        mainnet_gate_present=mainnet_gate,
        multi_network_present=multi_network,
        etherscan_packet_present=etherscan_packet,
        verified=verified,
    )


def format_summary(report: BlockchainAnchorValidatorReport) -> str:
    status = "PASSED" if report.verified else "FAILED"
    return (
        f"{VALIDATOR_NAME} {status} | "
        f"adr={report.adr_present} rule={report.rule_present} binding={report.binding_present} "
        f"indexer={report.indexer_persistence_present} stream={report.event_subscription_present} "
        f"reconciliation={report.reconciliation_engine_present} "
        f"policy={report.evidence_policy_present} semantics={report.operational_semantics_present} "
        f"mainnet_gate={report.mainnet_gate_present} "
        f"multi_network={report.multi_network_present} etherscan={report.etherscan_packet_present}"
    )


def main() -> int:
    report = validate()
    print(format_summary(report))
    return 0 if report.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
