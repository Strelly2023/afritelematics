"""Download and verify NovaTrust public packets locally."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib import request

from afritech.core_platform.signing import verify_packet_signature


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Base URL exposing /trust/explorer/{id}")
    parser.add_argument("--trust-id", required=True, help="Trust or receipt identifier")
    parser.add_argument("--write-dir", help="Directory to write downloaded artifacts")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def run(argv: list[str] | None = None) -> int:
    return main(argv)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    base = args.base_url.rstrip("/")
    trust_id = args.trust_id
    packet = _get_json(f"{base}/trust/explorer/{trust_id}")
    signature = _get_json(f"{base}/trust/explorer/{trust_id}/signature")
    report = _get_json(f"{base}/trust/explorer/{trust_id}/compliance-report")
    packet_body = packet["packet"]
    signature_body = signature["signature"]
    verified = verify_packet_signature(packet_body, signature_body)
    result = {
        "trust_id": trust_id,
        "verified": verified,
        "explorer": f"{base}/trust/explorer/{trust_id}",
        "pdf": f"{base}/trust/explorer/{trust_id}/audit.pdf",
        "signature": signature_body,
        "control_count": len(report.get("controls", [])),
    }
    if args.write_dir:
        target = Path(args.write_dir)
        target.mkdir(parents=True, exist_ok=True)
        (target / "packet.json").write_text(json.dumps(packet, indent=2, sort_keys=True), encoding="utf-8")
        (target / "signature.json").write_text(json.dumps(signature, indent=2, sort_keys=True), encoding="utf-8")
        (target / "compliance-report.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        (target / "verification-result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"NovaTrust verification: {'PASS' if verified else 'FAIL'}")
        print(f"trust_id: {trust_id}")
        print(f"explorer: {result['explorer']}")
        print(f"pdf: {result['pdf']}")
        print(f"controls: {result['control_count']}")
    return 0 if verified else 1


def _get_json(url: str) -> dict[str, object]:
    req = request.Request(url, headers={"Accept": "application/json"})
    with request.urlopen(req, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{url} did not return a JSON object")
    return payload


if __name__ == "__main__":
    sys.exit(main())
