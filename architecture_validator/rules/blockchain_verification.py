from __future__ import annotations

from pathlib import Path

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import read_text


def check_blockchain_verification(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []

    contract_path = str(config.get("anchor_v2_contract_path") or "")
    abi_path = str(config.get("anchor_v2_abi_path") or "")
    client_path = str(config.get("anchor_v2_client_path") or "")

    if contract_path:
        if not Path(contract_path).exists():
            issues.append(f"Missing ArchitectureAnchorV2 contract: {contract_path}")
        else:
            source = read_text(contract_path)
            for fragment in ("contract ArchitectureAnchorV2", "anchorBatch", "verifyAnchor"):
                if fragment not in source:
                    issues.append(f"ArchitectureAnchorV2 source missing fragment: {fragment}")

    if abi_path:
        if not Path(abi_path).exists():
            issues.append(f"Missing ArchitectureAnchorV2 ABI: {abi_path}")
        else:
            abi_source = read_text(abi_path)
            for fragment in ("ARCHITECTURE_ANCHOR_V2_ABI", '"verifyAnchor"', '"anchorBatch"'):
                if fragment not in abi_source:
                    issues.append(f"ArchitectureAnchorV2 ABI missing fragment: {fragment}")

    if client_path:
        if not Path(client_path).exists():
            issues.append(f"Missing ArchitectureAnchorV2 client: {client_path}")
        else:
            client_source = read_text(client_path)
            for fragment in ("verify_anchor_v2_on_chain", "get_anchor_v2", "anchor_batch_v2_on_chain"):
                if fragment not in client_source:
                    issues.append(f"ArchitectureAnchorV2 client missing fragment: {fragment}")

    if str(config.get("blockchain_live_verification") or "disabled").lower() == "enabled":
        issues.append(
            "Live blockchain verification is enabled but no CI-safe proof list is configured"
        )

    return pass_or_fail("Blockchain Proof Verification", issues)
