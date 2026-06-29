"""Central registry for cryptographic hash domain separators.

⚠️ Do not change these values without a protocol migration plan.
The strings are part of the wire protocol and must remain stable
across mobile, backend, and dashboard runtimes.
"""

from __future__ import annotations

from types import MappingProxyType


HASH_DOMAINS = MappingProxyType(
    {
        "PACKET": "packet",
        "SIGNATURE": "signature",
        "AGGREGATE": "aggregate",
        "VIOLATIONS": "violations",
        "CONSENSUS_ROOT": "consensus_root",
        "VALIDATOR_ROOT": "validator_root",
        "SEAL": "seal",
        "QR_PAYLOAD": "qr_payload",
        "SIGNED_PAYLOAD": "signed_payload",
        "PROOF_RECEIPT": "proof_receipt",
        "SIGNER_SET": "signer_set",
        "TRANSFER_REQUEST": "transfer_request",
        "TRANSFER_QUOTE": "transfer_quote",
        "TRANSFER_EVENT": "transfer_event",
        "TRANSFER_RECEIPT": "transfer_receipt",
        "LEDGER_ENTRY": "ledger_entry",
        "LEDGER_JOURNAL": "ledger_journal",
        "AUDIT_PACKAGE": "audit_package",
        "MERKLE_LEAF": "merkle_leaf",
        "MERKLE_ROOT": "merkle_root",
        "GLOBAL_LEDGER_ROOT": "global_ledger_root",
        "LEDGER_CHECKPOINT": "ledger_checkpoint",
        "RECONCILIATION_REPORT": "reconciliation_report",
        "OUTBOX": "outbox",
        "POLICY_DECISION": "policy_decision",
        "SNAPSHOT": "snapshot",
        "TRANSFER_FEATURES": "transfer_features",
        "TRANSFER_LIMITS": "transfer_limits",
        "TRANSFER_RAILS": "transfer_rails",
        "ZK_RECEIPT_HIDDEN": "zk_receipt_hidden",
        "ZK_RECEIPT_PUBLIC": "zk_receipt_public",
        "ZK_RECEIPT_COMMITMENT": "zk_receipt_commitment",
        "ZK_RECEIPT_PROOF": "zk_receipt_proof",
        "ZK_RECEIPT_ARTIFACT": "zk_receipt_artifact",
        "ZK_QR_PAYLOAD": "zk_qr_payload",
        "ZK_QR_BUNDLE": "zk_qr_bundle",
        "ONCHAIN_BUNDLE": "onchain_bundle",
    }
)

PROTOCOL_HASH_VERSION = "v1"
SIGNED_MESSAGE_PREFIX = "NOVATECH"

__all__ = ["HASH_DOMAINS", "PROTOCOL_HASH_VERSION", "SIGNED_MESSAGE_PREFIX"]
