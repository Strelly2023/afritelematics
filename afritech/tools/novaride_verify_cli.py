"""Verify a NovaRide architecture contract or publication artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

from afritech.architecture.novaride_architecture import (
    novaride_architecture_schema_hash,
    novaride_architecture_signed_publication,
    verify_novaride_architecture_contract,
)
from afritech.security.architecture_signing import verify_architecture_signature


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novaride-verify",
        description="Verify a NovaRide architecture contract or publication artifact.",
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="Optional path or URL to a NovaRide architecture JSON artifact",
    )
    parser.add_argument(
        "--version",
        help="Optional architecture version to verify when no source is supplied",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for the verification result",
    )
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Optional capability to require when verifying a raw architecture contract",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    return main(argv)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.source is None:
        artifact = novaride_architecture_signed_publication(args.version)
    else:
        artifact = _load_artifact(args.source)
    result = _verify_artifact(artifact, list(args.capability))
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        status = "PASS" if result["valid"] else "FAIL"
        print(f"NovaRide architecture verification: {status}")
        print(f"schema_hash_valid: {result.get('schema_hash_valid', False)}")
        print(f"signature_valid: {result.get('signature_valid', False)}")
        print(f"capabilities_valid: {result.get('capabilities_valid', False)}")
        print(f"supported: {result.get('supported', False)}")
        print(f"version: {result.get('resolved_version') or result.get('version')}")
        if "publication_valid" in result:
            print(f"publication_valid: {result['publication_valid']}")
    return 0 if result["valid"] else 1


def _load_artifact(source: str) -> dict[str, Any]:
    if source.startswith(("http://", "https://")):
        response = httpx.get(source, timeout=30.0)
        response.raise_for_status()
        payload = response.json()
    else:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("architecture artifact must decode to a JSON object")
    return payload


def _verify_artifact(artifact: dict[str, Any], required_capabilities: list[str]) -> dict[str, Any]:
    if "contract" in artifact and "schema_hash" in artifact["contract"]:
        publication = artifact
        publication_valid = _verify_publication(publication)
        contract = publication["contract"]
        contract_result = verify_novaride_architecture_contract(
            contract.get("requested_version"),
            contract.get("schema_hash"),
            required_capabilities,
        )
        return {
            **contract_result,
            "publication_valid": publication_valid,
            "signature_valid": publication_valid,
            "valid": bool(publication_valid and contract_result["valid"]),
        }
    if "version" in artifact and "layers" in artifact:
        return verify_novaride_architecture_contract(
            artifact.get("version"),
            novaride_architecture_schema_hash(),
            required_capabilities,
        )
    raise ValueError("unsupported architecture artifact")


def _verify_publication(publication: dict[str, Any]) -> bool:
    signature = publication.get("signature")
    contract = publication.get("contract")
    if not isinstance(signature, dict) or not isinstance(contract, dict):
        return False
    if publication.get("signature_status") != "signed":
        return False
    return verify_architecture_signature(contract, signature)


if __name__ == "__main__":
    sys.exit(main())
