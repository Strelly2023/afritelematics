"""CLI for verifying AfriTech public architecture proof surfaces."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib import request

from afritech.sdk.external_verifier import ExternalVerifierClient


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _load_json(source: str) -> dict[str, Any]:
    if source.startswith(("http://", "https://")):
        with request.urlopen(source, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    else:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("source must decode to a JSON object")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof", help="Path or URL to /public/architecture/proof payload")
    parser.add_argument("--chain", help="Optional path or URL to /public/architecture/chain/{anchor_id} payload")
    parser.add_argument("--demo", help="Optional path or URL to /public/demo/system-integrity payload")
    parser.add_argument("--base-url", help="Base URL that exposes the public trust endpoints")
    parser.add_argument("--trust-dashboard", help="Optional path or URL to /public/trust/dashboard payload")
    parser.add_argument("--expect-network", help="Optional expected network for the chain receipt")
    parser.add_argument("--write-report", help="Write the verification result to a JSON report file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def run(argv: list[str] | None = None) -> int:
    return main(argv)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.proof and not args.base_url:
        raise SystemExit("either --proof or --base-url is required")

    client = ExternalVerifierClient()

    proof_source = args.proof
    chain_source = args.chain
    demo_source = args.demo
    dashboard_source = args.trust_dashboard

    if args.base_url:
        base_url = _normalize_base_url(args.base_url)
        proof_source = proof_source or f"{base_url}/public/architecture/proof"
        dashboard_source = dashboard_source or f"{base_url}/public/trust/dashboard"
        demo_source = demo_source or f"{base_url}/public/demo/system-integrity"

    assert proof_source is not None
    proof_payload = client.decode_architecture_proof_response(_load_json(proof_source))
    proof_result = client.verify_architecture_proof_locally(proof_payload)
    anchor_id = str(proof_result["anchor_id"])

    if chain_source is None and args.base_url:
        base_url = _normalize_base_url(args.base_url)
        chain_source = f"{base_url}/public/architecture/chain/{anchor_id}"

    chain_payload = None
    if chain_source:
        chain_payload = client.decode_public_chain_receipt(_load_json(chain_source))

    demo_payload = None
    if demo_source:
        demo_payload = client.decode_partner_demo_narrative(_load_json(demo_source))

    dashboard_payload = None
    if dashboard_source:
        dashboard_payload = client.decode_public_trust_dashboard(_load_json(dashboard_source))

    network_match = None
    if args.expect_network and chain_payload is not None:
        network_match = chain_payload["chain_receipt"].get("network") == args.expect_network

    result = {
        "proof": proof_result,
        "chain": None if chain_payload is None else chain_payload["chain_receipt"],
        "demo_ready": None if demo_payload is None else demo_payload.get("demo_readiness"),
        "dashboard": (
            None
            if dashboard_payload is None
            else {
                "headline": dashboard_payload.get("headline"),
                "status": dashboard_payload.get("status"),
                "surface_count": len(dashboard_payload.get("surfaces", [])),
                "live_publication_status": (
                    dashboard_payload.get("chain", {})
                    .get("live_publication", {})
                    .get("status")
                ),
            }
        ),
        "expected_network": args.expect_network,
        "expected_network_matched": network_match,
    }

    if args.write_report:
        Path(args.write_report).write_text(
            json.dumps(result, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        lines = [
            f"AfriTech External Verifier: {proof_result['verification_status']}",
            f"proof_id: {proof_result['proof_id']}",
            f"anchor_id: {proof_result['anchor_id']}",
            f"chain_receipt_matches: {proof_result['chain_receipt_matches']}",
        ]
        if chain_payload is not None:
            lines.append(f"public_chain_status: {chain_payload['status']}")
            lines.append(f"public_chain_network: {chain_payload['chain_receipt'].get('network')}")
        if network_match is not None:
            lines.append(f"expected_network_matched: {network_match}")
        if demo_payload is not None:
            lines.append(f"demo_readiness: {demo_payload['demo_readiness']}")
        if dashboard_payload is not None:
            lines.append(f"dashboard_status: {dashboard_payload['status']}")
            lines.append(f"dashboard_headline: {dashboard_payload['headline']}")
        if args.write_report:
            lines.append(f"report_written: {args.write_report}")
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
