"""CLI for running a first external partner verification session."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any
from urllib import request

from afritech.sdk.external_verifier import ExternalVerifierClient


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _load_json(url: str) -> dict[str, Any]:
    with request.urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("remote payload must decode to a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Public base URL for the partner verification session")
    parser.add_argument("--partner", required=True, help="Partner or verifier name")
    parser.add_argument("--expect-network", default="sepolia", help="Expected publication network for this session")
    parser.add_argument("--report-out", help="Optional path to write the partner session report JSON")
    parser.add_argument("--notes", default="", help="Optional operator notes to attach to the report")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def build_partner_session_report(
    *,
    base_url: str,
    partner: str,
    expect_network: str,
    notes: str,
) -> dict[str, Any]:
    client = ExternalVerifierClient()
    normalized_base_url = _normalize_base_url(base_url)

    proof_payload = client.decode_architecture_proof_response(
        _load_json(f"{normalized_base_url}/public/architecture/proof")
    )
    proof_result = client.verify_architecture_proof_locally(proof_payload)
    anchor_id = str(proof_result["anchor_id"])

    chain_payload = client.decode_public_chain_receipt(
        _load_json(f"{normalized_base_url}/public/architecture/chain/{anchor_id}")
    )
    dashboard_payload = client.decode_public_trust_dashboard(
        _load_json(f"{normalized_base_url}/public/trust/dashboard")
    )
    demo_payload = client.decode_partner_demo_narrative(
        _load_json(f"{normalized_base_url}/public/demo/system-integrity")
    )

    live_publication = dashboard_payload.get("chain", {}).get("live_publication")
    live_status = None if not isinstance(live_publication, dict) else live_publication.get("status")
    network_match = chain_payload["chain_receipt"].get("network") == expect_network
    outcome = (
        "PASSED"
        if proof_result["verification_status"] == "VERIFIED"
        and chain_payload["status"] == "READY"
        and demo_payload.get("demo_readiness") == "PARTNER_READY"
        and network_match
        else "REVIEW_REQUIRED"
    )

    return {
        "classification": "EXTERNAL_PARTNER_VERIFICATION_SESSION",
        "session_id": f"partner-session-{anchor_id[:12]}",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "partner": partner,
        "base_url": normalized_base_url,
        "outcome": outcome,
        "verification": proof_result,
        "chain": {
            "status": chain_payload["status"],
            "network": chain_payload["chain_receipt"].get("network"),
            "transaction_hash": chain_payload["chain_receipt"].get("transaction_hash"),
            "expected_network": expect_network,
            "expected_network_matched": network_match,
            "live_publication_status": live_status,
        },
        "dashboard": {
            "headline": dashboard_payload.get("headline"),
            "status": dashboard_payload.get("status"),
            "surface_count": len(dashboard_payload.get("surfaces", [])),
            "verifier_cli": dashboard_payload.get("distribution", {}).get("verifier_cli"),
            "partner_session_cli": dashboard_payload.get("distribution", {}).get("partner_session_cli"),
        },
        "demo": {
            "readiness": demo_payload.get("demo_readiness"),
            "walkthrough_steps": len(demo_payload.get("walkthrough", [])),
        },
        "next_step": (
            "promote_to_mainnet"
            if expect_network == "sepolia" and outcome == "PASSED"
            else "mainnet_verification_live"
            if expect_network == "mainnet" and outcome == "PASSED"
            else "review_before_promotion"
        ),
        "notes": notes,
        "authority_boundary": proof_result["authority_boundary"],
    }


def run(argv: list[str] | None = None) -> int:
    return main(argv)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_partner_session_report(
        base_url=args.base_url,
        partner=args.partner,
        expect_network=args.expect_network,
        notes=args.notes,
    )

    if args.report_out:
        Path(args.report_out).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        lines = [
            f"AfriTech Partner Verification Session: {report['outcome']}",
            f"partner: {report['partner']}",
            f"session_id: {report['session_id']}",
            f"anchor_id: {report['verification']['anchor_id']}",
            f"verification_status: {report['verification']['verification_status']}",
            f"chain_network: {report['chain']['network']}",
            f"expected_network_matched: {report['chain']['expected_network_matched']}",
            f"dashboard_status: {report['dashboard']['status']}",
            f"demo_readiness: {report['demo']['readiness']}",
            f"next_step: {report['next_step']}",
        ]
        if args.report_out:
            lines.append(f"report_written: {args.report_out}")
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
