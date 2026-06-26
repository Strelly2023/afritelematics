"""CLI for verifying NovaTrust proof receipts."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any

from afritech.core_platform.mobile_verifier import verify_scanned_receipt
from afritech.core_platform.qr_proof import build_qr_artifact
from afritech.core_platform.smart_contract_verification import build_onchain_verification_bundle
from afritech.core_platform.proof_receipts import verify_proof_receipt


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("receipt_json_must_be_object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser("novatrust-proof-receipt")
    parser.add_argument("receipt", nargs="?", help="Path to a proof receipt JSON file")
    parser.add_argument(
        "--group-public-key",
        action="append",
        default=[],
        help="Hex-encoded BLS group public key; may be supplied multiple times",
    )
    parser.add_argument("--qr", action="store_true", help="Emit a QR payload artifact")
    parser.add_argument("--qr-output", help="Write QR PNG bytes to this path")
    parser.add_argument("--qr-data", help="Verify a scanned QR payload string")
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="Verify a scanned QR payload using the mobile trust flow",
    )
    parser.add_argument(
        "--onchain",
        action="store_true",
        help="Emit the on-chain verification commitment bundle",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    if args.qr_data:
        result = verify_scanned_receipt(args.qr_data)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True, default=str))
        else:
            status = "VALID" if result.get("status") is True else "INVALID"
            print(f"{status}: {result.get('reason', 'unknown')}")
        return 0 if result.get("status") is True else 2

    if not args.receipt:
        raise SystemExit("receipt path or --qr-data is required")

    receipt = _load_json(Path(args.receipt))
    group_public_keys = [
        bytes.fromhex(public_key)
        for public_key in args.group_public_key
        if public_key.strip()
    ]

    if args.qr or args.qr_output:
        artifact = build_qr_artifact(receipt)
        if args.qr_output:
            Path(args.qr_output).write_bytes(base64.b64decode(artifact["qr_png"]))
        if args.json:
            print(json.dumps(artifact, indent=2, sort_keys=True, default=str))
        else:
            print(artifact["qr_payload"])
        return 0

    if args.mobile:
        artifact = build_qr_artifact(receipt)
        result = verify_scanned_receipt(artifact["qr_payload"])
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True, default=str))
        else:
            status = "VALID" if result.get("status") is True else "INVALID"
            print(f"{status}: {result.get('reason', 'unknown')}")
        return 0 if result.get("status") is True else 2

    if args.onchain:
        bundle = build_onchain_verification_bundle(receipt)
        if args.json:
            print(json.dumps(bundle, indent=2, sort_keys=True, default=str))
        else:
            print(bundle["bundle_hash"])
        return 0

    result = verify_proof_receipt(receipt, group_public_keys=group_public_keys or None)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        status = "VALID" if result.get("valid") is True else "INVALID"
        reason = result.get("reason", "unknown")
        print(f"{status}: {reason}")
    return 0 if result.get("valid") is True else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
