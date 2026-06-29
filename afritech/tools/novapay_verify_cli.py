"""Verify a NovaPay audit package from disk."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from afritech.core_platform.novapay_external_verifier import verify_audit_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novapay-verify",
        description="Verify a NovaPay audit_package.json without NovaPay runtime state.",
    )
    parser.add_argument("audit_package", help="Path to a NovaPay audit_package.json file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--write-report", help="Optional path to write the verification report JSON")
    return parser


def run(argv: list[str] | None = None) -> int:
    return main(argv)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    package = _load_json(Path(args.audit_package))
    result = verify_audit_package(package)
    if args.write_report:
        Path(args.write_report).write_text(
            json.dumps(result, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "PASS" if result["valid"] else "FAIL"
        print(f"NovaPay audit package verification: {status}")
        print(f"root_hash: {result['root_hash']}")
        print(f"protocol_valid: {result['protocol_valid']}")
        print(f"signature_valid: {result['signature_valid']}")
        print(f"ledger_hash_valid: {result['ledger_hash_valid']}")
        print(f"snapshot_root_valid: {result['snapshot_root_valid']}")
        print(f"snapshot_ledger_valid: {result['snapshot_ledger_valid']}")
        print(f"event_chain_valid: {result['event_chain_valid']}")
        if args.write_report:
            print(f"report_written: {args.write_report}")
    return 0 if result["valid"] else 1


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("audit package must decode to a JSON object")
    return payload


if __name__ == "__main__":
    sys.exit(main())
