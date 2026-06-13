"""Third-party verifier for AfriPay evidence artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from afritech.afripay.public_validation import validate_public_proof_file
from afritech.afripay.audit_sandbox import verify_independent_audit_sandbox


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, help="Path to recursive_proof_bundle.json or a directory containing it")
    parser.add_argument("--public-key", help="Path to a PEM-encoded public key used to verify the signature")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--write-report", help="Write the verification report to JSON")
    parser.add_argument("--sandbox", action="store_true", help="Also verify the sibling PDF in the independent audit sandbox")
    return parser


def run(argv: list[str] | None = None) -> int:
    return main(argv)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    public_key_pem = None
    if args.public_key:
        public_key_pem = Path(args.public_key).read_text(encoding="utf-8")

    if args.sandbox:
        report = verify_independent_audit_sandbox(args.artifact, public_key_pem=public_key_pem)
        payload = report.canonical_dict()
    else:
        report = validate_public_proof_file(args.artifact, public_key_pem=public_key_pem)
        payload = report.canonical_dict()

    if args.write_report:
        Path(args.write_report).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        lines = [
            f"AfriPay Third-Party Verifier: {'VERIFIED' if payload['verified'] else 'REJECTED'}",
            f"artifact_hash: {payload.get('artifact_hash', payload.get('proof_report', {}).get('artifact_hash'))}",
            f"bundle_hash: {payload.get('bundle_hash', payload.get('proof_report', {}).get('bundle_hash'))}",
        ]
        if args.sandbox:
            lines.append(f"pdf_verified: {payload['pdf_verified']}")
        if args.write_report:
            lines.append(f"report_written: {args.write_report}")
        print("\n".join(lines))

    return 0 if payload.get("verified", False) else 1


if __name__ == "__main__":
    sys.exit(main())
