"""Standalone verifier for authority-bound AfriRide proof packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from afriride_system.backend.authority_runtime import (
    VERIFIER_VERSION,
    assert_consistent_authority_hashes,
    assert_protocol_version_compatible,
    authority_hash,
    execution_fingerprint,
    load_authority_snapshot,
)
from afriride_system.backend.evidence_engine import EvidenceEngine
from afriride_system.backend.receipt_engine import ReceiptEngine
from afriride_system.backend.replay_engine import ReplayEngine
from afriride_system.backend.trace_enforcement import trace_event_from_payload


class VerificationError(RuntimeError):
    """Raised when a proof packet fails verification."""


def _normalized_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized.pop("generated_at", None)
    return normalized


def _normalized_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized.pop("issued_at", None)
    return normalized


def load_packet(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise VerificationError("proof packet must be a JSON object")
    return payload


def verify_packet(payload: dict[str, Any]) -> dict[str, Any]:
    ride_id = str(payload["ride_id"])
    events = tuple(trace_event_from_payload(event) for event in payload["events"])
    authority_input = payload["authority"]
    try:
        compatibility = assert_protocol_version_compatible(
            protocol_version=str(authority_input["doc_version"]),
            verifier_version=VERIFIER_VERSION,
        )
    except RuntimeError as exc:
        raise VerificationError(str(exc)) from exc

    digest = authority_hash(
        doc_id=str(authority_input["doc_id"]),
        doc_version=str(authority_input["doc_version"]),
        governed_invariants=tuple(authority_input["governed_invariants"]),
    )
    if digest != authority_input["authority_hash"]:
        raise VerificationError("authority_hash mismatch")

    snapshot = load_authority_snapshot(digest)
    if snapshot.get("doc_version") != authority_input["doc_version"]:
        raise VerificationError("authority snapshot version mismatch")

    replay = ReplayEngine().replay(ride_id, events)
    evidence = EvidenceEngine().derive(ride_id, events)
    receipt = ReceiptEngine().derive(ride_id, events)

    assert_consistent_authority_hashes(
        authority=digest,
        replay=replay.canonical_dict()["authority"]["authority_hash"],
        evidence=evidence.canonical_dict()["authority"]["authority_hash"],
        receipt=receipt.canonical_dict()["authority"]["authority_hash"],
    )

    if replay.canonical_dict() != payload["replay"]:
        raise VerificationError("replay mismatch")
    if _normalized_evidence(evidence.canonical_dict()) != _normalized_evidence(payload["evidence"]):
        raise VerificationError("evidence mismatch")
    if _normalized_receipt(receipt.canonical_dict()) != _normalized_receipt(payload["receipt"]):
        raise VerificationError("receipt mismatch")

    fingerprint = execution_fingerprint(
        replay_hash=replay.replay_hash,
        receipt_hash=receipt.receipt_hash,
        authority_hash=digest,
    )
    return {
        "valid": True,
        "authority_verified": True,
        "execution_verified": True,
        "verifier_version": VERIFIER_VERSION,
        "compatibility": compatibility,
        "authority_hash": digest,
        "authority_snapshot": snapshot,
        "execution_fingerprint": fingerprint,
    }


def verify_packet_file(path: str | Path) -> dict[str, Any]:
    result = verify_packet(load_packet(path))
    result["packet_path"] = str(Path(path))
    return result


def render_verification_report(result: dict[str, Any]) -> str:
    compatibility = result.get("compatibility", {})
    status = "VALID" if result.get("valid") else "INVALID"
    return "\n".join(
        (
            f"AfriTech Public Verifier: {status}",
            f"verifier_version: {result.get('verifier_version', VERIFIER_VERSION)}",
            f"protocol_version: {compatibility.get('protocol_version', 'unknown')}",
            f"compatibility_status: {compatibility.get('status', 'unknown')}",
            f"authority_hash: {result.get('authority_hash', '')}",
            f"execution_fingerprint: {result.get('execution_fingerprint', '')}",
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = argv or []
    output_format = "json"
    report_path: Path | None = None
    packet_path: str | None = None
    index = 0
    while index < len(args):
        current = args[index]
        if current == "--format":
            index += 1
            if index >= len(args):
                raise SystemExit("--format requires json or text")
            output_format = args[index]
            if output_format not in {"json", "text"}:
                raise SystemExit("--format must be json or text")
        elif current == "--write-report":
            index += 1
            if index >= len(args):
                raise SystemExit("--write-report requires a path")
            report_path = Path(args[index])
        elif packet_path is None:
            packet_path = current
        else:
            raise SystemExit(
                "usage: python -m afritech.verify.verify_proof "
                "[--format json|text] [--write-report path] <packet.json>"
            )
        index += 1
    if packet_path is None:
        raise SystemExit(
            "usage: python -m afritech.verify.verify_proof "
            "[--format json|text] [--write-report path] <packet.json>"
        )

    result = verify_packet_file(packet_path)
    rendered = (
        json.dumps(result, sort_keys=True)
        if output_format == "json"
        else render_verification_report(result)
    )
    if report_path is not None:
        report_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
