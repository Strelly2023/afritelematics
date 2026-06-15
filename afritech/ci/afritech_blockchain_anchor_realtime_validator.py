"""CI validator for realtime blockchain anchor streaming and ADR hashing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/architecture/AFRITECH_ANCHOR_REALTIME_STREAM_AND_ADR_HASHING.md"
ADR = ROOT / "afritech/governance/adr/ADR-0046-realtime-anchor-streaming-and-adr-hashing.yaml"
RULE = ROOT / "afritech/governance/rules/RULE-066-realtime-anchor-streaming-and-adr-hashing.yaml"
BIND = ROOT / "afritech/governance/bindings/BIND-044-realtime-anchor-streaming-and-adr-hashing.yaml"
INDEXER = ROOT / "afritech/architecture/anchor_indexer.py"
API = ROOT / "afritech/api/architecture_proof_api.py"
ADR_HELPER = ROOT / "afritech/governance/adr_anchor.py"
EXPLORER_APP = ROOT / "anchor_explorer/src/App.jsx"
EXPLORER_STYLES = ROOT / "anchor_explorer/src/styles.css"

VALIDATOR_NAME = "afritech.ci.afritech_blockchain_anchor_realtime_validator"


@dataclass(frozen=True)
class BlockchainAnchorRealtimeValidatorReport:
    docs_present: bool
    adr_present: bool
    rule_present: bool
    binding_present: bool
    indexer_realtime_present: bool
    api_surface_present: bool
    adr_helper_present: bool
    explorer_present: bool
    stream_replay_present: bool
    contract_link_present: bool
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "adr_present": self.adr_present,
            "adr_helper_present": self.adr_helper_present,
            "api_surface_present": self.api_surface_present,
            "binding_present": self.binding_present,
            "contract_link_present": self.contract_link_present,
            "docs_present": self.docs_present,
            "explorer_present": self.explorer_present,
            "indexer_realtime_present": self.indexer_realtime_present,
            "rule_present": self.rule_present,
            "schema": "afritech.blockchain_anchor_realtime_validator_report.v1",
            "stream_replay_present": self.stream_replay_present,
            "verified": self.verified,
        }


def validate() -> BlockchainAnchorRealtimeValidatorReport:
    docs = DOC.exists() and "websocket" in DOC.read_text(encoding="utf-8")
    adr = ADR.exists() and "Realtime Anchor Streaming and ADR Hashing" in ADR.read_text(encoding="utf-8")
    rule = RULE.exists() and "Realtime Anchor Streaming and ADR Hashing Governance" in RULE.read_text(encoding="utf-8")
    binding = BIND.exists() and "realtime anchor streaming" in BIND.read_text(encoding="utf-8").lower()
    indexer_text = INDEXER.read_text(encoding="utf-8")
    api_text = API.read_text(encoding="utf-8")
    adr_helper_text = ADR_HELPER.read_text(encoding="utf-8")
    explorer_present = EXPLORER_APP.exists() and EXPLORER_STYLES.exists()
    indexer_realtime = all(
        marker in indexer_text
        for marker in (
            "AnchorStreamHub",
            "build_anchor_stream_snapshot",
            "build_cross_network_anchor_reconciliation",
            "resolve_chain_ws_url",
        )
    )
    api_surface = all(
        marker in api_text
        for marker in (
            "/public/architecture/anchors/stream/ws",
            "/public/architecture/anchors/stream/replay",
            "/public/architecture/anchors/reconciliation",
            "/public/architecture/anchors/reconciliation/resolution",
            "/public/architecture/anchors/mainnet-promotion-gate",
            "/public/architecture/anchors/explorer",
            "/public/architecture/evidence/policy",
            "/public/architecture/evidence/semantics",
            "/public/architecture/adr/{adr_id}/hash",
            "/public/architecture/adr/{adr_id}/preview",
            "/public/architecture/adr/{adr_id}/contract-link",
        )
    )
    adr_helper = all(
        marker in adr_helper_text
        for marker in (
            "hash_adr_artifact",
            "anchor_adr_to_chain",
            "build_adr_anchor_preview",
            "build_adr_contract_link_packet",
        )
    )
    stream_replay = (
        "build_anchor_stream_replay" in indexer_text
        and "build_anchor_stream_replay" in api_text
        and "stream_sequence" in indexer_text
        and "primary_transport" in indexer_text
        and "operator_backfill_only" in indexer_text
    )
    contract_link = (
        "build_adr_contract_link_packet" in adr_helper_text
        and "ADR_CONTRACT_LINK_PACKET" in adr_helper_text
        and "anchorProof(string,bytes32)" in adr_helper_text
        and "verifyAnchor(string,bytes32)" in adr_helper_text
        and "/public/architecture/adr/{adr_id}/contract-link" in api_text
    )
    explorer_text = (EXPLORER_APP.read_text(encoding="utf-8") if EXPLORER_APP.exists() else "")
    explorer_full = explorer_present and all(
        marker in explorer_text
        for marker in (
            "replayStream",
            "selectAnchor",
            "adrContractLink",
            "reconciliationRows",
            "mainnetGate",
            "evidencePolicy",
            "operationalSemantics",
        )
    )
    verified = all(
        (
            docs,
            adr,
            rule,
            binding,
            indexer_realtime,
            api_surface,
            adr_helper,
            explorer_full,
            stream_replay,
            contract_link,
        )
    )
    return BlockchainAnchorRealtimeValidatorReport(
        docs_present=docs,
        adr_present=adr,
        rule_present=rule,
        binding_present=binding,
        indexer_realtime_present=indexer_realtime,
        api_surface_present=api_surface,
        adr_helper_present=adr_helper,
        explorer_present=explorer_full,
        stream_replay_present=stream_replay,
        contract_link_present=contract_link,
        verified=verified,
    )


def format_summary(report: BlockchainAnchorRealtimeValidatorReport) -> str:
    status = "PASSED" if report.verified else "FAILED"
    return (
        f"{VALIDATOR_NAME} {status} | "
        f"adr={report.adr_present} rule={report.rule_present} binding={report.binding_present} "
        f"indexer={report.indexer_realtime_present} api={report.api_surface_present} "
        f"adr_helper={report.adr_helper_present} explorer={report.explorer_present} "
        f"replay={report.stream_replay_present} contract_link={report.contract_link_present}"
    )


def main() -> int:
    report = validate()
    print(format_summary(report))
    return 0 if report.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
